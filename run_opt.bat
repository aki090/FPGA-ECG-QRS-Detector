@echo off
rem Baseline vs OPTIMISED RTL check. Edit N (samples) and K (noise level 0..7)
set N=7200
set K=0
python python\prep_sim.py 36000
python python\make_n_data.py %N%
if not exist results\base_k%K% mkdir results\base_k%K%
if not exist results\opt_k%K% mkdir results\opt_k%K%
echo === BASELINE (16-bit, 41 multipliers) ===
iverilog -g2012 -Wall -Ptb_ecg_qrs.N_SAMPLES=%N% -Ptb_ecg_qrs.ECG_FILE=\"sim/ecg_n.hex\" -Ptb_ecg_qrs.NOISE_FILE=\"sim/noise_n.hex\" -c files.f -s tb_ecg_qrs -o sim\base_n.vvp
vvp sim\base_n.vvp +SW=%K% +OUT=results/base_k%K%
python python\compare.py results/base_k%K% %K% 16 0 32 %N%
echo === OPTIMISED (12-bit, 1 shared multiplier) ===
iverilog -g2012 -Wall -Ptb_ecg_qrs.N_SAMPLES=%N% -Ptb_ecg_qrs.ECG_FILE=\"sim/ecg_n.hex\" -Ptb_ecg_qrs.NOISE_FILE=\"sim/noise_n.hex\" -Ptb_ecg_qrs.DW=12 -Ptb_ecg_qrs.BLW=20 -Ptb_ecg_qrs.SEQ=1 -Ptb_ecg_qrs.ACCW=32 -Ptb_ecg_qrs.SQSH=4 -Ptb_ecg_qrs.SQW=18 -Ptb_ecg_qrs.EW=24 -c files.f -s tb_ecg_qrs -o sim\opt_n.vvp
vvp sim\opt_n.vvp +SW=%K% +OUT=results/opt_k%K%
python python\compare.py results/opt_k%K% %K% 12 4 18 %N%
pause
