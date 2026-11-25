# ECG QRS Detector — Icarus Verilog simulation (DE1-SoC project)

Noise-robust, resource-efficient ECG QRS detection. This folder contains the synthesizable Verilog (baseline version),
the testbench, and a Python golden model that proves the Verilog is bit-exact.

## 1. Software requirements
| Software | Version tested | Needed for |
|---|---|---|
| Icarus Verilog (`iverilog`, `vvp`) | 12.0 (11+ is fine) | compile + run the simulation |
| GTKWave (optional) | any | view waveforms (`+VCD` option) |
| Python 3 | 3.9+ | data preparation, golden model, scoring, plots |
| Python packages | numpy, scipy, matplotlib, wfdb | `pip install numpy scipy matplotlib wfdb` |
| VS Code (or any editor) | any | edit Verilog / Python |
| Quartus Prime Lite + Cyclone V support | 18.1–23.1 | LATER: synthesis, pin assignment, board programming, resource reports |
Windows: add the Icarus `bin` folder to PATH, reopen the terminal, then check `iverilog -V`, `vvp -V`, `python --version`.

## 2. Hardware requirements
* **For this simulation: only a laptop** (any CPU, 4 GB RAM; 100 s of ECG takes ~40 s to simulate). No board needed.
* **For the board stage (later):** Terasic DE1-SoC (Cyclone V 5CSEMA5F31C6), 5 V power adapter, USB cable to the
  USB-Blaster port, laptop with Quartus + USB-Blaster driver. A live ECG sensor (e.g. AD8232 front end with isolation)
  is an optional extension — not needed for the first demo.

## 3. Folder layout
```
rtl/        Verilog design (one module per block of the block diagram)
tb/         tb_ecg_qrs.v  testbench
python/     prep_sim.py (data + FIR coefficients), golden.py (bit-exact model), compare.py, sweep_report.py, plot_stages.py, noise.py
data/       MIT-BIH record 100 (.dat .hea .atr) + reference beats
sim/        generated ROM files (ecg.hex, noise.hex) and compiled simulation
results/    simulation logs per noise level (k0..k7), figures
files.f     file list for iverilog        run_sim.sh / run_sim.bat   one-command run
```

## 4. Run it
Linux/macOS/WSL: `./run_sim.sh` (clean ECG, 100 s)   or   `./run_sim.sh 36000 4` (noise level k=4)
Windows: edit N and K in `run_sim.bat`, double-click it.
Manual steps:
```
python3 python/prep_sim.py 36000                      # makes sim/ecg.hex, sim/noise.hex, rtl/fir_coeffs.vh
iverilog -g2012 -Wall -P tb_ecg_qrs.N_SAMPLES=36000 -c files.f -s tb_ecg_qrs -o sim/ecg_sim.vvp
vvp sim/ecg_sim.vvp +SW=0 +OUT=results/k0             # +SW = noise level 0..7 ; add +VCD for a waveform file
python3 python/compare.py results/k0 0                # RTL vs golden model + accuracy vs annotations
gtkwave sim/ecg_qrs.vcd                               # only if you ran with +VCD
```
Important: the number N must be the same in `prep_sim.py` and `-P tb_ecg_qrs.N_SAMPLES`.

## 5. Module map (same names as the block diagram)
| Verilog module | Block | What it does |
|---|---|---|
| sample_source | Sample controller + ECG ROM + Noise ROM | releases 1 sample every SAMPLE_DIV clocks (board: 138889 = 50 MHz/360 Hz; simulation: 200) |
| noise_injector | Noise injector (1) | y = ecg + (noise x k)/8, k = SW[2:0] |
| baseline_remove | Noise filtering (part 1) | IIR baseline estimate (~0.45 Hz) subtracted |
| fir_bp | Noise filtering (part 2) | 41-tap FIR band-pass 5–20 Hz (fully parallel baseline) |
| derivative, squarer | Feature enhancer | 5-point derivative, then square |
| mwi | Window integrator | 54-sample (150 ms) running sum |
| qrs_decision | Peak detector, Adaptive threshold, Decision logic | SPKI/NPKI threshold, 200 ms refractory, T-wave check, search-back |
| rpeak_locator | R-peak localisation (4) | scans buffered ECG [p-64, p-4] for the true R-peak |
| rr_bpm, seq_div | RR interval and BPM | RR = difference of R positions, BPM = 21600 / RR (hardware divider) |
| ecg_qrs_top | top level | connects everything. Ports: inputs clk, rst, sw[2:0]; outputs done, rpeak_valid, rpeak_idx, rr_samples, bpm, bpm_valid. Stage signals and cycle counters are internal (the testbench reads them as dut.x_v, dut.cyc_pipe_max, ...) |

## 6. Results of the supplied run (MIT-BIH record 100, first 100 s, first 3 s excluded from scoring)
RTL output is bit-identical to the Python model at every stage for all 8 noise levels.
| k | SNR (dB) | beats | TP | FP | FN | Sensitivity % | PPV % | F1 % | R-peak error (ms) |
|---|---|---|---|---|---|---|---|---|---|
| 0 | clean | 120 | 119 | 0 | 0 | 100.00 | 100.00 | 100.00 | 1.1 |
| 1 | 12.0 | 120 | 119 | 0 | 0 | 100.00 | 100.00 | 100.00 | 1.2 |
| 2 | 6.0 | 121 | 119 | 1 | 0 | 100.00 | 99.17 | 99.58 | 1.4 |
| 3 | 2.5 | 124 | 119 | 4 | 0 | 100.00 | 96.75 | 98.35 | 1.8 |
| 4 | 0.0 | 128 | 119 | 8 | 0 | 100.00 | 93.70 | 96.75 | 2.9 |
| 5 | -1.9 | 131 | 119 | 11 | 0 | 100.00 | 91.54 | 95.58 | 4.0 |
Noise here is synthetic (baseline wander + muscle + electrode motion), not the PhysioNet NST files, and only one record is used.
Treat these as simulation results, not final claims.

## 7. Known limitations / next work
* Baseline design only: the FIR is fully parallel (41 multipliers) and computed in one clock — expect Quartus timing/DSP
  results to need pipelining or a shared multiplier (that is the "optimised" version for the resource comparison).
* The separate noise-level estimator (contribution 2) is not added yet; the threshold currently adapts through SPKI/NPKI only.
  False detections at low SNR (electrode-motion bursts) are what it should reduce.
* Only record 100 tested; run more MIT-BIH records and the real NST files before reporting accuracy.
* Search-back uses 1.75 x average RR; T-wave check is a simple amplitude rule.

## 8. Presentation demo (waveforms like the counter project)
```
Windows : run_demo.bat            (edit SW in the file: 0 = clean ... 7 = very noisy)
Linux   : ./run_demo.sh [SW]
```
It compiles `tb/tb_demo.v`, prints every detected heartbeat on the console, writes `sim/demo_overview.vcd` (10 s of ECG) and
`sim/demo_zoom.vcd` (450 clock cycles around one heartbeat, clock visible), and draws GTKWave-style pictures in `results/`.
Open the waveform yourself:  `gtkwave sim/demo_overview.vcd` -> drag signals into the list -> right-click `ecg_in`, `filtered`,
`envelope` -> Data Format -> Signed Decimal -> Analog -> Interpolated.
Manual commands: `iverilog -g2012 -c files_demo.f -s tb_demo -o sim/demo.vvp` then `vvp sim/demo.vvp +SW=0 +VCD=sim/demo_overview.vcd`
(zoom file: add `+ZOOM=1264`).

## 9. Member B: baseline vs optimised RTL
All widths are now parameters of `ecg_qrs_top`; the defaults give the BASELINE, the values below give the OPTIMISED design:
| Parameter | Baseline | Optimised | Meaning |
|---|---|---|---|
| DW / BLW | 16 / 24 | 12 / 20 | data width / baseline register width |
| SEQ / ACCW | 0 / 48 | 1 / 32 | FIR: 41 parallel multipliers vs ONE shared multiplier (one tap per clock) |
| SQSH / SQW | 0 / 32 | 4 / 18 | right shift after squaring / squared-value width |
| EW | 40 | 24 | moving-sum and threshold width |
Run both and compare with the Python model:  `./run_opt.sh 7200 4`  (or `run_opt.bat`; arguments = samples, noise level).
`results/opt_vs_base.txt` has the detection comparison and the storage counted from the RTL (these are NOT Quartus numbers).
Internal cycle counters (simulation only, not built in hardware) `cyc_pipe_max` and `cyc_beat_max` (printed by the testbench as CYCLES) show the real-time margin:
the worst case is 97 clock cycles per sample, against 138,889 available on the board.
Known limits: the optimised design is not identical to the baseline under heavy noise (R-peak error up to about 1 ms larger);
the 1024-sample R-peak buffer is now the largest memory and is the next thing to shrink.

## 10. Quartus
The `quartus_project` folder is ready for Quartus (top level `de1soc_top`, set `OPT` to 0 for the baseline or 1 for the optimised design).
Follow `quartus_project/README_quartus.md`. It has not been run in Quartus yet.

## 8. Board build (DE1-SoC)
`quartus_project/` holds the Quartus Prime Lite 22.1 project (device 5CSEMA5F31C6). Top module `de1soc_top`: inputs CLOCK_50, KEY[0] (reset), SW[2:0] (noise level); outputs LEDR[9:0] (beat flash, done, switch echo) and HEX0..HEX5 (BPM digits). All 57 pins are assigned in `de1soc_top.qsf`; see `docs/ECG_QRS_All_Pins.pdf`.
Compile result: 8,440 ALMs (26%), 3 DSP blocks, Fmax 61.62 MHz, setup slack +2.653 ns.

## 9. Multi-record test (48 MIT-BIH records, first 100 s, bit-accurate Python model)
| | Clean | Noise level 4 (about 0 dB) |
|---|---|---|
| Sensitivity (gross) | 99.78 % | 99.37 % |
| PPV (gross) | 95.53 % | 88.41 % |
Weak records: 104, 108, 114, 207 (paced beats / unusual leads). Noise is synthetic, not the PhysioNet NST files. Run `python python/multi_record_test.py` after placing records under `data/mitdb/` (from https://physionet.org/content/mitdb/1.0.0/).
