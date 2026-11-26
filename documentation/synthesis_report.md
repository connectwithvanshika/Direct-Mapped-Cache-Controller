# Synthesis Report

## 1. Flow
- Target: Lattice iCE40 HX8K FPGA (open-source flow: Yosys for synthesis, nextpnr for
  place and route and timing).
- `synth/run_synth.sh` runs everything; raw results are in `synth/out/`.
- Reason for the wrapper: `cache_top` has more than 300 I/O pins (two 128-bit buses),
  so `synth/synth_wrapper.v` puts registers around the cache. It is used only for timing.

## 2. Resource utilization per module (Yosys)

| Module | Cells | LUT4 | Flip-flops | Block RAM (4 Kbit) |
|---|---:|---:|---:|---:|
| address_decoder | 0 | 0 | 0 | 0 |
| tag_comparator | 30 | 30 | 0 | 0 |
| cache_controller | 24 | 12 | 12 | 0 |
| cache_tag_ram | 84 | 30 | 52 | 2 |
| cache_valid_ram | 215 | 150 | 65 | 0 |
| cache_data_ram | 266 | 129 | 129 | 8 |
| main_memory (model) | 444 | 153 | 277 | 8 |
| cache_top (data multiplexer) | 128 | 128 | 0 | 0 |
| **Total** | 1191 | 632 | 535 | 18 |

## 3. After place and route (nextpnr, iCE40 HX8K)
- Logic cells used: 898 / 7680 (11 %)
- Block RAM used: 18 / 32 (56 %)
- Maximum clock frequency: 134.59 MHz (final value, after routing)

## 4. Observations
- The 2:1 multiplexer in `cache_top` (refill data or CPU write data) needs one LUT per
  data bit, 128 LUTs.
- The data RAM and the tag RAM are mapped to block RAM. The valid bits are kept in
  flip-flops, because all of them must be cleared at reset.
- The main memory is a simulation model. In a real system it would be an external memory.
  Its cells are not part of the cache itself.
- The tag comparator is small: 22 equality tests plus the valid bit.

## 5. Limitation
The numbers belong to the iCE40 FPGA family and to these tool versions. Other FPGAs or
Vivado would give different values. The frequency is measured with registered inputs
and outputs (wrapper).
