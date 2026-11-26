#!/bin/bash
# Run from the repository root:  bash synth/run_synth.sh
# Needs: yosys and nextpnr-ice40 (OSS CAD Suite or package manager)
set -e
mkdir -p synth/out

echo "=== 1. Resource count per module (Yosys, iCE40 target) ==="
yosys -q -p "read_verilog rtl/address_decoder.v rtl/tag_comparator.v rtl/cache_tag_ram.v rtl/cache_valid_ram.v rtl/cache_data_ram.v rtl/main_memory.v rtl/cache_controller.v rtl/cache_top.v; hierarchy -top cache_top; synth_ice40 -noflatten -top cache_top; tee -o synth/out/yosys_stat_per_module.txt stat"
grep -E "^=== |Number of cells|SB_LUT4|SB_DFF|SB_RAM40_4K|SB_CARRY" synth/out/yosys_stat_per_module.txt

echo
echo "=== 2. Place and route and maximum frequency (nextpnr, iCE40 HX8K) ==="
yosys -q -p "read_verilog rtl/address_decoder.v rtl/tag_comparator.v rtl/cache_tag_ram.v rtl/cache_valid_ram.v rtl/cache_data_ram.v rtl/main_memory.v rtl/cache_controller.v rtl/cache_top.v synth/synth_wrapper.v; hierarchy -top synth_wrapper; synth_ice40 -top synth_wrapper -json synth/out/wrapper.json"
nextpnr-ice40 --hx8k --package ct256 --json synth/out/wrapper.json --freq 25 --seed 1 > synth/out/nextpnr.log 2>&1 || true
grep -E "Max frequency for clock|ICESTORM_LC:|ICESTORM_RAM:|ICESTORM_DFF|ICESTORM_CARRY|ERROR" synth/out/nextpnr.log | tail -8
