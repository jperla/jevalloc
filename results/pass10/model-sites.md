# Model answers by naming and context

Static first-sight answers under defaults. Probabilities are the recorded native model output; unasked sites remain in each block’s sites.json catalogue.

| Naming / workload | Key | Context | Stack | P(transient) | P(permanent) | Class | Oracle |
|---|---|---|---|---:|---:|---|---|
| named/site-mixed-1 | d1c78a5bcfc55993 | kind=store ttl=0 | xmalloc → store_request_payload → server_worker → start_thread → clone3 | 0.636149 | 0.363851 | transient | transient |
| named/site-mixed-1 | 7290c61dfb50bee4 | kind=store ttl=0 | xmalloc → parse_request_buffer → server_worker → start_thread → clone3 | 0.681621 | 0.318379 | transient | transient |
| named/site-mixed-1 | 1e9b6686eaa93623 | kind=store ttl=0 | xmalloc → assemble_response_buffer → server_worker → start_thread → clone3 | 0.754975 | 0.245025 | transient | transient |
| named/site-mixed-1 | ad3382736f297fa3 | kind=store ttl=short | xmalloc → store_request_payload → server_worker → start_thread → clone3 | 0.704171 | 0.295829 | transient | transient |
| named/site-mixed-1 | 6759e825e7719e95 | kind=store ttl=short | xmalloc → parse_request_buffer → server_worker → start_thread → clone3 | 0.749658 | 0.250342 | transient | transient |
| named/site-mixed-1 | 63151fb39c0517a4 | kind=store ttl=short | xmalloc → assemble_response_buffer → server_worker → start_thread → clone3 | 0.818877 | 0.181123 | transient | transient |
| named/site-mixed-1 | 8928cdbd63df0455 | kind=store ttl=day | xmalloc → store_request_payload → server_worker → start_thread → clone3 | 0.367783 | 0.632217 | permanent | permanent |
| named/site-mixed-1 | fd069064c50bb447 | kind=store ttl=day | xmalloc → parse_request_buffer → server_worker → start_thread → clone3 | 0.566293 | 0.433707 | transient | transient |
| named/site-mixed-1 | b71dd8ec8f13acf5 | kind=store ttl=day | xmalloc → assemble_response_buffer → server_worker → start_thread → clone3 | 0.654076 | 0.345924 | transient | transient |
| named/site-mixed-1 | 79ad8781f59e8774 | empty | xmalloc → parse_request_buffer → server_worker → start_thread → clone3 | 0.714997 | 0.285003 | transient | transient |
| named/site-mixed-16 | d1c78a5bcfc55993 | kind=store ttl=0 | xmalloc → store_request_payload → server_worker → start_thread → clone3 | 0.636149 | 0.363851 | transient | transient |
| named/site-mixed-16 | 7290c61dfb50bee4 | kind=store ttl=0 | xmalloc → parse_request_buffer → server_worker → start_thread → clone3 | 0.681621 | 0.318379 | transient | transient |
| named/site-mixed-16 | 1e9b6686eaa93623 | kind=store ttl=0 | xmalloc → assemble_response_buffer → server_worker → start_thread → clone3 | 0.754975 | 0.245025 | transient | transient |
| named/site-mixed-16 | ad3382736f297fa3 | kind=store ttl=short | xmalloc → store_request_payload → server_worker → start_thread → clone3 | 0.704171 | 0.295829 | transient | transient |
| named/site-mixed-16 | 6759e825e7719e95 | kind=store ttl=short | xmalloc → parse_request_buffer → server_worker → start_thread → clone3 | 0.749658 | 0.250342 | transient | transient |
| named/site-mixed-16 | 63151fb39c0517a4 | kind=store ttl=short | xmalloc → assemble_response_buffer → server_worker → start_thread → clone3 | 0.818877 | 0.181123 | transient | transient |
| named/site-mixed-16 | 8928cdbd63df0455 | kind=store ttl=day | xmalloc → store_request_payload → server_worker → start_thread → clone3 | 0.367783 | 0.632217 | permanent | permanent |
| named/site-mixed-16 | fd069064c50bb447 | kind=store ttl=day | xmalloc → parse_request_buffer → server_worker → start_thread → clone3 | 0.566293 | 0.433707 | transient | transient |
| named/site-mixed-16 | b71dd8ec8f13acf5 | kind=store ttl=day | xmalloc → assemble_response_buffer → server_worker → start_thread → clone3 | 0.654076 | 0.345924 | transient | transient |
| named/site-mixed-16 | 79ad8781f59e8774 | empty | xmalloc → parse_request_buffer → server_worker → start_thread → clone3 | 0.714997 | 0.285003 | transient | transient |
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
| opaque/site-mixed-1 | f650e70a986740ba | k=0 | xmalloc → fn_e → server_worker → start_thread → clone3 | 0.511350 | 0.488650 | transient | transient |
| opaque/site-mixed-1 | 28d687b5405cd5f2 | k=0 | xmalloc → fn_a → server_worker → start_thread → clone3 | 0.516829 | 0.483171 | transient | transient |
| opaque/site-mixed-1 | f3cf17c51dd5e7ea | k=0 | xmalloc → fn_b → server_worker → start_thread → clone3 | 0.542156 | 0.457844 | transient | transient |
| opaque/site-mixed-1 | caabb39531501790 | k=1 | xmalloc → fn_e → server_worker → start_thread → clone3 | 0.578836 | 0.421164 | transient | transient |
| opaque/site-mixed-1 | a35a0702940c1cbd | k=1 | xmalloc → fn_a → server_worker → start_thread → clone3 | 0.568491 | 0.431509 | transient | transient |
| opaque/site-mixed-1 | dc5ae2e0e1f135d8 | k=1 | xmalloc → fn_b → server_worker → start_thread → clone3 | 0.602649 | 0.397351 | transient | transient |
| opaque/site-mixed-1 | 8282c56a3ab0825d | k=2 | xmalloc → fn_e → server_worker → start_thread → clone3 | 0.603376 | 0.396624 | transient | permanent |
| opaque/site-mixed-1 | 2f234ca101518bcd | k=2 | xmalloc → fn_a → server_worker → start_thread → clone3 | 0.605311 | 0.394689 | transient | transient |
| opaque/site-mixed-1 | 86c5ceee7bd7b5de | k=2 | xmalloc → fn_b → server_worker → start_thread → clone3 | 0.633817 | 0.366183 | transient | transient |
| opaque/site-mixed-1 | e6ab1a46631f359d | empty | xmalloc → fn_a → server_worker → start_thread → clone3 | 0.587907 | 0.412093 | transient | transient |
| opaque/site-mixed-16 | f650e70a986740ba | k=0 | xmalloc → fn_e → server_worker → start_thread → clone3 | 0.511350 | 0.488650 | transient | transient |
| opaque/site-mixed-16 | 28d687b5405cd5f2 | k=0 | xmalloc → fn_a → server_worker → start_thread → clone3 | 0.516829 | 0.483171 | transient | transient |
| opaque/site-mixed-16 | f3cf17c51dd5e7ea | k=0 | xmalloc → fn_b → server_worker → start_thread → clone3 | 0.542156 | 0.457844 | transient | transient |
| opaque/site-mixed-16 | caabb39531501790 | k=1 | xmalloc → fn_e → server_worker → start_thread → clone3 | 0.578836 | 0.421164 | transient | transient |
| opaque/site-mixed-16 | a35a0702940c1cbd | k=1 | xmalloc → fn_a → server_worker → start_thread → clone3 | 0.568491 | 0.431509 | transient | transient |
| opaque/site-mixed-16 | dc5ae2e0e1f135d8 | k=1 | xmalloc → fn_b → server_worker → start_thread → clone3 | 0.602649 | 0.397351 | transient | transient |
| opaque/site-mixed-16 | 8282c56a3ab0825d | k=2 | xmalloc → fn_e → server_worker → start_thread → clone3 | 0.603376 | 0.396624 | transient | permanent |
| opaque/site-mixed-16 | 2f234ca101518bcd | k=2 | xmalloc → fn_a → server_worker → start_thread → clone3 | 0.605311 | 0.394689 | transient | transient |
| opaque/site-mixed-16 | 86c5ceee7bd7b5de | k=2 | xmalloc → fn_b → server_worker → start_thread → clone3 | 0.633817 | 0.366183 | transient | transient |
| opaque/site-mixed-16 | e6ab1a46631f359d | empty | xmalloc → fn_a → server_worker → start_thread → clone3 | 0.587907 | 0.412093 | transient | transient |
| opaque/site-pure-1 | 4df8df3b1536a5e6 | empty | xmalloc → fn_a → server_worker → start_thread → clone3 | 0.594191 | 0.405809 | transient | transient |
| opaque/site-pure-1 | 0faa8e84fdd3c0a4 | empty | xmalloc → fn_b → server_worker → start_thread → clone3 | 0.597297 | 0.402703 | transient | transient |
| opaque/site-pure-1 | 6f22fe2acb8efeed | empty | xmalloc → fn_c → server_worker → start_thread → clone3 | 0.568800 | 0.431200 | transient | transient |
| opaque/site-pure-1 | 31b4a969152f71a9 | empty | xmalloc → fn_d → server_worker → start_thread → clone3 | 0.589242 | 0.410758 | transient | permanent |
| opaque/site-pure-1 | e6ab1a46631f359d | empty | xmalloc → fn_a → server_worker → start_thread → clone3 | 0.587907 | 0.412093 | transient | transient |
| opaque/site-pure-16 | 4df8df3b1536a5e6 | empty | xmalloc → fn_a → server_worker → start_thread → clone3 | 0.594191 | 0.405809 | transient | transient |
| opaque/site-pure-16 | 0faa8e84fdd3c0a4 | empty | xmalloc → fn_b → server_worker → start_thread → clone3 | 0.597297 | 0.402703 | transient | transient |
| opaque/site-pure-16 | 6f22fe2acb8efeed | empty | xmalloc → fn_c → server_worker → start_thread → clone3 | 0.568800 | 0.431200 | transient | transient |
| opaque/site-pure-16 | 31b4a969152f71a9 | empty | xmalloc → fn_d → server_worker → start_thread → clone3 | 0.589242 | 0.410758 | transient | permanent |
| opaque/site-pure-16 | e6ab1a46631f359d | empty | xmalloc → fn_a → server_worker → start_thread → clone3 | 0.587907 | 0.412093 | transient | transient |
| plausible/site-pure-1 | 3ae0a936eeeb4cfb | empty | xmalloc → buf_get → server_worker → start_thread → clone3 | 0.743953 | 0.256047 | transient | transient |
| plausible/site-pure-1 | 29576832f1f5b260 | empty | xmalloc → resp_build → server_worker → start_thread → clone3 | 0.738968 | 0.261032 | transient | transient |
| plausible/site-pure-1 | fcbeb76a3434e316 | empty | xmalloc → conn_attach → server_worker → start_thread → clone3 | 0.733194 | 0.266806 | transient | transient |
| plausible/site-pure-1 | 3e6e881d5301cf0a | empty | xmalloc → entry_put → server_worker → start_thread → clone3 | 0.549059 | 0.450941 | transient | permanent |
| plausible/site-pure-1 | 9b90b058545f9dfb | empty | xmalloc → buf_get → server_worker → start_thread → clone3 | 0.738635 | 0.261365 | transient | transient |
