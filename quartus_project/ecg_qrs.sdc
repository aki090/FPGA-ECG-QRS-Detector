# 50 MHz board clock (20 ns). Add this file to the Quartus project so the timing report is meaningful.
create_clock -name CLOCK_50 -period 20.000 [get_ports {CLOCK_50}]
derive_pll_clocks
derive_clock_uncertainty
