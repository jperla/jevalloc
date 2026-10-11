/* One allocation PC changes from retained objects to eventually freed objects. */
#include <stdlib.h>
#include <stdio.h>
static void* held[1200];
__attribute__((noinline)) static void allocations(void) {
 for(int phase=0;phase<2;phase++) {
  int count=phase?12000:1200;
  for(int i=0;i<count;i++) {
   void* p=malloc(32);if(!p)abort();
   if(phase)free(p);else held[i]=p;
  }
  if(!phase)for(int i=0;i<1200;i++)free(held[i]);
 }
}
int main(void){allocations();puts("permanent heuristic OK");return 0;}
