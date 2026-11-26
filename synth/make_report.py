#!/usr/bin/env python3
# Run from the repository root (after bash synth/run_synth.sh):
#     python3 synth/make_report.py
# Reads synth/out/yosys_stat_per_module.txt and synth/out/nextpnr.log and writes
# documentation/synthesis_report.md with the numbers of YOUR run.
import re, sys

def read(path):
    try:
        return open(path).read()
    except FileNotFoundError:
        sys.exit("ERROR: %s not found. Run 'bash synth/run_synth.sh' first." % path)

stat = read("synth/out/yosys_stat_per_module.txt")
pnr = read("synth/out/nextpnr.log")

def parse_block(block):
    # Supports both Yosys formats: "<count> <name>" (new) and "<name> <count>" (old).
    def count(name):
        m = re.search(r"^\s*(\d+)\s+" + name + r"\s*$", block, flags=re.M)
        if m:
            return int(m.group(1))
        m = re.search(r"^\s*" + name + r"\s+(\d+)\s*$", block, flags=re.M)
        return int(m.group(1)) if m else 0
    cells = re.search(r"^\s*(\d+)\s+cells\s*$", block, flags=re.M) or \
            re.search(r"Number of cells:\s+(\d+)", block)
    ff = 0
    for m in re.finditer(r"^\s*(\d+)\s+(SB_DFF\w*)\s*$", block, flags=re.M):
        ff += int(m.group(1))
    for m in re.finditer(r"^\s*(SB_DFF\w*)\s+(\d+)\s*$", block, flags=re.M):
        ff += int(m.group(2))
    return (int(cells.group(1)) if cells else 0,
            count("SB_LUT4"), ff, count("SB_RAM40_4K"))

parts = re.split(r"^=== (.+?) ===\s*$", stat, flags=re.M)
modules, total = {}, None
for i in range(1, len(parts), 2):
    name, block = parts[i], parts[i + 1]
    if name == "design hierarchy":
        total = parse_block(block)
    else:
        modules[name] = parse_block(block)
if total is None or not modules:
    sys.exit("ERROR: could not read the Yosys statistics file.")

order = [("address_decoder", "address_decoder"),
         ("tag_comparator", "tag_comparator"),
         ("cache_controller", "cache_controller"),
         ("cache_tag_ram", "cache_tag_ram"),
         ("cache_valid_ram", "cache_valid_ram"),
         ("cache_data_ram", "cache_data_ram"),
         ("main_memory", "main_memory (model)"),
         ("cache_top", "cache_top (data multiplexer)")]
rows = ""
for key, label in order:
    c, l, f, r = modules.get(key, (0, 0, 0, 0))
    rows += "| %s | %d | %d | %d | %d |\n" % (label, c, l, f, r)
rows += "| **Total** | %d | %d | %d | %d |\n" % total

lc = re.search(r"ICESTORM_LC:\s+(\d+)/\s*(\d+)\s+(\d+)%", pnr)
rm = re.search(r"ICESTORM_RAM:\s+(\d+)/\s*(\d+)\s+(\d+)%", pnr)
fm = re.findall(r"Max frequency for clock '[^']*':\s+([\d.]+) MHz", pnr)
if not (lc and rm and fm):
    sys.exit("ERROR: could not read nextpnr results. Open synth/out/nextpnr.log and check for errors.")

report = f"""# Synthesis Report

## 1. Flow
- Target: Lattice iCE40 HX8K FPGA (open-source flow: Yosys for synthesis, nextpnr for
  place and route and timing).
- `synth/run_synth.sh` runs everything; raw results are in `synth/out/`.
- Reason for the wrapper: `cache_top` has 294 I/O pins (164 inputs, 130 outputs; two 128-bit
  buses), but the FPGA package has only 206 user I/O pins. So `synth/synth_wrapper.v` feeds the
  cache from a shift register and reduces its output to one bit. It is used only for timing.

## 2. Resource utilization per module (Yosys)

| Module | Cells | LUT4 | Flip-flops | Block RAM (4 Kbit) |
|---|---:|---:|---:|---:|
{rows}
## 3. After place and route (nextpnr, iCE40 HX8K)
- Logic cells used: {lc.group(1)} / {lc.group(2)} ({lc.group(3)} %). This is the whole timing design:
  cache, main-memory model and the timing wrapper (shift register and output registers).
- Block RAM used: {rm.group(1)} / {rm.group(2)} ({rm.group(3)} %)
- Maximum clock frequency: {fm[-1]} MHz (final value, after routing)

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
"""
open("documentation/synthesis_report.md", "w").write(report)
print("Written: documentation/synthesis_report.md")
print()
print(rows)
print("Logic cells: %s/%s (%s%%)   Block RAM: %s/%s (%s%%)   Max frequency: %s MHz" %
      (lc.group(1), lc.group(2), lc.group(3), rm.group(1), rm.group(2), rm.group(3), fm[-1]))
