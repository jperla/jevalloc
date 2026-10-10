#include "jevalloc.h"
#include <new>
extern "C" void* jev_new_aligned(size_t n,size_t a) {
  for (;;) { if(void* p=jev_malloc_aligned(n,a)) return p;
    auto h=std::get_new_handler(); if(!h) throw std::bad_alloc(); h(); }
}
extern "C" void* jev_new(size_t n) { return jev_new_aligned(n,0); }
extern "C" void* jev_new_aligned_nothrow(size_t n,size_t a) { try {return jev_new_aligned(n,a);} catch(...) {return nullptr;} }
extern "C" void* jev_new_nothrow(size_t n) { return jev_new_aligned_nothrow(n,0); }
