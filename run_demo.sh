#!/bin/bash
# Demo for presentation: console log + VCD waveforms + pictures.   usage: ./run_demo.sh [SW 0..7]
SW=${1:-0}
python3 python/prep_sim.py 36000 > /dev/null
python3 python/make_demo_data.py
iverilog -g2012 -Wall -c files_demo.f -s tb_demo -o sim/demo.vvp
vvp sim/demo.vvp +SW=$SW +VCD=sim/demo_overview.vcd | tee results/demo_console.txt
vvp sim/demo.vvp +SW=$SW +VCD=sim/demo_zoom.vcd +ZOOM=1264 | tail -1
python3 python/vcd_plot.py
echo "Open the waveform with:  gtkwave sim/demo_overview.vcd"
