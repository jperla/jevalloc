#ifndef JEVALLOC_HYBRID_H
#define JEVALLOC_HYBRID_H
#include <stdint.h>
/* Retain the current class unless direct evidence permits a transition. */
static inline unsigned hybrid_class(unsigned current,double transient,uint64_t samples,
 uint64_t bytes,uint64_t freed_bytes,uint64_t frees,uint64_t oldest,uint64_t clock) {
 if(samples>=16 && bytes && (long double)freed_bytes*20>=bytes)return 0;
 if(!frees && transient<0.7 && clock>=UINT64_C(64)*1024*1024 && oldest>clock/2)return 1;
 return current;
}
#endif
