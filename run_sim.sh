#!/bin/bash
# usage: ./run_sim.sh [N_SAMPLES] [K]    default: 36000 samples (100 s), K=0 (clean)
N=${1:-36000}; K=${2:-0}
python3 python/prep_sim.py $N
iverilog -g2012 -Wall -P tb_ecg_qrs.N_SAMPLES=$N -c files.f -s tb_ecg_qrs -o sim/ecg_sim.vvp
mkdir -p results/k$K
vvp sim/ecg_sim.vvp +SW=$K +OUT=results/k$K
python3 python/compare.py results/k$K $K
