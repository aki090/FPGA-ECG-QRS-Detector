`timescale 1ns/1ps
// Top level: ECG ROM -> noise injector -> baseline removal -> FIR band-pass -> derivative -> squaring
//            -> moving-window integrator -> QRS decision -> R-peak localisation -> RR / BPM
//
// Defaults = BASELINE design (16-bit data, parallel FIR with 41 multipliers, 40-bit envelope).
// OPTIMISED design:  DW=12 BLW=20 SEQ=1 ACCW=32 SQSH=4 SQW=18 EW=24
module ecg_qrs_top #(
    parameter N_SAMPLES  = 36000,
    parameter SAMPLE_DIV = 200,
    parameter ECG_FILE   = "sim/ecg.hex",
    parameter NOISE_FILE = "sim/noise.hex",
    parameter DW   = 16,     // data width (noise injector, baseline removal, FIR, derivative)
    parameter BLW  = 24,     // baseline-register width (>= DW + 8)
    parameter SEQ  = 0,      // 0 = parallel FIR (41 multipliers), 1 = one shared multiplier
    parameter ACCW = 48,     // FIR accumulator width
    parameter SQSH = 0,      // right shift applied after squaring
    parameter SQW  = 32,     // squared-value width
    parameter EW   = 40      // envelope (moving-sum) width
)(
    // ---------------- INPUT PORTS ----------------
    input  wire        clk,           // 50 MHz clock
    input  wire        rst,           // reset, high = reset
    input  wire [2:0]  sw,            // noise level k (0 = clean ... 7 = very noisy)
    // ---------------- OUTPUT PORTS (the main results only) ----------------
    output wire        done,          // whole ECG recording has been processed
    output wire        rpeak_valid,   // one pulse per detected heartbeat
    output wire [31:0] rpeak_idx,     // R-peak sample index
    output wire [15:0] rr_samples,    // RR interval in samples
    output wire [15:0] bpm,           // heart rate in beats per minute
    output wire        bpm_valid      // bpm / rr_samples are valid
);
    // Internal stage signals (NOT ports). The testbench reads them hierarchically (dut.x_v, ...).
    wire        x_v, hp_v, bp_v, d_v, env_v, det_v;
    wire signed [15:0] x_dbg, hp_dbg, bp_dbg, d_dbg;
    wire [39:0]        env_dbg;
    wire [31:0]        det_p_dbg;
    wire              s_valid;  wire signed [11:0] s_ecg, s_noise;
    wire              sq_v;     wire [SQW-1:0] sq;
    wire [EW-1:0]     thr_dbg;
    wire signed [DW-1:0] x_w, hp_w, bp_w, d_w;
    wire [EW-1:0]        env_w;

    sample_source #(.N_SAMPLES(N_SAMPLES), .SAMPLE_DIV(SAMPLE_DIV), .ECG_FILE(ECG_FILE), .NOISE_FILE(NOISE_FILE))
        u_src (.clk(clk), .rst(rst), .valid(s_valid), .ecg(s_ecg), .noise(s_noise), .done(done));
    noise_injector  #(.OW(DW))                       u_inj (.clk(clk), .rst(rst), .in_valid(s_valid), .ecg(s_ecg), .noise(s_noise), .k(sw), .out_valid(x_v), .y(x_w));
    baseline_remove #(.W(DW), .BLW(BLW))             u_bl  (.clk(clk), .rst(rst), .in_valid(x_v),  .x(x_w),  .out_valid(hp_v), .y(hp_w));
    fir_bp          #(.W(DW), .SEQ(SEQ), .ACCW(ACCW)) u_fir (.clk(clk), .rst(rst), .in_valid(hp_v), .x(hp_w), .out_valid(bp_v), .y(bp_w));
    derivative      #(.W(DW))                        u_der (.clk(clk), .rst(rst), .in_valid(bp_v), .x(bp_w), .out_valid(d_v),  .d(d_w));
    squarer         #(.DW(DW), .SQSHIFT(SQSH), .SW(SQW)) u_sqr (.clk(clk), .rst(rst), .in_valid(d_v), .d(d_w), .out_valid(sq_v), .sq(sq));
    mwi             #(.SW(SQW), .EW(EW))             u_mwi (.clk(clk), .rst(rst), .in_valid(sq_v), .sq(sq), .out_valid(env_v), .env(env_w));
    qrs_decision    #(.EW(EW))                       u_dec (.clk(clk), .rst(rst), .in_valid(env_v), .env(env_w), .det_valid(det_v), .det_p(det_p_dbg), .thr_out(thr_dbg));
    rpeak_locator   #(.W(DW))                        u_loc (.clk(clk), .rst(rst), .hp_valid(hp_v), .hp(hp_w), .det_valid(det_v), .det_p(det_p_dbg), .out_valid(rpeak_valid), .rpeak_idx(rpeak_idx));
    rr_bpm                                           u_bpm (.clk(clk), .rst(rst), .r_valid(rpeak_valid), .r_idx(rpeak_idx), .rr(rr_samples), .bpm(bpm), .bpm_valid(bpm_valid));

    assign x_dbg = x_w;  assign hp_dbg = hp_w;  assign bp_dbg = bp_w;  assign d_dbg = d_w;  assign env_dbg = env_w;

    // ---- cycle counters (real-time margin): simulation measurement only, not built in hardware ----
    // synthesis translate_off
    reg [15:0] cyc_pipe_max, cyc_beat_max;
    reg [15:0] c1, c2; reg run1, run2;
    always @(posedge clk) begin
        if (rst) begin c1<=0; c2<=0; run1<=0; run2<=0; cyc_pipe_max<=0; cyc_beat_max<=0; end
        else begin
            if (s_valid) begin run1 <= 1'b1; c1 <= 16'd1; end else if (run1) c1 <= c1 + 1;
            if (env_v && run1) begin run1 <= 1'b0; if (c1 > cyc_pipe_max) cyc_pipe_max <= c1; end
            if (det_v) begin run2 <= 1'b1; c2 <= 16'd1; end else if (run2) c2 <= c2 + 1;
            if (bpm_valid && run2) begin run2 <= 1'b0; if (c2 > cyc_beat_max) cyc_beat_max <= c2; end
        end
    end
    // synthesis translate_on
endmodule
