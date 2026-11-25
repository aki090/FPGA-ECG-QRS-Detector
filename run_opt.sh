#!/bin/bash
# Baseline vs OPTIMISED RTL check.   usage: ./run_opt.sh [N_SAMPLES] [K]    default 7200 samples, K=0
N=${1:-7200}; K=${2:-0}
python3 python/prep_sim.py 36000 > /dev/null
python3 python/make_n_data.py $N
COMMON="-g2012 -Wall -Ptb_ecg_qrs.N_SAMPLES=$N -Ptb_ecg_qrs.ECG_FILE=\"sim/ecg_n.hex\" -Ptb_ecg_qrs.NOISE_FILE=\"sim/noise_n.hex\" -c files.f -s tb_ecg_qrs"
mkdir -p results/base_k$K results/opt_k$K
echo "=== BASELINE (16-bit, 41 multipliers) ==="
iverilog $COMMON -o sim/base_n.vvp && vvp sim/base_n.vvp +SW=$K +OUT=results/base_k$K | grep -E "finished|CYCLES"
python3 python/compare.py results/base_k$K $K 16 0 32 $N | grep -E "RESULT|Sensitivity"
echo "=== OPTIMISED (12-bit, 1 shared multiplier) ==="
iverilog $COMMON -Ptb_ecg_qrs.DW=12 -Ptb_ecg_qrs.BLW=20 -Ptb_ecg_qrs.SEQ=1 -Ptb_ecg_qrs.ACCW=32 -Ptb_ecg_qrs.SQSH=4 -Ptb_ecg_qrs.SQW=18 -Ptb_ecg_qrs.EW=24 -o sim/opt_n.vvp && vvp sim/opt_n.vvp +SW=$K +OUT=results/opt_k$K | grep -E "finished|CYCLES"
python3 python/compare.py results/opt_k$K $K 12 4 18 $N | grep -E "RESULT|Sensitivity"
