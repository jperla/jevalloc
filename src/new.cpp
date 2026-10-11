// C programs must not acquire a libstdc++ dependency just by preloading malloc.
// C++ programs already supply these ABI symbols. Keep their exception semantics.
#ifndef __APPLE__
asm(".weak __cxa_allocate_exception");
asm(".weak __cxa_throw");
asm(".weak __cxa_begin_catch");
asm(".weak __cxa_end_catch");
asm(".weak __gxx_personality_v0");
asm(".weak _ZSt15get_new_handlerv");
asm(".weak _ZNSt9bad_allocD1Ev");
asm(".weak _ZTVSt9bad_alloc");
asm(".weak _ZTISt9bad_alloc");
#endif
#include "jevalloc.h"
#include <new>
#include <dlfcn.h>
// Keep handler discovery and exception machinery off the successful allocation path.
static __attribute__((noinline,cold)) void* retry_new(size_t n,size_t a) {
  for (;;) {
#ifdef __APPLE__
    auto h=std::get_new_handler();
#else
    // mimalloc supplies a weak C fallback with this name. Skip that definition.
    auto get=reinterpret_cast<std::new_handler(*)()>(dlsym(RTLD_NEXT,"_ZSt15get_new_handlerv"));
    auto h=get?get():nullptr;
#endif
    if(!h) throw std::bad_alloc(); h();
    if(void* p=jev_malloc_aligned(n,a))return p;
  }
}
extern "C" void* jev_new_aligned(size_t n,size_t a) {
  if(void* p=jev_malloc_aligned(n,a))return p;return retry_new(n,a);
}
extern "C" void* jev_new(size_t n) {
  if(void* p=jev_malloc(n))return p;return retry_new(n,0);
}
extern "C" void* jev_new_aligned_nothrow(size_t n,size_t a) { try {return jev_new_aligned(n,a);} catch(...) {return nullptr;} }
extern "C" void* jev_new_nothrow(size_t n) { return jev_new_aligned_nothrow(n,0); }
#ifndef __APPLE__
// The 64-bit Itanium ABI uses the same signature as jev_new. Avoid a forwarding
// jump in C++ programs, matching the baseline allocator's direct aliases.
extern "C" void* _Znwm(size_t n) __attribute__((alias("jev_new"),used,visibility("default")));
extern "C" void* _Znam(size_t n) __attribute__((alias("jev_new"),used,visibility("default")));
#endif
