"""Supply Mesh's pinned CMake dependencies using archives, with no git writes."""
import difflib,hashlib,json,re
from pathlib import Path
from fetch_mesh import ROOT,fetch,records
base=ROOT/'results/pass9/builds';source=ROOT/'build/mesh-source/CMakeLists.txt'
original=source.read_text();updated=original
if 'GIT_REPOSITORY' not in original:
 assert (base/'mesh-archive-dependencies.patch').exists()
 for item in json.loads((base/'mesh-dependencies.json').read_text()):
  assert hashlib.sha256((ROOT/item['archive']).read_bytes()).hexdigest()==item['sha256']
  assert (ROOT/item['directory']).is_dir()
 assert '../mesh-deps/googletest' in original and '../mesh-deps/heap_layers' in original
 print('Using recorded archive dependencies and build adaptation')
 raise SystemExit(0)
for name,repository,revision in re.findall(r'ExternalProject_Add\((\w+)\s+GIT_REPOSITORY\s+https://github.com/(\S+?)\.git\s+GIT_TAG\s+(\w+)',original):
 fetch(repository,revision,ROOT/'build/mesh-deps'/name)
 updated=re.sub(r'(ExternalProject_Add\('+name+r'\s+)GIT_REPOSITORY[^\n]+\n\s+GIT_TAG[^\n]+',r'\1DOWNLOAD_COMMAND ""\n        UPDATE_COMMAND ""',updated)
 updated=updated.replace('"${CMAKE_CURRENT_BINARY_DIR}/'+name+'-src"','"${CMAKE_SOURCE_DIR}/../mesh-deps/'+name+'"')
 if name=='googletest':updated=updated.replace('ExternalProject_Add(googletest','ExternalProject_Add(googletest\n        CMAKE_ARGS -DCMAKE_POLICY_VERSION_MINIMUM=3.5')
assert len(records)>=2,'Expected pinned googletest and Heap-Layers dependencies'
# The src subdirectory also refers directly to the original dependency paths.
sub=source.parent/'src/CMakeLists.txt';sub_original=sub.read_text();sub_updated=sub_original
for name in ('googletest','heap_layers'):
 sub_updated=sub_updated.replace('${CMAKE_CURRENT_BINARY_DIR}/../'+name+'-src','${CMAKE_SOURCE_DIR}/../mesh-deps/'+name)
patch=''.join(difflib.unified_diff(original.splitlines(True),updated.splitlines(True),fromfile='a/CMakeLists.txt',tofile='b/CMakeLists.txt'))
patch+=''.join(difflib.unified_diff(sub_original.splitlines(True),sub_updated.splitlines(True),fromfile='a/src/CMakeLists.txt',tofile='b/src/CMakeLists.txt'))
(base/'mesh-archive-dependencies.patch').write_text(patch)
(base/'mesh-dependencies.json').write_text(json.dumps(records,indent=2))
source.write_text(updated);sub.write_text(sub_updated)
