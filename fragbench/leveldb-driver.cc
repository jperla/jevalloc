#include "leveldb/db.h"
#include "leveldb/cache.h"
#include "leveldb/write_batch.h"
#include "phase.h"
#include <memory>
#include <vector>
#include <thread>
#include <string>
#include <cstdlib>
static void check(leveldb::Status s){if(!s.ok()){fprintf(stderr,"%s\n",s.ToString().c_str());exit(1);}}
static std::string key(int i){char b[32];snprintf(b,sizeof(b),"key%09d",i);return b;}
static uint64_t live(leveldb::DB* db){std::string value;if(!db->GetProperty("leveldb.approximate-memory-usage",&value))exit(2);return strtoull(value.c_str(),nullptr,10);}
int main(int argc,char** argv){
 if(argc!=2)return 2;
 leveldb::Options options;options.create_if_missing=true;options.compression=leveldb::kNoCompression;options.write_buffer_size=4<<20;options.max_open_files=256;
 std::unique_ptr<leveldb::Cache> cache(leveldb::NewLRUCache(32<<20));options.block_cache=cache.get();check(leveldb::DestroyDB(argv[1],options));
 leveldb::DB* raw;check(leveldb::DB::Open(options,argv[1],&raw));std::unique_ptr<leveldb::DB> db(raw);std::string value(1024,'v');
 for(int b=0;b<120000;b+=500){leveldb::WriteBatch batch;for(int i=b;i<b+500;i++)batch.Put(key(i),value);check(db->Write(leveldb::WriteOptions(),&batch));}
 db->CompactRange(nullptr,nullptr);
 std::vector<std::thread> readers;for(int t=0;t<8;t++)readers.emplace_back([&,t]{std::string out;for(int i=0;i<20000;i++)check(db->Get(leveldb::ReadOptions(),key((i*7919+t*31)%120000),&out));});for(auto& t:readers)t.join();
 std::vector<std::unique_ptr<leveldb::Iterator>> iterators;
 for(int round=0;round<12;round++){
  for(int j=0;j<16;j++){iterators.emplace_back(db->NewIterator(leveldb::ReadOptions()));iterators.back()->Seek(key((round*1000+j*317)%120000));}
  leveldb::WriteBatch batch;for(int i=0;i<4096;i++)batch.Put(key((round*4096+i)%120000),value);check(db->Write(leveldb::WriteOptions(),&batch));
 }
 frag_phase("peak",live(db.get()),"LevelDB approximate-memory-usage (partial estimate)");iterators.clear();db->CompactRange(nullptr,nullptr);
 frag_phase("drop",live(db.get()),"LevelDB approximate-memory-usage (partial estimate)");usleep(500000);frag_phase("idle",live(db.get()),"LevelDB approximate-memory-usage (partial estimate)");puts("fragbench OK");
}
