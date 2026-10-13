# Pass 11 findings



All 24 factorial blocks (2400 runs), four Redis blocks (220 runs), and both diagnostic option sets are complete and inference-audited. Pass 10’s remaining accepted groups and validation were already complete at this pass’s initial inspection and remain uncommitted.



Gate 0.6: 2/6 namings beat both controls by paired median in all four workload/thread conditions (plausible, seed2); 0/6 do so with both pointwise 95% intervals below zero in every condition (none).

- site-pure, 1 threads: beats both controls 3/6 by paired median, 2/6 with both intervals below zero; worse than mi 4/6 by paired median.

- site-pure, 16 threads: beats both controls 3/6 by paired median, 2/6 with both intervals below zero; worse than mi 4/6 by paired median.

- site-mixed, 1 threads: beats both controls 2/6 by paired median, 0/6 with both intervals below zero; worse than mi 6/6 by paired median.

- site-mixed, 16 threads: beats both controls 4/6 by paired median, 0/6 with both intervals below zero; worse than mi 6/6 by paired median.



Gate 0.7: 1/6 namings beat both controls by paired median in all four workload/thread conditions (plausible); 1/6 do so with both pointwise 95% intervals below zero in every condition (plausible).

- site-pure, 1 threads: beats both controls 3/6 by paired median, 3/6 with both intervals below zero; worse than mi 3/6 by paired median.

- site-pure, 16 threads: beats both controls 3/6 by paired median, 3/6 with both intervals below zero; worse than mi 3/6 by paired median.

- site-mixed, 1 threads: beats both controls 2/6 by paired median, 1/6 with both intervals below zero; worse than mi 5/6 by paired median.

- site-mixed, 16 threads: beats both controls 3/6 by paired median, 1/6 with both intervals below zero; worse than mi 5/6 by paired median.



Gate 0.8: 0/6 namings beat both controls by paired median in all four workload/thread conditions (none); 0/6 do so with both pointwise 95% intervals below zero in every condition (none).

- site-pure, 1 threads: beats both controls 0/6 by paired median, 0/6 with both intervals below zero; worse than mi 6/6 by paired median.

- site-pure, 16 threads: beats both controls 0/6 by paired median, 0/6 with both intervals below zero; worse than mi 6/6 by paired median.

- site-mixed, 1 threads: beats both controls 0/6 by paired median, 0/6 with both intervals below zero; worse than mi 6/6 by paired median.

- site-mixed, 16 threads: beats both controls 0/6 by paired median, 0/6 with both intervals below zero; worse than mi 6/6 by paired median.



These counts refer to six fixed namings of two author-designed workloads, not six independent applications. Ten repetitions quantify run variability with frozen priors; the five new mappings each have fresh inference, not ten independent model draws. Pointwise bootstrap intervals are not a family-wide multiple-comparison guarantee. The historical 0.7 plausible-name benefit remains in the record regardless of these additional outcomes.



Guarded unnormalized Redis/defaults static/context: idle 283.484 MiB versus mi 274.848 MiB; target CPU 0.569564 s versus 0.324659 s. Its raw metadata peak median is 7.776 MiB; registered pairs 961; overflow allocations 494960, covering 220.947 requested MiB. Historical unguarded static/context held 4246.531 MiB. This is a boundedness fix; metadata reservations are not a byte-for-byte attribution of RSS.



defaults, mi: idle10 RSS 280.223 MiB, after mi_collect(true) 279.477 MiB, after tagged-heap collection 279.477 MiB. Workload live bytes are unchanged; heap-area used/committed bytes before collection are 29.915/266.199 MiB. Reported committed bytes fall by 18.750 MiB. Forced collection barely changes RSS while heap areas with live blocks contain substantial unused capacity; this supports live-page pinning as the dominant remaining heap cost in this run.

defaults, jev-table:oracle-site: idle10 RSS 213.012 MiB, after mi_collect(true) 187.574 MiB, after tagged-heap collection 41.273 MiB. Workload live bytes are unchanged; heap-area used/committed bytes before collection are 29.922/30.075 MiB. Reported committed bytes fall by 193.062 MiB. The large RSS release without workload frees demonstrates deferred reclamation at ten seconds; this retained RSS cannot all be described as irreducible live-page fragmentation.

defaults, jev-live:static-model: idle10 RSS 215.102 MiB, after mi_collect(true) 111.922 MiB, after tagged-heap collection 43.504 MiB. Workload live bytes are unchanged; heap-area used/committed bytes before collection are 30.447/31.333 MiB. Reported committed bytes fall by 191.875 MiB. The large RSS release without workload frees demonstrates deferred reclamation at ten seconds; this retained RSS cannot all be described as irreducible live-page fragmentation.

immediate, mi: idle10 RSS 280.172 MiB, after mi_collect(true) 279.480 MiB, after tagged-heap collection 279.480 MiB. Workload live bytes are unchanged; heap-area used/committed bytes before collection are 29.915/266.193 MiB. Reported committed bytes fall by 18.750 MiB. Forced collection barely changes RSS while heap areas with live blocks contain substantial unused capacity; this supports live-page pinning as the dominant remaining heap cost in this run.

immediate, jev-table:oracle-site: idle10 RSS 41.383 MiB, after mi_collect(true) 41.258 MiB, after tagged-heap collection 41.141 MiB. Workload live bytes are unchanged; heap-area used/committed bytes before collection are 29.922/30.073 MiB. The reported committed counters are negative and unusable as absolute committed-byte estimates; raw values are retained. Forced collection changes RSS little in this run; the exact counter split remains in the phase table.

immediate, jev-live:static-model: idle10 RSS 43.582 MiB, after mi_collect(true) 43.344 MiB, after tagged-heap collection 43.246 MiB. Workload live bytes are unchanged; heap-area used/committed bytes before collection are 30.447/31.332 MiB. The reported committed counters are negative and unusable as absolute committed-byte estimates; raw values are retained. Forced collection changes RSS little in this run; the exact counter split remains in the phase table.



Mimalloc committed/reserved counters include sparsely touched arenas and are not resident-byte counts; subtracting live bytes from those counters is not an RSS decomposition. The diagnostic uses separate MI_STAT=2 libraries and one observation per policy/options/collection condition. Heap-area inspection can collect delayed frees. It diagnoses this workload/protocol, not an allocator-wide guarantee; RSS also includes bookkeeping, thread resources and metadata. Both option sets preserve identical histories through the final idle10 before the intervention.


