`timescale 1ns/1ps
// Testbench: 50 MHz clock, runs the whole ECG ROM through the detector and logs every stage to text files.
//   plusargs:  +SW=<0..7> noise level   +OUT=<directory for log files>
module tb_ecg_qrs;
    parameter N_SAMPLES  = 36000;
    parameter SAMPLE_DIV = 200;
    parameter ECG_FILE   = "sim/ecg.hex";
    parameter NOISE_FILE = "sim/noise.hex";
    parameter DW=16, BLW=24, SEQ=0, ACCW=48, SQSH=0, SQW=32, EW=40;

    reg clk = 0, rst = 1;
    reg [2:0] sw;
    always #10 clk = ~clk;                    // 50 MHz

    // ---- DUT: only the main ports are connected ----
    wire        done, rpeak_valid, bpm_valid;
    wire [31:0] rpeak_idx;
    wire [15:0] rr_samples, bpm;
    ecg_qrs_top #(.N_SAMPLES(N_SAMPLES), .SAMPLE_DIV(SAMPLE_DIV), .ECG_FILE(ECG_FILE), .NOISE_FILE(NOISE_FILE),
                  .DW(DW), .BLW(BLW), .SEQ(SEQ), .ACCW(ACCW), .SQSH(SQSH), .SQW(SQW), .EW(EW)) dut (
        .clk(clk), .rst(rst), .sw(sw), .done(done),
        .rpeak_valid(rpeak_valid), .rpeak_idx(rpeak_idx), .rr_samples(rr_samples), .bpm(bpm), .bpm_valid(bpm_valid));

    // ---- internal taps, read hierarchically (not ports) ----
    wire        x_v = dut.x_v, hp_v = dut.hp_v, bp_v = dut.bp_v, d_v = dut.d_v, env_v = dut.env_v, det_v = dut.det_v;
    wire signed [15:0] x_dbg = dut.x_dbg, hp_dbg = dut.hp_dbg, bp_dbg = dut.bp_dbg, d_dbg = dut.d_dbg;
    wire [39:0] env_dbg = dut.env_dbg;
    wire [31:0] det_p_dbg = dut.det_p_dbg;
    wire [15:0] cyc_pipe_max = dut.cyc_pipe_max, cyc_beat_max = dut.cyc_beat_max;

    reg [8*80-1:0] outdir, fname;
    integer f_x, f_hp, f_bp, f_d, f_env, f_det, f_r, f_bpm, sw_i, nbeats;

    initial begin
        if (!$value$plusargs("OUT=%s", outdir)) outdir = "sim";
        if (!$value$plusargs("SW=%d", sw_i))   sw_i = 0;
        sw = sw_i[2:0];
        $sformat(fname, "%0s/x.txt",   outdir); f_x   = $fopen(fname, "w");
        $sformat(fname, "%0s/hp.txt",  outdir); f_hp  = $fopen(fname, "w");
        $sformat(fname, "%0s/bp.txt",  outdir); f_bp  = $fopen(fname, "w");
        $sformat(fname, "%0s/d.txt",   outdir); f_d   = $fopen(fname, "w");
        $sformat(fname, "%0s/env.txt", outdir); f_env = $fopen(fname, "w");
        $sformat(fname, "%0s/det.txt", outdir); f_det = $fopen(fname, "w");
        $sformat(fname, "%0s/rpeaks.txt", outdir); f_r = $fopen(fname, "w");
        $sformat(fname, "%0s/bpm.txt", outdir); f_bpm = $fopen(fname, "w");
        nbeats = 0;
        $dumpfile("sim/ecg_qrs.vcd");
        if ($test$plusargs("VCD")) $dumpvars(0, tb_ecg_qrs);
        repeat (10) @(posedge clk);
        rst = 0;
        wait (done);
        repeat (3000) @(posedge clk);         // let the last beat finish localisation and BPM division
        $display("TB finished: %0d beats detected, noise level SW=%0d, %0d samples", nbeats, sw_i, N_SAMPLES);
        $display("CYCLES: pipe_max=%0d beat_max=%0d (clock cycles; available per sample = SAMPLE_DIV = %0d)", cyc_pipe_max, cyc_beat_max, SAMPLE_DIV);
        $fclose(f_x); $fclose(f_hp); $fclose(f_bp); $fclose(f_d); $fclose(f_env); $fclose(f_det); $fclose(f_r); $fclose(f_bpm);
        $finish;
    end

    always @(posedge clk) if (!rst) begin
        if (x_v)   $fdisplay(f_x,   "%0d", x_dbg);
        if (hp_v)  $fdisplay(f_hp,  "%0d", hp_dbg);
        if (bp_v)  $fdisplay(f_bp,  "%0d", bp_dbg);
        if (d_v)   $fdisplay(f_d,   "%0d", d_dbg);
        if (env_v) $fdisplay(f_env, "%0d", env_dbg);
        if (det_v) $fdisplay(f_det, "%0d", det_p_dbg);
        if (rpeak_valid) begin $fdisplay(f_r, "%0d", rpeak_idx); nbeats = nbeats + 1; end
        if (bpm_valid)   $fdisplay(f_bpm, "%0d %0d", rr_samples, bpm);
    end
endmodule
