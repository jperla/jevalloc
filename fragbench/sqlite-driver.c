#include "sqlite3.h"
#include "phase.h"
#include <stdlib.h>
#include <string.h>
#define NCONN 48
#define NSTMT 16
static void check(int code){if(code!=SQLITE_OK && code!=SQLITE_DONE && code!=SQLITE_ROW){fprintf(stderr,"SQLite error %d\n",code);exit(1);}}
static sqlite3* connect_db(void){sqlite3* db;check(sqlite3_open_v2("file:fragbench?mode=memory&cache=shared",&db,SQLITE_OPEN_READWRITE|SQLITE_OPEN_CREATE|SQLITE_OPEN_URI,NULL));return db;}
static void sql(sqlite3* db,const char* text){char* error=0;int rc=sqlite3_exec(db,text,0,0,&error);if(rc){fprintf(stderr,"%s\n",error);exit(1);}}
int main(void){
 sqlite3* db=connect_db();sql(db,"PRAGMA temp_store=MEMORY; CREATE TABLE items(id INTEGER PRIMARY KEY,value BLOB); BEGIN");
 sqlite3_stmt* insert;check(sqlite3_prepare_v2(db,"INSERT INTO items VALUES(?,?)",-1,&insert,0));
 char value[512];memset(value,'x',sizeof(value));
 for(int i=0;i<100000;i++){check(sqlite3_bind_int(insert,1,i));check(sqlite3_bind_blob(insert,2,value,sizeof(value),SQLITE_STATIC));check(sqlite3_step(insert));check(sqlite3_reset(insert));}
 check(sqlite3_finalize(insert));sql(db,"COMMIT");
 sqlite3* connections[NCONN];sqlite3_stmt* statements[NCONN][NSTMT];
 for(int c=0;c<NCONN;c++){
  connections[c]=connect_db();sql(connections[c],"PRAGMA temp_store=MEMORY");
  for(int j=0;j<NSTMT;j++){
   check(sqlite3_prepare_v2(connections[c],"SELECT id,value FROM items WHERE id>=? AND id<? ORDER BY substr(value,1,64)||id DESC",-1,&statements[c][j],0));
   int start=(c*NSTMT+j)*97%99000;check(sqlite3_bind_int(statements[c][j],1,start));check(sqlite3_bind_int(statements[c][j],2,start+256));check(sqlite3_step(statements[c][j]));
  }
 }
 frag_phase("peak",sqlite3_memory_used(),"sqlite3_memory_used");
 for(int c=0;c<NCONN;c++){for(int j=0;j<NSTMT;j++)check(sqlite3_finalize(statements[c][j]));check(sqlite3_close(connections[c]));}
 frag_phase("drop",sqlite3_memory_used(),"sqlite3_memory_used");usleep(500000);
 frag_phase("idle",sqlite3_memory_used(),"sqlite3_memory_used");
 check(sqlite3_close(db));puts("fragbench OK");return 0;
}
