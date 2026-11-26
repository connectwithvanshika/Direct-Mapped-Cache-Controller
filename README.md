# Direct-Mapped Cache Controller (Verilog HDL)

**Modern Computer Architecture | B.Tech (CS&AI) | Rishihood University**
**Project 6 | Phase I and Phase II submission**

A Verilog implementation of a 1 KB direct-mapped cache controller with a main-memory model, a self-checking testbench, simulation results and an IEEE project report. Phase II adds a valid-bit reset, a trace-driven performance study, a cache versus no-cache comparison and FPGA synthesis results (898 logic cells, 18 block RAMs, 134.59 MHz on an iCE40 HX8K).

## Phase I deliverables

| Deliverable | Location |
|---|---|
| IEEE project report | [IEEE Project Report](./report/Cache_Controller_IEEE_Report.pdf) |
| Prototype demo video (under 5 minutes) |https://drive.google.com/file/d/10uqqdOOXCRrFWfJ8nc2S0BqfsuwE8R15/view?usp=sharing|
| Verilog implementation | [rtl/](rtl/) |
| Testbenches | [testbench/](testbench/) |
| Diagrams and documentation | [documentation/](documentation/) |
| Simulation outputs and waveform | [simulation/](simulation/) |

## Phase II deliverables

| Deliverable | Location |
|---|---|
| Valid-bit reset (RTL and test) | [rtl/cache_valid_ram.v](rtl/cache_valid_ram.v), [testbench/tb_valid_reset.v](testbench/tb_valid_reset.v) |
| Six memory-access traces and trace-driven study | [traces/](traces/), [documentation/trace_analysis.md](documentation/trace_analysis.md) |
| Cache versus no-cache baseline | [rtl/nocache_top.v](rtl/nocache_top.v), [documentation/baseline_comparison.md](documentation/baseline_comparison.md) |
| FPGA synthesis and timing | [synth/](synth/), [documentation/synthesis_report.md](documentation/synthesis_report.md) |
| Final IEEE project report (Phase II) | submitted separately |

## Team

| Member | Enrollment No. | GitHub | Main work |
|---|---|---|---|
| Riya Garg | 2401010389 | riyaseema80 | Phase I: base RTL design and integration, cache controller FSM, base testbench, FSM and block diagrams, report, repository. Phase II: valid-bit reset (RTL, top-level connection, testbench) |
| Vanshika Yadav | 2401010496 | Sung Jin-woo | Phase I: 1 KB random trace, comparator fault-injection test, simulation output, results analysis. Phase II: trace generator, trace-driven testbench, automated runner, six traces, plotting script, trace analysis |
| Nitanshu Goyal | 2401010304 | Nitanshu12 | Phase I: unit testbenches for address decoder, tag comparator, tag and valid RAMs; datapath notes. Phase II: FPGA synthesis flow (Yosys and nextpnr), resource and timing report |
| Krish Garg | 2401020097 | Krish Garg | Phase I: unit testbenches for data RAM and main memory; memory read-latency parameter and experiment. Phase II: no-cache baseline design, comparison testbench, baseline analysis |
| Mishti Sharma | 2401010278 | mishti | Phase I: corner-case testbench, cache parameter analysis, references check. Phase II: interview-preparation documentation (not yet in the repository) |

The commit history of every member is visible under *Insights > Contributors* or with `git shortlog -sne`.

## Project overview

A cache is a small and fast memory between the processor and main memory. It keeps recently used blocks so that most accesses do not have to wait for the slow main memory. This project implements a **direct-mapped** cache: every memory block can be stored in exactly one cache line, so a lookup needs only one tag comparison.

The controller handles:

- cache lookup with hit and miss detection
- read miss: block refill from main memory
- write hit: write-through (cache and main memory are updated)
- write miss: no-write-allocate (only main memory is updated)

## Cache configuration

| Parameter | Value |
|---|---|
| Cache size | 1 KB |
| Block size | 16 bytes (128 bits) |
| Number of blocks | 64 |
| Address width | 32 bits |
| Tag / index / offset | 22 / 6 / 4 bits |
| Address split | tag = address[31:10], index = address[9:4], offset = address[3:0] |
| Mapping | direct mapped |
| Write policy | write-through, no-write-allocate |
| Main memory model | 256 blocks of 128 bits (4 KB) |

Example: address `0x00000410` gives tag 1, index 1, offset 0. Address `0x00000010` has the same index but tag 0, so the two addresses conflict.

## Architecture

![Block diagram](documentation/block_diagram.png)

| Module | File | Function |
|---|---|---|
| `cache_top` | `rtl/cache_top.v` | Connects all modules; 2:1 multiplexer for the data written to the cache |
| `address_decoder` | `rtl/address_decoder.v` | Splits the address into tag, index and offset |
| `cache_tag_ram` | `rtl/cache_tag_ram.v` | Stores the 22-bit tag of each of the 64 lines |
| `cache_valid_ram` | `rtl/cache_valid_ram.v` | Stores one valid bit per line |
| `cache_data_ram` | `rtl/cache_data_ram.v` | Stores the 128-bit data block of each line |
| `tag_comparator` | `rtl/tag_comparator.v` | `hit` = tags equal AND valid bit set |
| `cache_controller` | `rtl/cache_controller.v` | 12-state FSM that controls the cache and the memory |
| `main_memory` | `rtl/main_memory.v` | Main memory model with `mem_ready` handshake and read-latency parameter |

The RAMs register their read data, so the data for a new index appears one clock cycle later. The controller waits for this in its LOOKUP state.

## Controller FSM

![FSM diagram](documentation/fsm_diagram.png)

| Code | State | Description | Outputs |
|---|---|---|---|
| 0 | IDLE | waits for `cpu_req` | |
| 1 | LOOKUP | RAMs read with the new index | |
| 2 | CHECK | `cache_hit` selects the path | |
| 3 | HIT | hit; a write updates cache and memory | `cache_data_we`, `mem_write_en` (write hit) |
| 4 | MISS | starts the memory read | `cache_miss`, `mem_read_en` |
| 5 | WAIT_MEM | waits for `mem_ready` | `cache_miss` |
| 6 | REFILL | data, tag and valid bit written together | `cache_data_we`, `cache_tag_we`, `cache_valid_we` |
| 7 | RELOAD | one cycle for the new data to reach the RAM output | |
| 8 | COMPLETE | read miss finished | `cpu_ready` |
| 9 | WRITE_WAIT | write miss: write to main memory | `mem_write_en`, `cache_miss` |
| 10 (a) | WRITE_DONE | write miss finished | `cpu_ready` |
| 11 (b) | HIT_DONE | hit finished | `cpu_ready` |

| Access | State path | Latency |
|---|---|---|
| Read hit | IDLE, LOOKUP, CHECK, HIT, HIT_DONE | 4 cycles |
| Read miss | IDLE, LOOKUP, CHECK, MISS, WAIT_MEM, REFILL, RELOAD, COMPLETE | 7 cycles |
| Write hit | same path as read hit | 4 cycles |
| Write miss | IDLE, LOOKUP, CHECK, WRITE_WAIT, WRITE_DONE | 4 cycles |

The outputs depend only on the current state (Moore machine).

## Waveform

![Waveform](simulation/waveform_miss_hit_writemiss.png)

State values are hexadecimal. The waveform shows a read miss at `0x10` (7 cycles), a read hit at `0x10` (4 cycles) and a write miss at `0x20` (4 cycles).

## Repository structure

```
.
├── rtl/
│   ├── address_decoder.v
│   ├── cache_controller.v
│   ├── cache_data_ram.v
│   ├── cache_tag_ram.v
│   ├── cache_top.v
│   ├── cache_valid_ram.v
│   ├── main_memory.v
│   ├── nocache_top.v            baseline without cache (Phase II)
│   └── tag_comparator.v
├── testbench/
│   ├── cache_tb.v               main self-checking testbench (reference model, 4 traces)
│   ├── tb_corner_cases.v        corner-case tests
│   ├── tb_address_decoder.v     unit test
│   ├── tb_tag_comparator.v      unit test
│   ├── tb_tag_valid_ram.v       unit test
│   ├── tb_data_ram.v            unit test
│   ├── tb_main_memory.v         unit test
│   ├── tb_valid_reset.v         valid-bit reset test (Phase II)
│   ├── tb_trace.v               trace-driven testbench (Phase II)
│   └── tb_compare.v             cache versus no-cache (Phase II)
├── traces/                      six trace files (Phase II)
├── scripts/                     gen_traces.py, run_traces.sh, plot_results.py (Phase II)
├── synth/                       run_synth.sh, make_report.py, synth_wrapper.v, out/ (Phase II)
├── simulation/
│   ├── waveform_miss_hit_writemiss.png
│   ├── sim_output.txt
│   ├── mutation_test_output.txt
│   ├── latency_L1.txt, latency_L2.txt, latency_L4.txt, latency_L8.txt
│   ├── compare_L*.txt, trace_results.csv, trace_results.png   (Phase II)
├── documentation/
│   ├── block_diagram.png
│   ├── fsm_diagram.png
│   ├── results.md
│   ├── parameters.md
│   ├── datapath_notes.md
│   ├── latency_experiment.md
│   ├── references_check.md
│   ├── trace_analysis.md        (Phase II)
│   ├── baseline_comparison.md   (Phase II)
│   └── synthesis_report.md      (Phase II)
└── report/
    └── Cache_Controller_IEEE_Report.pdf   (Phase I)
```

## How to run

**Requirements:** Icarus Verilog (`iverilog`, `vvp`).
macOS: `brew install icarus-verilog`. Ubuntu: `sudo apt install iverilog`.

```
git clone https://github.com/riyaseema80/Direct-Mapped-Cache-Controller.git
cd Direct-Mapped-Cache-Controller
```

**Main testbench** (also writes `cache_wave.vcd`):
```
iverilog -o sim rtl/*.v testbench/cache_tb.v
vvp sim
```
Expected last lines: `Checks passed = 103, failed = 0` and `ALL CHECKS PASSED`.

**Corner-case tests:**
```
iverilog -o sim rtl/*.v testbench/tb_corner_cases.v
vvp sim
```
Expected: `Checks passed = 31, failed = 0`.

**Unit tests:**
```
iverilog -o sim rtl/address_decoder.v testbench/tb_address_decoder.v && vvp sim
iverilog -o sim rtl/tag_comparator.v testbench/tb_tag_comparator.v && vvp sim
iverilog -o sim rtl/cache_tag_ram.v rtl/cache_valid_ram.v testbench/tb_tag_valid_ram.v && vvp sim
iverilog -o sim rtl/cache_data_ram.v testbench/tb_data_ram.v && vvp sim
iverilog -o sim rtl/main_memory.v testbench/tb_main_memory.v && vvp sim
```

**Different main-memory read latency** (default is 1 cycle):
```
iverilog -DMEM_READ_LATENCY=4 -o sim rtl/*.v testbench/cache_tb.v
vvp sim
```

**Valid-bit reset test:**
```
iverilog -o sim rtl/*.v testbench/tb_valid_reset.v && vvp sim
```

**Trace-driven study** (generates the traces, runs all six, writes `simulation/trace_results.csv`):
```
bash scripts/run_traces.sh
python3 scripts/plot_results.py      # needs matplotlib: pip install matplotlib
```

**Cache versus no cache** (change the memory latency with `-DMEM_READ_LATENCY`):
```
iverilog -DMEM_READ_LATENCY=20 -o sim rtl/*.v testbench/tb_compare.v && vvp sim
```

**FPGA synthesis** (needs the OSS CAD Suite: `yosys` and `nextpnr-ice40`):
```
source /path/to/oss-cad-suite/environment
bash synth/run_synth.sh
python3 synth/make_report.py
```

**View the waveform:** open `cache_wave.vcd` with GTKWave or with the Surfer extension in VS Code. The files `sim` and `cache_wave.vcd` are created locally and are ignored by git.

## Verification

- **Reference model:** the testbench keeps a model of the valid bit and tag of every line. For each request it predicts hit or miss and compares it with the design. It also measures the latency of every request.
- **Test plan:** 9 directed tests, sequential trace (16 words), conflict trace (`0x30` and `0x430`, same index), random trace in 2 KB (20 accesses, about 25% writes) and random trace in 1 KB (50 reads). Random traces use a fixed seed.
- **Result:** 103 of 103 checks passed.
- **Fault injection:** when the comparison in `tag_comparator.v` was temporarily changed from `==` to `!=`, the testbench reported 47 failed checks out of 103 (see `simulation/mutation_test_output.txt`). The faulty code was not committed.
- **Corner cases:** first and last line, conflict on one index, write-through after eviction, write miss without allocation, all-ones tag and offsets inside one block: 31 of 31 checks passed.
- **Valid-bit reset (Phase II):** after a reset every line is empty again, so a block that was cached before the reset misses afterwards.
- **Unit tests:** address decoder, tag comparator, data RAM, tag and valid RAM, main memory: all passed.

## Results (directed testbench)

AMAT = hit time + miss rate x miss penalty = 4 + miss rate x 3 (read accesses only).

| Trace | Reads | Read hits | Hit rate | AMAT (cycles) |
|---|---:|---:|---:|---:|
| Directed tests | 7 | 3 | 42.9% | 5.71 |
| Sequential | 16 | 12 | 75.0% | 4.75 |
| Conflict | 6 | 0 | 0% | 7.00 |
| Random, 2 KB | 15 | 0 | 0% | 7.00 |
| Random, 1 KB | 50 | 25 | 50.0% | 5.50 |
| **Overall** | **94** | **40** | **42.6%** | **5.72** |

- A sequential access pattern benefits from spatial locality: one miss per 16-byte block, then three hits.
- The conflict trace shows the weakness of direct mapping: two addresses with the same index evict each other, so the hit rate is 0%.
- When the random addresses fit into 1 KB, blocks are reused and half of the reads hit.

More details: [documentation/results.md](documentation/results.md).

## Trace-driven study (Phase II)

Six longer traces were generated with `scripts/gen_traces.py` (fixed seed) and run with `testbench/tb_trace.v`. AMAT = 4 + miss rate x 3 (reads only).

| Trace | Reads | Writes | Read hits | Hit rate | AMAT (cycles) |
|---|---:|---:|---:|---:|---:|
| Sequential | 64 | 0 | 48 | 75.0% | 4.75 |
| Conflict | 40 | 0 | 0 | 0% | 7.00 |
| Loop over 1.5 KB | 384 | 0 | 96 | 25.0% | 6.25 |
| Random, 1 KB | 200 | 0 | 139 | 69.5% | 4.92 |
| Random, 4 KB | 200 | 0 | 40 | 20.0% | 6.40 |
| Mixed read/write | 123 | 77 | 40 | 32.5% | 6.02 |

The hit rate depends on the access pattern: spatial locality and a working set that fits into the cache give high hit rates; a working set larger than the cache, or addresses with the same index, give low hit rates. Details: [documentation/trace_analysis.md](documentation/trace_analysis.md). This is a different experiment from the directed testbench above, so the numbers are not meant to match.

## Memory latency experiment

The same testbench was run with a main-memory read latency of 1, 2, 4 and 8 cycles.

| Memory latency | Hit | Read miss | Read miss rate | AMAT |
|---:|---:|---:|---:|---:|
| 1 | 4 | 7 | 57.4% | 5.72 |
| 2 | 4 | 8 | 57.4% | 6.30 |
| 4 | 4 | 10 | 57.4% | 7.45 |
| 8 | 4 | 14 | 57.4% | 9.74 |

The miss rate does not change because the memory speed does not decide which accesses hit. The miss latency is 6 cycles plus the memory latency. Details: [documentation/latency_experiment.md](documentation/latency_experiment.md).

## Cache versus no cache (Phase II)

A baseline without cache (`rtl/nocache_top.v`) and the cache were given the same 72 reads (34 hits, 38 misses in the cache).

| Memory latency L | Cache cycles | No-cache cycles | Speed-up |
|---:|---:|---:|---:|
| 1 | 402 | 216 | 0.54 |
| 4 | 516 | 432 | 0.84 |
| 8 | 668 | 720 | 1.08 |
| 20 | 1124 | 1584 | 1.41 |
| 50 | 2264 | 3744 | 1.65 |

Cache total = 364 + 38 L cycles, no-cache total = 144 + 72 L cycles, so the two are equal at L = 220/34, about 6.5 cycles. For this workload the cache pays off only when main memory is slower than about 6.5 cycles. Details: [documentation/baseline_comparison.md](documentation/baseline_comparison.md).

## FPGA synthesis (Phase II)

Target: Lattice iCE40 HX8K, open-source flow (Yosys and nextpnr), 25 MHz target clock. A wrapper with registers around the cache is used for timing, because `cache_top` has more than 300 I/O pins.

| Module | Cells | LUT4 | Flip-flops | Block RAM |
|---|---:|---:|---:|---:|
| address_decoder | 0 | 0 | 0 | 0 |
| tag_comparator | 30 | 30 | 0 | 0 |
| cache_controller | 24 | 12 | 12 | 0 |
| cache_tag_ram | 84 | 30 | 52 | 2 |
| cache_valid_ram | 215 | 150 | 65 | 0 |
| cache_data_ram | 266 | 129 | 129 | 8 |
| cache_top (data multiplexer) | 128 | 128 | 0 | 0 |
| main_memory (simulation model) | 444 | 153 | 277 | 8 |
| **Total** | **1191** | **632** | **535** | **18** |

After place and route: **898 / 7680 logic cells (11%)**, **18 / 32 block RAMs (56%)**, estimated maximum frequency **134.59 MHz**. The main memory is a simulation model, so its cells are not part of the cache. The numbers belong to the iCE40 family and to these tool versions. Details: [documentation/synthesis_report.md](documentation/synthesis_report.md).

## Limitations

- The memory interface moves whole 128-bit blocks. The offset is decoded but is not used to select a word.
- The valid-bit memory is cleared at start-up and by the reset input (Phase II). The tag RAM and data RAM are not reset, which is safe because a line is used only when its valid bit is 1.
- The data RAM has no initial values, so a line that was never written returns unknown (`x`). The valid bit prevents the cache from using such a line.
- The main-memory model is simple (no refresh, no banks), so the miss penalty is small compared with a real DRAM.
- Synthesis was done with the open-source Yosys and nextpnr flow for an iCE40 FPGA, not with Vivado. The design was not run on a physical FPGA board.
- The 6.5-cycle break-even latency belongs to the 72-read workload (47% hit rate) used in the comparison.

## Future work

- More detailed main-memory model
- Two-way set-associative cache with LRU replacement
- Write-back policy with dirty bits
- Victim cache to reduce conflict misses
- Word-level access using the offset bits

## References

1. J. L. Hennessy and D. A. Patterson, *Computer Architecture: A Quantitative Approach*, 6th ed. Morgan Kaufmann, 2019.
2. D. A. Patterson and J. L. Hennessy, *Computer Organization and Design MIPS Edition: The Hardware/Software Interface*, 6th ed. Morgan Kaufmann, 2020.
3. D. M. Harris and S. L. Harris, *Digital Design and Computer Architecture*, 2nd ed. Morgan Kaufmann, 2012.
4. A. J. Smith, "Cache memories," *ACM Computing Surveys*, vol. 14, no. 3, pp. 473-530, Sep. 1982.
5. M. D. Hill, "A case for direct-mapped caches," *IEEE Computer*, vol. 21, no. 12, pp. 25-40, Dec. 1988.
6. N. P. Jouppi, "Improving direct-mapped cache performance by the addition of a small fully-associative cache and prefetch buffers," in *Proc. 17th Annual Int. Symp. on Computer Architecture (ISCA)*, Seattle, WA, USA, May 1990, pp. 364-373.
