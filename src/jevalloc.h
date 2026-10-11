#pragma once
#include <stddef.h>
#include <stdint.h>
#ifdef __cplusplus
extern "C" {
#endif
void* jev_malloc(size_t);
void* jev_calloc(size_t,size_t);
void* jev_realloc(void*,size_t);
void jev_free(void*);
void jev_cfree(void*);
void* jev_malloc_aligned(size_t,size_t);
void* jev_aligned_alloc(size_t,size_t);
int jev_posix_memalign(void**,size_t,size_t);
void* jev_valloc(size_t);
void* jev_pvalloc(size_t);
void* jev_memalign(size_t,size_t);
void* jev_reallocf(void*,size_t);
void* jev_reallocarray(void*,size_t,size_t);
int jev_reallocarr(void*,size_t,size_t);
char* jev_strdup(const char*);
char* jev_strndup(const char*,size_t);
void jev_free_size(void*,size_t);
void jev_free_aligned(void*,size_t);
void jev_free_size_aligned(void*,size_t,size_t);
void* jev_new(size_t);
void* jev_new_nothrow(size_t);
void* jev_new_aligned(size_t,size_t);
void* jev_new_aligned_nothrow(size_t,size_t);
uint64_t jev_site_key(void);
char* jev_realpath(const char*,char*);
#define jev_malloc_good_size mi_malloc_good_size
#ifdef __cplusplus
}
#endif
