# Trace Analysis

> **Note:** This file reports the trace-driven study (six trace files, 64 to 384 requests each).
> The shorter directed-testbench results (`cache_tb.v`, 103 checks) are in `results.md`.
> The two sets are different experiments, so their numbers are not meant to match.

## 1. Method
`scripts/gen_traces.py` creates six trace files in `traces/` (fixed random seed). The
trace-driven testbench `testbench/tb_trace.v` sends every request of a file to the cache
and counts hits and misses. `scripts/run_traces.sh` runs all traces and writes
`simulation/trace_results.csv`; `scripts/plot_results.py` draws `simulation/trace_results.png`.
AMAT = 4 + miss rate x 3 (read accesses only; hit = 4 cycles, miss = 7 cycles).

## 2. Results

| Trace | Requests | Reads | Writes | Read hits | Hit rate | AMAT (cycles) |
|---|---:|---:|---:|---:|---:|---:|
| sequential | 64 | 64 | 0 | 48 | 75.0% | 4.75 |
| conflict | 40 | 40 | 0 | 0 | 0% | 7.00 |
| loop_1_5kb | 384 | 384 | 0 | 96 | 25.0% | 6.25 |
| random_1kb | 200 | 200 | 0 | 139 | 69.5% | 4.92 |
| random_4kb | 200 | 200 | 0 | 40 | 20.0% | 6.40 |
| mixed_rw | 200 | 123 | 77 | 40 | 32.5% | 6.02 |

## 3. Discussion
- **sequential:** 64 consecutive words. Each 16-byte block holds 4 words, so every block
  gives 1 miss and 3 hits: 16 misses, 48 hits. This is spatial locality.
- **conflict:** the two addresses 0x30 and 0x430 have the same index and different tags,
  so they evict each other: 0% hits.
- **loop_1_5kb:** a loop over 96 blocks (1.5 KB) in a cache of 64 lines. Blocks 0-31 and
  64-95 share lines and evict each other, only blocks 32-63 stay in the cache. This gives
  32 hits per pass for the last 3 passes: 96 hits out of 384 (25%). The array is bigger than the
  cache, so these are capacity and conflict misses.
- **random_1kb:** the 1 KB address range has exactly 64 blocks, one per cache line, so there are
  no conflicts. The only misses are the first access to each block: 61 different
  blocks were touched in 200 reads, so 61 misses and 139 hits (69.5%).
- **random_4kb:** the range is 4 times the cache size, 4 blocks compete for each line, so the hit
  rate falls to 20%.
- **mixed_rw:** 77 of the 200 requests are writes. Writes do not allocate a block, so only the
  123 reads are counted: 40 hits (32.5%).

## 4. Conclusion
The hit rate depends strongly on the access pattern: spatial locality and a working set
that fits into the cache give high hit rates, while a working set larger than the cache or
addresses with the same index give low hit rates.
