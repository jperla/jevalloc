"""Adapt upstream override sources in the build tree; vendor checkout stays pristine."""
import pathlib, re, sys
mi, out = map(pathlib.Path, sys.argv[1:])
names = 'realpath malloc calloc realloc free cfree strdup strndup posix_memalign reallocf valloc aligned_alloc malloc_aligned new new_nothrow new_aligned new_aligned_nothrow free_size free_aligned free_size_aligned reallocarray reallocarr pvalloc memalign'.split()
for source, target in [('src/alloc-override.c', 'override.c'), ('src/prim/osx/alloc-override-zone.c', 'zone.c')]:
    text = (mi/source).read_text()
    for n in sorted(names, key=len, reverse=True):
        text = re.sub(r'\bmi_' + n + r'\b', 'jev_' + n, text)
    # Token concatenation does not rescan mi_##fun into a replacement macro.
    text = text.replace('mi_##fun', 'jev_##fun') if target == 'override.c' else text
    text = text.replace('#if (defined(__GNUC__) || defined(__clang__)) && !defined(__APPLE__) && !MI_TRACK_ENABLED', '#if 0')
    if target == 'override.c':
        # ELF free is a direct alias in jevalloc.c, where its target is defined.
        text, count = re.subn(r'^([ \t]*mi_decl_export void\s+free\(void\* p\)\s+MI_FORWARD0\(jev_free, p\)[ \t]*)$', r'#ifdef __APPLE__\n\1\n#endif', text, flags=re.M)
        if count != 1:raise RuntimeError('upstream free override changed')
        for pattern in (r'^([ \t]*void _Zd[la]Pv\(void\* p\).*MI_FORWARD0\(jev_free,p\).*)$',
                        r'^([ \t]*void\* _Zn[wa]m\(size_t n\).*MI_FORWARD1\(jev_new,n\).*)$'):
            text, count = re.subn(pattern, r'#ifdef __APPLE__\n\1\n#endif', text, flags=re.M)
            if count != 2:raise RuntimeError('upstream C++ override changed')
    prefix = '#include <stdlib.h>\n#include <string.h>\n#include "mimalloc.h"\n#include "mimalloc/internal.h"\n#include "jevalloc.h"\n#define MI_IN_ALLOC_C 1\n#define MI_MALLOC_OVERRIDE 1\n#define MI_SHARED_LIB_EXPORT 1\n'
    if target == 'zone.c':
        text = '#ifdef __APPLE__\n' + text + '\n#endif\n'
    prefix += '#ifdef __APPLE__\n#define MI_OSX_ZONE 1\n#define MI_OSX_INTERPOSE 1\n#endif\n'
    (out/target).write_text(prefix + text)
