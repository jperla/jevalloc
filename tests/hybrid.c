#include <assert.h>
#include "../src/hybrid.h"
int main(void){
 const uint64_t m=64*1024*1024;
 assert(hybrid_class(0,.7,100,10000,0,0,m,m)==0);
 assert(hybrid_class(0,.9,100,10000,0,0,100*m,100*m)==0);
 assert(hybrid_class(0,.699,100,10000,0,0,m/2+1,m)==1);
 assert(hybrid_class(0,.6,100,10000,0,0,m/2,m)==0);
 assert(hybrid_class(0,.6,100,10000,0,0,m,m-1)==0);
 assert(hybrid_class(0,.6,100,10000,1,1,m,m)==0);
 assert(hybrid_class(1,.1,16,10000,500,1,m,m)==0);
 assert(hybrid_class(1,.1,15,10000,500,1,m,m)==1);
 assert(hybrid_class(1,.1,16,10000,499,1,m,m)==1);
 assert(hybrid_class(0,.1,10000,1000000,500,1,m,m)==0);
 assert(hybrid_class(1,.1,16,0,0,0,0,0)==1);
 for(unsigned i=0;i<3;i++) {
  hybrid_promotion_gate=.6+.1*i;
  assert(hybrid_class(0,hybrid_promotion_gate,100,10000,0,0,m,m)==0);
  assert(hybrid_class(0,hybrid_promotion_gate-.001,100,10000,0,0,m,m)==1);
 }
}
