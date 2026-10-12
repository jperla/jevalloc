#!/usr/bin/env python3
"""Fetch a pinned Mesh source snapshot and gitlink dependencies without git writes."""
import configparser,hashlib,json,subprocess,urllib.parse,urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
records=[]
def get_json(url):
 with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'jevalloc-source-build'}),timeout=90) as r:return json.load(r)
def fetch(repo,revision,destination):
 commit=get_json(f'https://api.github.com/repos/{repo}/commits/{revision}')
 sha=commit['sha'];tree_sha=commit['commit']['tree']['sha']
 archive=ROOT/'build'/('source-'+repo.replace('/','-')+'-'+sha+'.tar.gz')
 if not archive.exists():
  with urllib.request.urlopen(f'https://codeload.github.com/{repo}/tar.gz/{sha}',timeout=120) as r:archive.write_bytes(r.read())
 destination.mkdir(parents=True,exist_ok=True)
 subprocess.run(['tar','xzf',str(archive),'--strip-components=1','-C',str(destination)],check=True)
 records.append(dict(repository=repo,revision=sha,archive=str(archive.relative_to(ROOT)),sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),directory=str(destination.relative_to(ROOT))))
 modules=destination/'.gitmodules'
 if modules.exists():
  tree=get_json(f'https://api.github.com/repos/{repo}/git/trees/{tree_sha}?recursive=1')
  links={entry['path']:entry['sha'] for entry in tree['tree'] if entry['type']=='commit'}
  config=configparser.ConfigParser();config.read(modules)
  for section in config.sections():
   path=config[section]['path'];url=config[section]['url']
   if url.startswith('../'):url=urllib.parse.urljoin('https://github.com/'+repo+'/',url)
   url=url.replace('git@github.com:','https://github.com/').replace('git://github.com/','https://github.com/')
   if not url.startswith('https://github.com/'):raise RuntimeError('Unsupported submodule URL: '+url)
   child=url.removeprefix('https://github.com/').removesuffix('.git')
   fetch(child,links[path],destination/path)
def main():
 base=ROOT/'results/pass9'
 assert (base/'context.status').read_text().strip()=='0','Context measurements must finish first'
 provenance=base/'builds/mesh-sources.json';provenance.parent.mkdir(parents=True,exist_ok=True)
 if provenance.exists():
  old=json.loads(provenance.read_text())
  for r in old:
   archive=ROOT/r['archive']
   if archive.exists():assert hashlib.sha256(archive.read_bytes()).hexdigest()==r['sha256']
  if all((ROOT/r['archive']).exists() and (ROOT/r['directory']).is_dir() for r in old):
   print('Using recorded source snapshot');return
  root=old[0]
  fetch(root['repository'],root['revision'],ROOT/root['directory'])
  assert records==old,'Restored source archives differ from the recorded snapshot'
  print('Restored the recorded source snapshot');return
 fetch('plasma-umass/Mesh','master',ROOT/'build/mesh-source')
 provenance.write_text(json.dumps(records,indent=2))
 print(json.dumps(records,indent=2))
if __name__=='__main__':main()
