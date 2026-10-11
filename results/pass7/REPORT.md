# Pass 7 — stack-only live classification

**Status: 12/12 fragbench prompt/workload blocks; 22/22 regression workloads complete and audited.** Five interleaved warm repetitions per variant. Pass-6 results below remain the historical `v-permanent-1` measurement.

Measured library SHA-256: `cae42e81344dd0838d08f595627fda1256a21eca6a15f2b0251ab7c5d478ca92`. Full Linux correctness passed for all 22 workloads.

Code-only Clef captures 99.1% of the oracle idle-RSS saving on site-pure with one thread and 94.0% with 16 threads; omitting the description gives 99.1% and 94.8%. All five queried first-sight sites agree with the oracle. Runtime Clef captures only 20.6% and 14.2%: the requested confidence/age gate still admits an early, incorrect session promotion before any session ends. Redis model byte coverage rises from about 2% in pass 6 to about 99.8%; neither the mixed-site nor Redis fragmentation workloads show positive oracle savings. Timing costs and acceptance-target misses are reported below without further prompt or policy tuning.

The default `stack-v1` includes a neutral hand-written program description and up to 12 function/file/line stack frames, without source. `stack-v1-nodesc` omits the description. The old descriptions are retained verbatim in `descriptions-leaky/`; the old prompt was not rerun. The two new prompt variants isolate the description in first-sight context; comparisons with pass 6 also include the byte gate, budget and runtime-policy changes, so they are not a source-only causal ablation. Site keys remain four frames. The oracle remains the prior-trace byte-majority transient/permanent label (permanent = never freed or alive through more than half the final allocation volume).

All live policies admit a site only after at least 64 KiB of successful requested bytes; smaller sites remain transient. Admission is checked before the next allocation after crossing the threshold. A one-shot large allocation can therefore remain unasked; Barnes is an observed 0%-coverage case with six large one-allocation sites. Counter batching can also delay admission. Each cold model schedule has 1,500 slots shared with replay coverage fills, including cached answers and rechecks. Byte coverage counts all requested bytes from sites with a model-backed answer, including bytes allocated before the answer; it is not the fraction allocated after classification. Published totals can omit up to 4,095 unmerged allocations per still-active thread/site at exit; sample clocks and concurrent snapshots are approximate.

For an initially transient site, runtime Clef can promote to permanent only with permanent probability at least 0.8 and oldest still-live reservoir sample age strictly above one quarter of the current requested-byte clock. The heuristic uses a uniform 128-entry reservoir, requires at least 16 entries, and examines entries strictly older than the lower count-median age: permanent requires less than 5% freed requested bytes in that cohort AND the same age gate. Otherwise transient. Freed entries remain in the reservoir; sample selection is independent of survival. Age uses surviving reservoir entries and the batched clock, not the final run length.

Headline timings replay recorded decisions with unchanged live sampling and no inference. Cold inference and coverage-fill costs are separate below. Missing-slot probes are excluded and retried after fills. Warm request state can drift from the cold state: replay measures the recorded policy, not whether fresh inference would repeat its answers. Model-server memory is excluded. Five observations give medians and ranges, not equivalence claims. Settle time is included in fragbench wall time. The independent server-log audit found no inference overlap in the published warm runs.

## Fragmentation

| Prompt | Workload | mi idle MiB | Oracle MiB | Oracle saving | Code-only MiB / capture | Runtime MiB / capture | Heuristic MiB / capture |
|---|---|---:|---:|---:|---:|---:|---:|
| stack-v1 | site-pure-1 | 280.22 | 41.36 | 85.2% | 43.57 / 99.1% | 231.13 / 20.6% | 228.54 / 21.6% |
| stack-v1 | site-pure-16 | 296.55 | 51.68 | 82.6% | 66.36 / 94.0% | 261.70 / 14.2% | 262.83 / 13.8% |
| stack-v1-nodesc | site-pure-1 | 280.21 | 41.33 | 85.3% | 43.57 / 99.1% | 231.13 / 20.5% | 228.51 / 21.6% |
| stack-v1-nodesc | site-pure-16 | 296.55 | 51.53 | 82.6% | 64.27 / 94.8% | 260.20 / 14.8% | 261.50 / 14.3% |
| stack-v1 | site-mixed-1 | 144.70 | 144.98 | -0.2% | 146.36 / n/a | 154.28 / n/a | 146.43 / n/a |
| stack-v1 | site-mixed-16 | 146.43 | 149.67 | -2.2% | 154.39 / n/a | 164.95 / n/a | 154.89 / n/a |
| stack-v1 | redis-mesh | 183.95 | 185.96 | -1.1% | 192.90 / n/a | 224.95 / n/a | 226.93 / n/a |
| stack-v1 | redis-drop | 269.43 | 271.02 | -0.6% | 277.69 / n/a | 277.84 / n/a | 277.78 / n/a |
| stack-v1-nodesc | site-mixed-1 | 144.70 | 144.98 | -0.2% | 146.37 / n/a | 154.28 / n/a | 146.42 / n/a |
| stack-v1-nodesc | site-mixed-16 | 146.43 | 149.62 | -2.2% | 154.57 / n/a | 166.34 / n/a | 154.96 / n/a |
| stack-v1-nodesc | redis-mesh | 185.95 | 186.01 | -0.0% | 192.90 / n/a | 220.93 / n/a | 230.93 / n/a |
| stack-v1-nodesc | redis-drop | 270.52 | 271.37 | -0.3% | 277.28 / n/a | 277.49 / n/a | 277.73 / n/a |

Capture = (mi RSS − policy RSS)/(mi RSS − oracle RSS). It is undefined (`n/a`) when the oracle saves no memory; tiny oracle savings make this ratio unstable. Negative values are retained.

## Time, model coverage and cold cost

Score is normalized inverse throughput for duration-limited regression workloads and Redis regression; otherwise it is wall time. Lower is better.

| Prompt | Workload | Policy | Wall/mi | Score/mi | CPU/mi | Cold byte coverage | Warm byte coverage | Model slots / rechecks | Cold wall s | Cold+fill HTTP s |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| stack-v1 | site-pure-1 | heuristic | 1.075 | 1.075 | 1.839 | n/a | n/a | 0 / 0 | 1.2 | 0.0 |
| stack-v1 | site-pure-1 | static-model | 1.148 | 1.148 | 2.829 | 100.00% | 100.00% | 5 / 0 | 8.2 | 6.8 |
| stack-v1 | site-pure-1 | model | 1.069 | 1.069 | 1.761 | 100.00% | 100.00% | 20 / 15 | 28.1 | 26.7 |
| stack-v1 | site-pure-16 | heuristic | 1.020 | 1.020 | 1.205 | n/a | n/a | 0 / 0 | 1.1 | 0.0 |
| stack-v1 | site-pure-16 | static-model | 1.019 | 1.019 | 1.420 | 100.00% | 100.00% | 5 / 0 | 1.2 | 0.0 |
| stack-v1 | site-pure-16 | model | 1.023 | 1.023 | 1.271 | 100.00% | 100.00% | 20 / 15 | 26.2 | 25.0 |
| stack-v1-nodesc | site-pure-1 | heuristic | 1.073 | 1.073 | 1.821 | n/a | n/a | 0 / 0 | 1.2 | 0.0 |
| stack-v1-nodesc | site-pure-1 | static-model | 1.148 | 1.148 | 2.823 | 100.00% | 100.00% | 5 / 0 | 8.0 | 6.6 |
| stack-v1-nodesc | site-pure-1 | model | 1.069 | 1.069 | 1.775 | 100.00% | 100.00% | 20 / 15 | 24.4 | 23.1 |
| stack-v1-nodesc | site-pure-16 | heuristic | 1.017 | 1.017 | 1.176 | n/a | n/a | 0 / 0 | 1.1 | 0.0 |
| stack-v1-nodesc | site-pure-16 | static-model | 1.021 | 1.021 | 1.503 | 100.00% | 100.00% | 5 / 0 | 1.2 | 0.0 |
| stack-v1-nodesc | site-pure-16 | model | 1.019 | 1.019 | 1.154 | 100.00% | 100.00% | 20 / 15 | 21.6 | 20.3 |
| stack-v1 | site-mixed-1 | heuristic | 1.048 | 1.048 | 1.347 | n/a | n/a | 0 / 0 | 1.2 | 0.0 |
| stack-v1 | site-mixed-1 | static-model | 1.044 | 1.044 | 1.344 | 100.00% | 100.00% | 4 / 0 | 2.8 | 1.4 |
| stack-v1 | site-mixed-1 | model | 1.008 | 1.008 | 1.035 | 100.00% | 100.00% | 16 / 12 | 8.5 | 7.2 |
| stack-v1 | site-mixed-16 | heuristic | 1.014 | 1.014 | 1.047 | n/a | n/a | 0 / 0 | 1.1 | 0.0 |
| stack-v1 | site-mixed-16 | static-model | 1.012 | 1.012 | 1.160 | 100.00% | 100.00% | 4 / 0 | 1.2 | 0.0 |
| stack-v1 | site-mixed-16 | model | 1.005 | 1.005 | 1.005 | 100.00% | 100.00% | 17 / 13 | 8.4 | 7.2 |
| stack-v1 | redis-mesh | heuristic | 1.033 | 1.033 | 1.142 | n/a | n/a | 0 / 0 | 4.0 | 0.0 |
| stack-v1 | redis-mesh | static-model | 1.075 | 1.075 | 1.207 | 99.81% | 99.81% | 12 / 0 | 30.0 | 25.2 |
| stack-v1 | redis-mesh | model | 1.036 | 1.036 | 1.148 | 99.81% | 99.81% | 43 / 31 | 80.6 | 75.7 |
| stack-v1 | redis-drop | heuristic | 1.010 | 1.010 | 1.170 | n/a | n/a | 0 / 0 | 2.5 | 0.0 |
| stack-v1 | redis-drop | static-model | 1.011 | 1.011 | 1.157 | 99.78% | 99.78% | 13 / 0 | 7.2 | 4.2 |
| stack-v1 | redis-drop | model | 1.010 | 1.010 | 1.168 | 99.78% | 99.78% | 38 / 25 | 48.1 | 45.1 |
| stack-v1-nodesc | site-mixed-1 | heuristic | 1.052 | 1.052 | 1.348 | n/a | n/a | 0 / 0 | 1.2 | 0.0 |
| stack-v1-nodesc | site-mixed-1 | static-model | 1.048 | 1.048 | 1.344 | 100.00% | 100.00% | 4 / 0 | 2.8 | 1.4 |
| stack-v1-nodesc | site-mixed-1 | model | 1.010 | 1.010 | 1.030 | 100.00% | 100.00% | 16 / 12 | 8.2 | 6.9 |
| stack-v1-nodesc | site-mixed-16 | heuristic | 1.019 | 1.019 | 1.148 | n/a | n/a | 0 / 0 | 1.1 | 0.0 |
| stack-v1-nodesc | site-mixed-16 | static-model | 1.012 | 1.012 | 1.219 | 100.00% | 100.00% | 4 / 0 | 1.2 | 0.0 |
| stack-v1-nodesc | site-mixed-16 | model | 1.005 | 1.005 | 0.950 | 100.00% | 100.00% | 17 / 13 | 9.5 | 8.2 |
| stack-v1-nodesc | redis-mesh | heuristic | 1.081 | 1.081 | 1.178 | n/a | n/a | 0 / 0 | 4.0 | 0.0 |
| stack-v1-nodesc | redis-mesh | static-model | 1.052 | 1.052 | 1.162 | 99.81% | 99.81% | 12 / 0 | 27.9 | 23.1 |
| stack-v1-nodesc | redis-mesh | model | 1.049 | 1.049 | 1.155 | 99.79% | 99.80% | 43 / 31 | 75.0 | 70.4 |
| stack-v1-nodesc | redis-drop | heuristic | 1.003 | 1.003 | 1.156 | n/a | n/a | 0 / 0 | 2.4 | 0.0 |
| stack-v1-nodesc | redis-drop | static-model | 1.008 | 1.008 | 1.136 | 99.81% | 99.81% | 13 / 0 | 7.0 | 4.0 |
| stack-v1-nodesc | redis-drop | model | 1.006 | 1.006 | 1.169 | 99.78% | 99.81% | 38 / 25 | 46.7 | 43.7 |
| stack-v1 | cfrac | heuristic | 1.954 | 1.954 | 1.930 | n/a | n/a | 0 / 0 | 5.2 | 0.0 |
| stack-v1 | cfrac | static-model | 1.830 | 1.830 | 1.822 | 99.96% | 99.96% | 66 / 0 | 102.0 | 96.5 |
| stack-v1 | cfrac | model | 1.924 | 1.924 | 1.898 | 99.96% | 99.96% | 229 / 163 | 252.8 | 246.9 |
| stack-v1 | espresso | heuristic | 1.552 | 1.552 | 1.419 | n/a | n/a | 0 / 0 | 4.6 | 0.0 |
| stack-v1 | espresso | static-model | 1.456 | 1.456 | 1.402 | 99.80% | 99.80% | 500 / 0 | 799.1 | 791.4 |
| stack-v1 | espresso | model | 1.579 | 1.579 | 1.441 | 99.80% | 99.80% | 1235 / 735 | 1342.6 | 1333.4 |
| stack-v1 | barnes | heuristic | 1.003 | 1.003 | 1.003 | n/a | n/a | 0 / 0 | 1.8 | 0.0 |
| stack-v1 | barnes | static-model | 1.002 | 1.002 | 1.002 | 0.00% | 0.00% | 0 / 0 | 1.8 | 0.0 |
| stack-v1 | barnes | model | 0.999 | 0.999 | 1.000 | 0.00% | 0.00% | 0 / 0 | 1.8 | 0.0 |
| stack-v1 | larson | heuristic | 1.003 | 2.052 | 1.005 | n/a | n/a | 0 / 0 | 7.1 | 0.0 |
| stack-v1 | larson | static-model | 1.001 | 2.041 | 1.005 | 100.00% | 100.00% | 4 / 0 | 9.9 | 5.5 |
| stack-v1 | larson | model | 1.002 | 2.027 | 1.005 | 100.00% | 100.00% | 15 / 11 | 18.2 | 19.5 |
| stack-v1 | larson-sized | heuristic | 1.003 | 2.035 | 1.005 | n/a | n/a | 0 / 0 | 7.1 | 0.0 |
| stack-v1 | larson-sized | static-model | 1.001 | 2.030 | 1.005 | 100.00% | 100.00% | 4 / 0 | 9.9 | 5.5 |
| stack-v1 | larson-sized | model | 1.003 | 2.034 | 1.004 | 100.00% | 100.00% | 15 / 11 | 18.3 | 19.5 |
| stack-v1 | xmalloc-test | heuristic | 1.000 | 3.277 | 0.990 | n/a | n/a | 0 / 0 | 5.0 | 0.0 |
| stack-v1 | xmalloc-test | static-model | 1.000 | 3.277 | 0.993 | 100.00% | 100.00% | 2 / 0 | 5.0 | 2.7 |
| stack-v1 | xmalloc-test | model | 1.000 | 3.297 | 0.995 | 99.86% | 100.00% | 9 / 7 | 5.0 | 11.2 |
| stack-v1 | cache-scratch1 | heuristic | 1.008 | 1.008 | 1.008 | n/a | n/a | 0 / 0 | 2.7 | 0.0 |
| stack-v1 | cache-scratch1 | static-model | 0.989 | 0.989 | 0.988 | 0.00% | 0.00% | 0 / 0 | 2.8 | 0.0 |
| stack-v1 | cache-scratch1 | model | 0.995 | 0.995 | 0.995 | 0.00% | 0.00% | 0 / 0 | 2.8 | 0.0 |
| stack-v1 | cache-scratchN | heuristic | 1.002 | 1.002 | 1.000 | n/a | n/a | 0 / 0 | 0.1 | 0.0 |
| stack-v1 | cache-scratchN | static-model | 1.001 | 1.001 | 0.998 | 0.00% | 0.00% | 0 / 0 | 0.1 | 0.0 |
| stack-v1 | cache-scratchN | model | 0.999 | 0.999 | 1.000 | 0.00% | 0.00% | 0 / 0 | 0.1 | 0.0 |
| stack-v1 | cache-thrash1 | heuristic | 0.963 | 0.963 | 0.963 | n/a | n/a | 0 / 0 | 2.8 | 0.0 |
| stack-v1 | cache-thrash1 | static-model | 0.974 | 0.974 | 0.974 | 0.00% | 0.00% | 0 / 0 | 2.8 | 0.0 |
| stack-v1 | cache-thrash1 | model | 0.978 | 0.978 | 0.978 | 0.00% | 0.00% | 0 / 0 | 2.8 | 0.0 |
| stack-v1 | cache-thrashN | heuristic | 0.996 | 0.996 | 0.997 | n/a | n/a | 0 / 0 | 0.1 | 0.0 |
| stack-v1 | cache-thrashN | static-model | 1.009 | 1.009 | 1.007 | 0.00% | 0.00% | 0 / 0 | 0.1 | 0.0 |
| stack-v1 | cache-thrashN | model | 0.994 | 0.994 | 0.999 | 0.00% | 0.00% | 0 / 0 | 0.1 | 0.0 |
| stack-v1 | mstress | heuristic | 1.076 | 1.076 | 1.025 | n/a | n/a | 0 / 0 | 0.8 | 0.0 |
| stack-v1 | mstress | static-model | 1.067 | 1.067 | 1.029 | 100.00% | 100.00% | 20 / 0 | 13.4 | 12.3 |
| stack-v1 | mstress | model | 1.063 | 1.063 | 1.008 | 100.00% | 100.00% | 47 / 27 | 46.0 | 46.6 |
| stack-v1 | rptest | heuristic | 1.000 | 0.988 | 0.916 | n/a | n/a | 0 / 0 | 16.0 | 0.0 |
| stack-v1 | rptest | static-model | 1.000 | 0.993 | 0.927 | 100.00% | 100.00% | 7 / 0 | 18.0 | 2.7 |
| stack-v1 | rptest | model | 1.000 | 1.037 | 0.951 | 100.00% | 100.00% | 22 / 15 | 41.0 | 25.9 |
| stack-v1 | glibc-simple | heuristic | 2.026 | 2.026 | 1.993 | n/a | n/a | 0 / 0 | 2.7 | 0.0 |
| stack-v1 | glibc-simple | static-model | 1.995 | 1.995 | 1.988 | 100.00% | 100.00% | 31 / 0 | 17.2 | 14.2 |
| stack-v1 | glibc-simple | model | 2.035 | 2.035 | 1.998 | 100.00% | 100.00% | 155 / 124 | 118.6 | 115.2 |
| stack-v1 | glibc-thread | heuristic | 1.000 | 3.253 | 0.996 | n/a | n/a | 0 / 0 | 2.0 | 0.0 |
| stack-v1 | glibc-thread | static-model | 1.000 | 3.149 | 0.997 | 100.00% | 100.00% | 1 / 0 | 2.0 | 1.4 |
| stack-v1 | glibc-thread | model | 1.001 | 3.234 | 0.996 | 99.58% | 100.00% | 5 / 4 | 3.6 | 6.9 |
| stack-v1 | alloc-test1 | heuristic | 1.495 | 1.495 | 1.493 | n/a | n/a | 0 / 0 | 3.0 | 0.0 |
| stack-v1 | alloc-test1 | static-model | 1.493 | 1.493 | 1.493 | 99.69% | 99.69% | 2 / 0 | 4.6 | 1.4 |
| stack-v1 | alloc-test1 | model | 1.504 | 1.504 | 1.502 | 99.69% | 99.69% | 9 / 7 | 15.9 | 12.7 |
| stack-v1 | alloc-testN | heuristic | 1.765 | 1.765 | 1.762 | n/a | n/a | 0 / 0 | 4.9 | 0.0 |
| stack-v1 | alloc-testN | static-model | 1.768 | 1.768 | 1.764 | 99.98% | 99.98% | 3 / 0 | 7.5 | 2.2 |
| stack-v1 | alloc-testN | model | 1.763 | 1.763 | 1.760 | 99.98% | 99.98% | 10 / 7 | 17.9 | 12.7 |
| stack-v1 | malloc-large | heuristic | 1.006 | 1.006 | 1.001 | n/a | n/a | 0 / 0 | 0.4 | 0.0 |
| stack-v1 | malloc-large | static-model | 1.006 | 1.006 | 1.002 | 100.00% | 100.00% | 1 / 0 | 1.8 | 1.4 |
| stack-v1 | malloc-large | model | 1.003 | 1.003 | 0.998 | 100.00% | 100.00% | 2 / 1 | 2.2 | 1.8 |
| stack-v1 | mleak10 | heuristic | 1.375 | 1.375 | 1.967 | n/a | n/a | 0 / 0 | 0.1 | 0.0 |
| stack-v1 | mleak10 | static-model | 1.330 | 1.330 | 1.855 | 97.15% | 97.15% | 2 / 0 | 3.2 | 2.8 |
| stack-v1 | mleak10 | model | 1.363 | 1.363 | 1.986 | 97.15% | 97.15% | 4 / 2 | 3.9 | 3.5 |
| stack-v1 | mleak100 | heuristic | 1.343 | 1.343 | 2.060 | n/a | n/a | 0 / 0 | 1.2 | 0.0 |
| stack-v1 | mleak100 | static-model | 1.346 | 1.346 | 2.071 | 99.97% | 99.97% | 3 / 0 | 2.9 | 1.4 |
| stack-v1 | mleak100 | model | 1.339 | 1.339 | 2.050 | 99.97% | 99.97% | 8 / 5 | 6.6 | 5.0 |
| stack-v1 | sh6benchN | heuristic | 9.216 | 9.216 | 9.750 | n/a | n/a | 0 / 0 | 1.4 | 0.0 |
| stack-v1 | sh6benchN | static-model | 9.242 | 9.242 | 9.787 | 100.00% | 100.00% | 1 / 0 | 2.9 | 1.3 |
| stack-v1 | sh6benchN | model | 9.141 | 9.141 | 9.730 | 100.00% | 100.00% | 5 / 4 | 7.1 | 5.5 |
| stack-v1 | sh8benchN | heuristic | 5.682 | 5.682 | 5.884 | n/a | n/a | 0 / 0 | 2.4 | 0.0 |
| stack-v1 | sh8benchN | static-model | 5.747 | 5.747 | 6.030 | 99.64% | 99.64% | 2 / 0 | 4.3 | 3.0 |
| stack-v1 | sh8benchN | model | 5.735 | 5.735 | 5.966 | 99.64% | 99.64% | 10 / 8 | 15.1 | 14.1 |
| stack-v1 | redis | heuristic | 1.018 | 1.432 | 1.374 | n/a | n/a | 0 / 0 | 4.3 | 0.0 |
| stack-v1 | redis | static-model | 1.011 | 1.378 | 1.359 | 99.98% | 99.98% | 7 / 0 | 9.2 | 4.6 |
| stack-v1 | redis | model | 1.011 | 1.432 | 1.375 | 99.98% | 99.98% | 20 / 13 | 19.1 | 14.5 |

Model slots include coverage fills; rechecks count model-backed noninitial answers. Heuristic uses no model, so model byte coverage is n/a. HTTP time can include queueing behind the independent prompt study and is not isolated inference speed.

## Regression (peak RSS)

These are peak RSS measurements of short programs, rather than idle fragmentation. All 12 variants, timing ranges and inverse-throughput score ratios are in the detailed table. Duration-limited workloads do not provide fixed-work RSS comparisons.

| Prompt | Workload | mi peak MiB | Oracle MiB | Oracle saving | Code-only MiB / capture | Runtime MiB / capture | Heuristic MiB / capture |
|---|---|---:|---:|---:|---:|---:|---:|
| stack-v1 | cfrac | 4.27 | 4.42 | -3.5% | 7.43 / n/a | 7.44 / n/a | 7.44 / n/a |
| stack-v1 | espresso | 10.14 | 10.23 | -0.9% | 22.96 / n/a | 22.44 / n/a | 18.78 / n/a |
| stack-v1 | barnes | 63.34 | 63.38 | -0.1% | 65.57 / n/a | 65.45 / n/a | 65.57 / n/a |
| stack-v1 | larson | 157.88 | 180.20 | -14.1% | 182.85 / n/a | 182.74 / n/a | 222.84 / n/a |
| stack-v1 | larson-sized | 154.82 | 179.74 | -16.1% | 182.73 / n/a | 218.81 / n/a | 218.80 / n/a |
| stack-v1 | xmalloc-test | 136.45 | 106.60 | 21.9% | 93.48 / 143.9% | 89.45 / 157.5% | 95.55 / 137.0% |
| stack-v1 | cache-scratch1 | 6.11 | 6.22 | -1.9% | 5.97 / n/a | 5.97 / n/a | 5.97 / n/a |
| stack-v1 | cache-scratchN | 6.10 | 6.21 | -1.9% | 6.09 / n/a | 6.09 / n/a | 6.09 / n/a |
| stack-v1 | cache-thrash1 | 6.23 | 6.22 | 0.1% | 5.97 / 6600.0% | 5.97 / 6600.0% | 5.97 / 6600.0% |
| stack-v1 | cache-thrashN | 6.11 | 6.10 | 0.1% | 6.09 / 150.0% | 5.98 / 1650.0% | 6.10 / 100.0% |
| stack-v1 | mstress | 512.02 | 874.27 | -70.7% | 635.38 / n/a | 617.21 / n/a | 618.09 / n/a |
| stack-v1 | rptest | 108.11 | 119.03 | -10.1% | 157.77 / n/a | 198.15 / n/a | 134.08 / n/a |
| stack-v1 | glibc-simple | 6.03 | 6.17 | -2.4% | 6.81 / n/a | 6.71 / n/a | 6.80 / n/a |
| stack-v1 | glibc-thread | 68.37 | 68.46 | -0.1% | 101.29 / n/a | 115.13 / n/a | 69.16 / n/a |
| stack-v1 | alloc-test1 | 15.10 | 14.97 | 0.9% | 15.96 / -669.7% | 16.35 / -966.7% | 16.31 / -939.4% |
| stack-v1 | alloc-testN | 16.36 | 18.10 | -10.7% | 19.59 / n/a | 24.10 / n/a | 23.97 / n/a |
| stack-v1 | malloc-large | 649.86 | 649.63 | 0.0% | 640.05 / 4257.6% | 640.05 / 4257.6% | 639.96 / 4296.6% |
| stack-v1 | mleak10 | 24.15 | 44.21 | -83.1% | 44.23 / n/a | 44.22 / n/a | 42.22 / n/a |
| stack-v1 | mleak100 | 24.16 | 44.10 | -82.5% | 35.05 / n/a | 40.21 / n/a | 42.10 / n/a |
| stack-v1 | sh6benchN | 251.41 | 245.89 | 2.2% | 251.66 / -4.6% | 276.38 / -452.7% | 249.20 / 40.1% |
| stack-v1 | sh8benchN | 210.58 | 210.89 | -0.1% | 213.74 / n/a | 219.98 / n/a | 274.01 / n/a |
| stack-v1 | redis | 13.76 | 15.95 | -15.9% | 20.80 / n/a | 20.26 / n/a | 20.32 / n/a |

## Acceptance target misses

Targets are diagnostics, not publication gates. Time targets use wall or inverse-throughput score as appropriate. These medians do not establish statistical significance. Possible causes are shim calls and scheduling/measurement variation for none-time misses, page/thread retention and accounting for RSS misses, and stack capture plus sampled lifetime tracking for live-time misses; these causes have not been independently isolated.

| Workload | Check | Measured ratio | Target |
|---|---|---:|---:|
| cfrac | keyonly_peak_rss/none | 1.032 | 1.03 |
| larson | heuristic_score/oracle | 1.227 | 1.15 |
| larson-sized | none_score/mi | 1.037 | 1.03 |
| larson-sized | heuristic_score/oracle | 1.205 | 1.15 |
| xmalloc-test | heuristic_score/oracle | 1.418 | 1.15 |
| mstress | keyonly_peak_rss/none | 1.047 | 1.03 |
| glibc-thread | none_score/mi | 1.036 | 1.03 |
| alloc-test1 | none_score/mi | 1.036 | 1.03 |
| alloc-testN | none_score/mi | 1.034 | 1.03 |
| mleak100 | keyonly_peak_rss/none | 1.098 | 1.03 |
| sh6benchN | none_score/mi | 1.048 | 1.03 |
| sh6benchN | heuristic_score/oracle | 3.104 | 1.15 |
| sh8benchN | heuristic_score/oracle | 2.276 | 1.15 |

## Dominant site-pure decisions

Classes: 0 transient, 1 permanent. Misclassifications and any later changes are retained without prompt tuning.

stack-v1, site-pure-1, static-model: `assemble_response_buffer` first classified 0 (oracle 0), permanent probability 0.212; decision classes [0].

stack-v1, site-pure-1, static-model: `parse_request_buffer` first classified 0 (oracle 0), permanent probability 0.278; decision classes [0].

stack-v1, site-pure-1, static-model: `create_session_state` first classified 0 (oracle 0), permanent probability 0.133; decision classes [0].

stack-v1, site-pure-1, static-model: `insert_cache_index` first classified 1 (oracle 1), permanent probability 0.797; decision classes [1].

stack-v1, site-pure-1, model: `assemble_response_buffer` first classified 0 (oracle 0), permanent probability 0.212; decision classes [0, 0, 0, 0, 0].

stack-v1, site-pure-1, model: `parse_request_buffer` first classified 0 (oracle 0), permanent probability 0.278; decision classes [0, 0, 0, 0, 0].

stack-v1, site-pure-1, model: `create_session_state` promoted at recheck 1, permanent p=0.906, 100% not freed so far; oldest surviving sample age 1.091 MiB / current clock 1.148 MiB (95.0%). The specified gate admits this promotion.

stack-v1, site-pure-1, model: `create_session_state` first classified 0 (oracle 0), permanent probability 0.133; decision classes [0, 1, 1, 1, 0].

stack-v1, site-pure-1, model: `insert_cache_index` first classified 1 (oracle 1), permanent probability 0.797; decision classes [1, 1, 1, 1].

stack-v1, site-pure-16, static-model: `assemble_response_buffer` first classified 0 (oracle 0), permanent probability 0.212; decision classes [0].

stack-v1, site-pure-16, static-model: `parse_request_buffer` first classified 0 (oracle 0), permanent probability 0.278; decision classes [0].

stack-v1, site-pure-16, static-model: `create_session_state` first classified 0 (oracle 0), permanent probability 0.133; decision classes [0].

stack-v1, site-pure-16, static-model: `insert_cache_index` first classified 1 (oracle 1), permanent probability 0.797; decision classes [1].

stack-v1, site-pure-16, model: `assemble_response_buffer` first classified 0 (oracle 0), permanent probability 0.212; decision classes [0, 0, 0, 0, 0].

stack-v1, site-pure-16, model: `parse_request_buffer` first classified 0 (oracle 0), permanent probability 0.278; decision classes [0, 0, 0, 0, 0].

stack-v1, site-pure-16, model: `create_session_state` promoted at recheck 1, permanent p=0.907, 100% not freed so far; oldest surviving sample age 1.094 MiB / current clock 1.151 MiB (95.1%). The specified gate admits this promotion.

stack-v1, site-pure-16, model: `create_session_state` first classified 0 (oracle 0), permanent probability 0.133; decision classes [0, 1, 1, 1, 0].

stack-v1, site-pure-16, model: `insert_cache_index` first classified 1 (oracle 1), permanent probability 0.797; decision classes [1, 1, 1].

stack-v1-nodesc, site-pure-1, static-model: `assemble_response_buffer` first classified 0 (oracle 0), permanent probability 0.161; decision classes [0].

stack-v1-nodesc, site-pure-1, static-model: `parse_request_buffer` first classified 0 (oracle 0), permanent probability 0.246; decision classes [0].

stack-v1-nodesc, site-pure-1, static-model: `create_session_state` first classified 0 (oracle 0), permanent probability 0.346; decision classes [0].

stack-v1-nodesc, site-pure-1, static-model: `insert_cache_index` first classified 1 (oracle 1), permanent probability 0.685; decision classes [1].

stack-v1-nodesc, site-pure-1, model: `assemble_response_buffer` first classified 0 (oracle 0), permanent probability 0.161; decision classes [0, 0, 0, 0, 0].

stack-v1-nodesc, site-pure-1, model: `parse_request_buffer` first classified 0 (oracle 0), permanent probability 0.246; decision classes [0, 0, 0, 0, 0].

stack-v1-nodesc, site-pure-1, model: `create_session_state` promoted at recheck 1, permanent p=0.908, 100% not freed so far; oldest surviving sample age 1.091 MiB / current clock 1.148 MiB (95.0%). The specified gate admits this promotion.

stack-v1-nodesc, site-pure-1, model: `create_session_state` first classified 0 (oracle 0), permanent probability 0.346; decision classes [0, 1, 1, 1, 0].

stack-v1-nodesc, site-pure-1, model: `insert_cache_index` first classified 1 (oracle 1), permanent probability 0.685; decision classes [1, 1, 1, 1].

stack-v1-nodesc, site-pure-16, static-model: `assemble_response_buffer` first classified 0 (oracle 0), permanent probability 0.161; decision classes [0].

stack-v1-nodesc, site-pure-16, static-model: `parse_request_buffer` first classified 0 (oracle 0), permanent probability 0.246; decision classes [0].

stack-v1-nodesc, site-pure-16, static-model: `create_session_state` first classified 0 (oracle 0), permanent probability 0.346; decision classes [0].

stack-v1-nodesc, site-pure-16, static-model: `insert_cache_index` first classified 1 (oracle 1), permanent probability 0.685; decision classes [1].

stack-v1-nodesc, site-pure-16, model: `assemble_response_buffer` first classified 0 (oracle 0), permanent probability 0.161; decision classes [0, 0, 0, 0, 0].

stack-v1-nodesc, site-pure-16, model: `parse_request_buffer` first classified 0 (oracle 0), permanent probability 0.246; decision classes [0, 0, 0, 0, 0].

stack-v1-nodesc, site-pure-16, model: `create_session_state` promoted at recheck 1, permanent p=0.908, 100% not freed so far; oldest surviving sample age 1.275 MiB / current clock 1.331 MiB (95.8%). The specified gate admits this promotion.

stack-v1-nodesc, site-pure-16, model: `create_session_state` first classified 0 (oracle 0), permanent probability 0.346; decision classes [0, 1, 1, 1, 0].

stack-v1-nodesc, site-pure-16, model: `insert_cache_index` first classified 1 (oracle 1), permanent probability 0.685; decision classes [1, 1, 1].


## Workload interpretation

stack-v1, site-pure-1: oracle saves memory (0.148× mi); runtime Clef does not beat the heuristic on RSS (1.011×). Code-only/runtime/heuristic RSS relative to oracle: 1.053×/5.588×/5.526×.

stack-v1, site-pure-16: oracle saves memory (0.174× mi); runtime Clef beats the heuristic on RSS (0.996×). Code-only/runtime/heuristic RSS relative to oracle: 1.284×/5.063×/5.085×.

stack-v1-nodesc, site-pure-1: oracle saves memory (0.147× mi); runtime Clef does not beat the heuristic on RSS (1.011×). Code-only/runtime/heuristic RSS relative to oracle: 1.054×/5.593×/5.529×.

stack-v1-nodesc, site-pure-16: oracle saves memory (0.174× mi); runtime Clef beats the heuristic on RSS (0.995×). Code-only/runtime/heuristic RSS relative to oracle: 1.247×/5.050×/5.075×.

stack-v1, site-mixed-1: oracle does not save memory (1.002× mi); runtime Clef does not beat the heuristic on RSS (1.054×). Code-only/runtime/heuristic RSS relative to oracle: 1.010×/1.064×/1.010×.

stack-v1, site-mixed-1: fixed-site classification ceiling is 89.40% for the mixed payload site and 96.47% over the workload; this does not bound RSS.

stack-v1, site-mixed-16: oracle does not save memory (1.022× mi); runtime Clef does not beat the heuristic on RSS (1.065×). Code-only/runtime/heuristic RSS relative to oracle: 1.032×/1.102×/1.035×.

stack-v1, site-mixed-16: fixed-site classification ceiling is 89.40% for the mixed payload site and 96.47% over the workload; this does not bound RSS.

stack-v1, redis-mesh: oracle does not save memory (1.011× mi); runtime Clef beats the heuristic on RSS (0.991×). Code-only/runtime/heuristic RSS relative to oracle: 1.037×/1.210×/1.220×.

stack-v1, redis-drop: oracle does not save memory (1.006× mi); runtime Clef does not beat the heuristic on RSS (1.000×). Code-only/runtime/heuristic RSS relative to oracle: 1.025×/1.025×/1.025×.

stack-v1-nodesc, site-mixed-1: oracle does not save memory (1.002× mi); runtime Clef does not beat the heuristic on RSS (1.054×). Code-only/runtime/heuristic RSS relative to oracle: 1.010×/1.064×/1.010×.

stack-v1-nodesc, site-mixed-1: fixed-site classification ceiling is 89.40% for the mixed payload site and 96.47% over the workload; this does not bound RSS.

stack-v1-nodesc, site-mixed-16: oracle does not save memory (1.022× mi); runtime Clef does not beat the heuristic on RSS (1.073×). Code-only/runtime/heuristic RSS relative to oracle: 1.033×/1.112×/1.036×.

stack-v1-nodesc, site-mixed-16: fixed-site classification ceiling is 89.39% for the mixed payload site and 96.47% over the workload; this does not bound RSS.

stack-v1-nodesc, redis-mesh: oracle does not save memory (1.000× mi); runtime Clef beats the heuristic on RSS (0.957×). Code-only/runtime/heuristic RSS relative to oracle: 1.037×/1.188×/1.241×.

stack-v1-nodesc, redis-drop: oracle does not save memory (1.003× mi); runtime Clef beats the heuristic on RSS (0.999×). Code-only/runtime/heuristic RSS relative to oracle: 1.022×/1.023×/1.023×.

stack-v1, cfrac: oracle does not save memory (1.035× mi); runtime Clef does not beat the heuristic on RSS (1.000×). Code-only/runtime/heuristic RSS relative to oracle: 1.681×/1.684×/1.684×.

stack-v1, espresso: oracle does not save memory (1.009× mi); runtime Clef does not beat the heuristic on RSS (1.195×). Code-only/runtime/heuristic RSS relative to oracle: 2.244×/2.194×/1.835×.

stack-v1, barnes: oracle does not save memory (1.001× mi); runtime Clef beats the heuristic on RSS (0.998×). Code-only/runtime/heuristic RSS relative to oracle: 1.035×/1.033×/1.035×.

stack-v1, barnes, static-model: this variant used the default class throughout, with no model-backed decisions.

stack-v1, barnes, model: this variant used the default class throughout, with no model-backed decisions.

stack-v1, larson: oracle does not save memory (1.141× mi); runtime Clef beats the heuristic on RSS (0.820×). Code-only/runtime/heuristic RSS relative to oracle: 1.015×/1.014×/1.237×.

stack-v1, larson-sized: oracle does not save memory (1.161× mi); runtime Clef does not beat the heuristic on RSS (1.000×). Code-only/runtime/heuristic RSS relative to oracle: 1.017×/1.217×/1.217×.

stack-v1, xmalloc-test: oracle saves memory (0.781× mi); runtime Clef beats the heuristic on RSS (0.936×). Code-only/runtime/heuristic RSS relative to oracle: 0.877×/0.839×/0.896×.

stack-v1, cache-scratch1: oracle does not save memory (1.019× mi); runtime Clef does not beat the heuristic on RSS (1.000×). Code-only/runtime/heuristic RSS relative to oracle: 0.960×/0.960×/0.960×.

stack-v1, cache-scratch1, static-model: this variant used the default class throughout, with no model-backed decisions.

stack-v1, cache-scratch1, model: this variant used the default class throughout, with no model-backed decisions.

stack-v1, cache-scratchN: oracle does not save memory (1.019× mi); runtime Clef does not beat the heuristic on RSS (1.000×). Code-only/runtime/heuristic RSS relative to oracle: 0.981×/0.981×/0.981×.

stack-v1, cache-scratchN, static-model: this variant used the default class throughout, with no model-backed decisions.

stack-v1, cache-scratchN, model: this variant used the default class throughout, with no model-backed decisions.

stack-v1, cache-thrash1: oracle saves memory (0.999× mi); runtime Clef does not beat the heuristic on RSS (1.000×). Code-only/runtime/heuristic RSS relative to oracle: 0.959×/0.959×/0.959×.

stack-v1, cache-thrash1, static-model: this variant used the default class throughout, with no model-backed decisions.

stack-v1, cache-thrash1, model: this variant used the default class throughout, with no model-backed decisions.

stack-v1, cache-thrashN: oracle saves memory (0.999× mi); runtime Clef beats the heuristic on RSS (0.980×). Code-only/runtime/heuristic RSS relative to oracle: 0.999×/0.980×/1.000×.

stack-v1, cache-thrashN, static-model: this variant used the default class throughout, with no model-backed decisions.

stack-v1, cache-thrashN, model: this variant used the default class throughout, with no model-backed decisions.

stack-v1, mstress: oracle does not save memory (1.707× mi); runtime Clef beats the heuristic on RSS (0.999×). Code-only/runtime/heuristic RSS relative to oracle: 0.727×/0.706×/0.707×.

stack-v1, rptest: oracle does not save memory (1.101× mi); runtime Clef does not beat the heuristic on RSS (1.478×). Code-only/runtime/heuristic RSS relative to oracle: 1.326×/1.665×/1.126×.

stack-v1, glibc-simple: oracle does not save memory (1.024× mi); runtime Clef beats the heuristic on RSS (0.987×). Code-only/runtime/heuristic RSS relative to oracle: 1.104×/1.087×/1.102×.

stack-v1, glibc-thread: oracle does not save memory (1.001× mi); runtime Clef does not beat the heuristic on RSS (1.665×). Code-only/runtime/heuristic RSS relative to oracle: 1.480×/1.682×/1.010×.

stack-v1, alloc-test1: oracle saves memory (0.991× mi); runtime Clef does not beat the heuristic on RSS (1.002×). Code-only/runtime/heuristic RSS relative to oracle: 1.066×/1.092×/1.089×.

stack-v1, alloc-testN: oracle does not save memory (1.107× mi); runtime Clef does not beat the heuristic on RSS (1.005×). Code-only/runtime/heuristic RSS relative to oracle: 1.083×/1.332×/1.324×.

stack-v1, malloc-large: oracle saves memory (1.000× mi); runtime Clef does not beat the heuristic on RSS (1.000×). Code-only/runtime/heuristic RSS relative to oracle: 0.985×/0.985×/0.985×.

stack-v1, mleak10: oracle does not save memory (1.831× mi); runtime Clef does not beat the heuristic on RSS (1.047×). Code-only/runtime/heuristic RSS relative to oracle: 1.000×/1.000×/0.955×.

stack-v1, mleak100: oracle does not save memory (1.825× mi); runtime Clef beats the heuristic on RSS (0.955×). Code-only/runtime/heuristic RSS relative to oracle: 0.795×/0.912×/0.955×.

stack-v1, sh6benchN: oracle saves memory (0.978× mi); runtime Clef does not beat the heuristic on RSS (1.109×). Code-only/runtime/heuristic RSS relative to oracle: 1.023×/1.124×/1.013×.

stack-v1, sh8benchN: oracle does not save memory (1.001× mi); runtime Clef beats the heuristic on RSS (0.803×). Code-only/runtime/heuristic RSS relative to oracle: 1.014×/1.043×/1.299×.

stack-v1, redis: oracle does not save memory (1.159× mi); runtime Clef beats the heuristic on RSS (0.997×). Code-only/runtime/heuristic RSS relative to oracle: 1.305×/1.271×/1.274×.


Detailed measurements: [warm observations](results/pass7/details.md), [phase medians](results/pass7/phases.md) and [phase records](results/pass7/phases.json), [dominant-site decisions](results/pass7/site-decisions.json), [first-sight accuracy](results/pass7/accuracy.json). Full cold, replay, fill and allocator logs remain on the test machine.
