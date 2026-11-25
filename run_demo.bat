@echo off
rem Demo for presentation. Edit SW (0..7 = noise level) below.
set SW=0
python python\prep_sim.py 36000
python python\make_demo_data.py
iverilog -g2012 -Wall -c files_demo.f -s tb_demo -o sim\demo.vvp
vvp sim\demo.vvp +SW=%SW% +VCD=sim/demo_overview.vcd
vvp sim\demo.vvp +SW=%SW% +VCD=sim/demo_zoom.vcd +ZOOM=1264
python python\vcd_plot.py
echo Open the waveform with:  gtkwave sim\demo_overview.vcd
gtkwave sim\demo_overview.vcd
pause
