@echo off
rem usage: run_sim.bat   (edit N and K below)
set N=36000
set K=0
python python\prep_sim.py %N%
iverilog -g2012 -Wall -P tb_ecg_qrs.N_SAMPLES=%N% -c files.f -s tb_ecg_qrs -o sim\ecg_sim.vvp
if not exist results\k%K% mkdir results\k%K%
vvp sim\ecg_sim.vvp +SW=%K% +OUT=results/k%K%
python python\compare.py results/k%K% %K%
pause
