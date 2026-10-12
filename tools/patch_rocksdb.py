"""Add only measurement/settle phase markers to the source-built db_bench."""
from pathlib import Path
root=Path(__file__).resolve().parents[1]
p=root/'build/real/rocksdb-10.10.1/tools/db_bench_tool.cc'
s=p.read_text()
if 'name == "fragidle"' not in s:
 s='#include "'+str(root/'fragbench/phase.h')+'"\n'+s
 needle='      } else if (name == "compact") {'
 assert s.count(needle)==1
 s=s.replace(needle,'''      } else if (name == "fragpeak" || name == "fragidle") {
        if (name == "fragidle") {
          FlushOptions flush; flush.wait = true;
          auto status = db_.db->Flush(flush);
          if (!status.ok()) { fprintf(stderr, "%s\\n", status.ToString().c_str()); ErrorExit(); }
          WaitForCompactOptions wait;
          status = db_.db->WaitForCompact(wait);
          if (!status.ok()) { fprintf(stderr, "%s\\n", status.ToString().c_str()); ErrorExit(); }
          usleep(500000);
        }
        uint64_t live = 0, part = 0;
        for (const char* property : {"rocksdb.cur-size-all-mem-tables", "rocksdb.estimate-table-readers-mem", "rocksdb.block-cache-usage"}) {
          if (!db_.db->GetIntProperty(property, &part)) { fprintf(stderr, "Missing memory property %s\\n", property); ErrorExit(); }
          live += part;
        }
        frag_phase(name == "fragidle" ? "idle" : "peak", live, "RocksDB memtable + table-reader + block-cache estimates (partial)");
        if (name == "fragidle") puts("fragbench OK");
''' +needle)
 p.write_text(s)
