# Member B summary: RTL and verification

## Built
- Width-parameterised Verilog (every stage), baseline defaults unchanged
- Optimised design: 12-bit data, ONE shared multiplier for the 41-tap FIR, 18-bit squared values, 24-bit envelope
- Cycle counters (real-time margin) in the top level and printed by the testbench
- Python model extended to the same widths; `compare.py` checks every stage bit for bit

## Verified (Icarus Verilog vs Python model)
| Design | Run | Result |
|---|---|---|
| Baseline | 7200 samples, k=0 and k=4 | bit-exact at every stage |
| Optimised | 7200 samples, k=0 and k=4 | bit-exact at every stage |
| Optimised | 36000 samples (100 s), k=0 and k=5 | bit-exact at every stage |

## Baseline vs optimised (record 100, 100 s, synthetic noise)
- Clean ECG: 119/119 beats, 0 false, 1.1 ms R-peak error, identical for both
- Noise: no missed beats at any level for either design; false beats the same or one fewer; R-peak error up to about 1 ms larger in the optimised design under heavy noise
- Register and memory bits counted from the RTL: 19251 to 14071 (27% less); multipliers 41 to 1
- Cycles per sample: 6 (baseline) vs 48 (optimised); beat to BPM 97; board allows 138889

## Not yet measured
- Quartus ALMs, registers, DSP blocks, Fmax and power (needs Member C's compile)
- Other MIT-BIH records and the real Noise Stress Test files (needs Member A)

## Next
1. Send the two top-level configurations to Member C for the Quartus comparison
2. Shrink the 1024-sample R-peak buffer (now the largest memory)
3. Re-check the widths on Member A's extra records
