#include <cstdlib>
#include <cstring>
#include <cassert>
#include <cstdio>
#include <cstdint>
#include <new>
#include <thread>
#include <vector>
#include <dlfcn.h>
#ifdef __APPLE__
#include <malloc/malloc.h>
#endif
static void* slots[8][2000];
int main(){
 assert(dlsym(RTLD_DEFAULT,"jev_site_key"));
 std::vector<std::thread> ts;
 for(int t=0;t<8;t++)ts.emplace_back([t]{for(int i=0;i<2000;i++){size_t n=1+(i*97)%4096;void* p=malloc(n);assert(p);memset(p,t,n);p=realloc(p,n+37);assert(p);for(size_t j=0;j<n;j++)assert(((unsigned char*)p)[j]==t);slots[t][i]=p;}});
 for(auto& t:ts)t.join();ts.clear();
 for(int t=0;t<8;t++)ts.emplace_back([t]{for(int i=0;i<2000;i++)free(slots[(t+1)%8][i]);});for(auto& t:ts)t.join();
 for(size_t a=8;a<=65536;a*=2){void* p=nullptr;assert(posix_memalign(&p,a,a+3)==0);assert((uintptr_t)p%a==0);free(p);p=aligned_alloc(a,a*2);assert(p&&(uintptr_t)p%a==0);free(p);}
 void* untouched=(void*)123;assert(posix_memalign(&untouched,3,20)!=0&&untouched==(void*)123);
 auto p=new int(42);assert(*p==42);delete p;auto ar=new int[100];ar[3]=4;assert(ar[3]==4);delete[] ar;
 auto q=new(std::nothrow) int(3);assert(q);delete q;
 struct alignas(256) A {char x[256];};auto ap=new A;assert((uintptr_t)ap%256==0);delete ap;
 void* z=malloc(0);free(z);z=calloc(0,4);free(z);z=malloc(10);z=realloc(z,0);free(z);free(nullptr);
 volatile size_t huge=SIZE_MAX;assert(!malloc(huge));assert(!calloc(huge,2));z=malloc(16);assert(!realloc(z,huge));free(z);
 char* s=strdup("hello");assert(!strcmp(s,"hello"));
#ifdef __APPLE__
 assert(malloc_size(s)>=6);
#endif
 free(s);
 void* vp=valloc(100);assert(vp&&(uintptr_t)vp%4096==0);free(vp);
 void* cp=calloc(31,7);assert(cp);for(int i=0;i<217;i++)assert(((char*)cp)[i]==0);free(cp);
 assert(!aligned_alloc(3,30));
 void* np=::operator new(135791);::operator delete(np);
 np=::operator new[](135792);::operator delete[](np);
 np=::operator new(135793,std::nothrow);assert(np);::operator delete(np,std::nothrow);
 np=::operator new[](135794,std::nothrow);assert(np);::operator delete[](np,std::nothrow);
 np=::operator new(135795,std::align_val_t(256));assert((uintptr_t)np%256==0);::operator delete(np,std::align_val_t(256));
 np=::operator new[](135796,std::align_val_t(256));::operator delete[](np,std::align_val_t(256));
 np=::operator new(135797,std::align_val_t(256),std::nothrow);assert(np);::operator delete(np,std::align_val_t(256),std::nothrow);
 np=::operator new[](135798,std::align_val_t(256),std::nothrow);assert(np);::operator delete[](np,std::align_val_t(256),std::nothrow);
 np=::operator new(135799);::operator delete(np,size_t(135799));
 np=::operator new[](135800);::operator delete[](np,size_t(135800));
 np=::operator new(135801,std::align_val_t(256));::operator delete(np,size_t(135801),std::align_val_t(256));
 np=::operator new[](135802,std::align_val_t(256));::operator delete[](np,size_t(135802),std::align_val_t(256));
 assert(!::operator new(huge,std::nothrow));
 bool threw=false;try{np=::operator new(huge);::operator delete(np);}catch(const std::bad_alloc&){threw=true;}assert(threw);
 puts("stress OK");
}
