"""Compile and exercise the numeric-family loop from the actual Redis patch."""
import subprocess,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
patch='\n'.join(line[1:] for line in (ROOT/'patches/redis-request-context.patch').read_text().splitlines() if line.startswith('+') and not line.startswith('+++'))
a=patch.index('        size_t n = sdslen(value), i;');b=patch.index('        prefix[i] = 0;',a)+len('        prefix[i] = 0;')
loop=patch[a:b].replace('sdslen(value)','strlen(value)')
source='''#include <string.h>
#include <assert.h>
static void family(const char* value,char prefix[17]) {
'''+loop+'''
}
int main(void) {
 char out[17];
 family("k123456",out);assert(!strcmp(out,"k#"));
 family("k0",out);assert(!strcmp(out,"k#"));
 family("k99999999999999999999999",out);assert(!strcmp(out,"k#"));
 family("session:123",out);assert(!strcmp(out,"session"));
 family("session17:123",out);assert(!strcmp(out,"session#"));
 family("a12b",out);assert(!strcmp(out,"a12b"));
 family("123",out);assert(!strcmp(out,"#"));
 family("",out);assert(!strcmp(out,""));
}
'''
with tempfile.TemporaryDirectory(dir=ROOT/'build',prefix='redis-context-') as d:
 p=Path(d);(p/'test.c').write_text(source)
 subprocess.run(['cc',str(p/'test.c'),'-o',str(p/'test')],check=True)
 subprocess.run([str(p/'test')],check=True)
print('REDIS NUMERIC KEY FAMILIES PASSED')
