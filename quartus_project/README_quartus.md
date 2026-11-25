# Putting the ECG detector into Quartus (DE1-SoC)

This folder is flat on purpose: every Verilog file, the include file and the ECG memory files are in one place.
I could not run Quartus myself, so this folder is untested in Quartus. The Verilog itself is checked in simulation.

## What is in the folder
| File | What it is |
|---|---|
| de1soc_top.v | **Top level for the board** (switches, LEDs, 7-segment display). Set `OPT` to 0 or 1 at the top |
| ecg_qrs_top.v and the other .v files | The detector (same code as the `rtl` folder) |
| fir_coeffs.vh | Filter coefficients (included by fir_bp.v) |
| ecg.hex, noise.hex | The ECG and noise samples stored in on-chip memory (36000 samples = 100 s) |
| ecg_qrs.sdc | The 50 MHz clock constraint for the timing report |

## Step 1: make the project
1. Install Quartus Prime Lite with **Cyclone V** device support.
2. **File, New Project Wizard.** Folder: this `quartus_project` folder. Project name and top-level entity: **de1soc_top**.
3. **Add files:** select all `.v` files, `fir_coeffs.vh` and `ecg_qrs.sdc`. (The .hex files only need to be in the folder.)
4. **Device:** family Cyclone V, device **5CSEMA5F31C6** (the DE1-SoC chip; confirm in the Terasic manual for your board revision).
5. Finish.

## Step 2: compile (no board needed)
**Processing, Start Compilation.** Pins do not have to be assigned yet; this is enough for the size and speed numbers.

## Step 3: read the numbers
- **Compilation Report, Flow Summary:** Logic utilization (in ALMs), Total registers, Total block memory bits, Total DSP Blocks.
- **Timing Analyzer, Fmax Summary:** the Fmax for CLOCK_50 and the setup slack.
Fill this table for both versions:

| | Baseline (OPT = 0) | Optimised (OPT = 1) |
|---|---|---|
| Logic utilization (ALMs) | | |
| Total registers | | |
| Total block memory bits | | |
| Total DSP blocks | | |
| Fmax (MHz) | | |
| Setup slack at 50 MHz (ns) | | |

## Step 4: the optimised version
Open `de1soc_top.v`, change `parameter OPT = 0` to `1`, save, and compile again. Keep the first report (screenshot or save a copy of the output folder) before you recompile. Both versions use the same ECG memory, so the comparison is fair; the block memory bits include the two ECG ROMs (about 864 kbit) in both.

## What to expect
- **Warnings are normal.** Look at errors only.
- The baseline has 41 multipliers working in one clock, so it may **fail timing at 50 MHz**. That is a result, not a mistake; report it.
- The R-peak buffer (1024 samples) is read in a way that may make Quartus use logic instead of memory blocks. If the ALM count looks very large, send me the report and I will change the buffer.
- If Quartus complains about a file or include, check that all files are in this folder and added to the project.

## Step 5: the board (later)
1. **Pins:** import the **official Terasic DE1-SoC pin assignment file** (the .qsf from the DE1-SoC CD or Terasic website): Assignments, Import Assignments. The port names here (CLOCK_50, KEY, SW, LEDR, HEX0 to HEX5) match Terasic's names. Do not type pins by hand.
2. Compile again, then **Tools, Programmer**: hardware USB-Blaster, add the `.sof` file in `output_files`, Start.
3. On the board: **KEY0** restarts, **SW[2:0]** sets the noise (0 = clean), **LEDR9** flashes on each heartbeat, **HEX2..HEX0** show the heart rate, **LEDR8** lights when the 100 s recording ends (it restarts by itself after about 1 second).

## What to send me
Screenshots of the Flow Summary and the Fmax Summary for OPT = 0 and OPT = 1, plus any error message in full.

## Port list (Nov 2026 update)
`ecg_qrs_top` now exposes only the main ports: inputs `clk, rst, sw[2:0]`; outputs `done, rpeak_valid, rpeak_idx, rr_samples, bpm, bpm_valid`.
The real-time counters and the debug taps are internal (simulation only). Recompile after replacing `ecg_qrs_top.v` and `de1soc_top.v`.
