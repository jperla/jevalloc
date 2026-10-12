# Model answers by naming and context

Static first-sight answers under defaults. Probabilities are the recorded native model output; unasked sites remain in each block’s sites.json catalogue.

| Naming / workload | Key | Context | Stack | P(transient) | P(permanent) | Class | Oracle |
|---|---|---|---|---:|---:|---|---|
| named/site-pure-1 | b1f63e1f4cf87cbb | empty | xmalloc → parse_request_buffer → server_worker → start_thread → clone3 | 0.718216 | 0.281784 | transient | transient |
| named/site-pure-1 | d530a5059e084b88 | empty | xmalloc → assemble_response_buffer → server_worker → start_thread → clone3 | 0.785742 | 0.214258 | transient | transient |
| named/site-pure-1 | 2800778c8c769d31 | empty | xmalloc → create_session_state → server_worker → start_thread → clone3 | 0.874855 | 0.125145 | transient | transient |
| named/site-pure-1 | d1b8e7f38b9b0658 | empty | xmalloc → insert_cache_index → server_worker → start_thread → clone3 | 0.183274 | 0.816726 | permanent | permanent |
| named/site-pure-1 | 79ad8781f59e8774 | empty | xmalloc → parse_request_buffer → server_worker → start_thread → clone3 | 0.714997 | 0.285003 | transient | transient |
| named/site-pure-16 | b1f63e1f4cf87cbb | empty | xmalloc → parse_request_buffer → server_worker → start_thread → clone3 | 0.718216 | 0.281784 | transient | transient |
| named/site-pure-16 | d530a5059e084b88 | empty | xmalloc → assemble_response_buffer → server_worker → start_thread → clone3 | 0.785742 | 0.214258 | transient | transient |
| named/site-pure-16 | 2800778c8c769d31 | empty | xmalloc → create_session_state → server_worker → start_thread → clone3 | 0.874855 | 0.125145 | transient | transient |
| named/site-pure-16 | d1b8e7f38b9b0658 | empty | xmalloc → insert_cache_index → server_worker → start_thread → clone3 | 0.183274 | 0.816726 | permanent | permanent |
| named/site-pure-16 | 79ad8781f59e8774 | empty | xmalloc → parse_request_buffer → server_worker → start_thread → clone3 | 0.714997 | 0.285003 | transient | transient |
