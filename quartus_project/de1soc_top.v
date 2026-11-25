`timescale 1ns/1ps
// DE1-SoC top level for the ECG QRS detector.
// Port names match the Terasic DE1-SoC pin file (CLOCK_50, KEY, SW, LEDR, HEX0..HEX5), so the official
// pin assignments can be imported directly. Do NOT type pins by hand.
//
//   OPT = 0 : BASELINE  (16-bit data, 41 parallel multipliers)
//   OPT = 1 : OPTIMISED (12-bit data, one shared multiplier)      <- default; change this one number to 0 for the baseline
//
//   KEY[0]    reset (press = restart, active low)
//   SW[2:0]   noise level: 0 = clean ECG ... 7 = very noisy
//   LEDR[9]   flashes on every detected heartbeat
//   LEDR[8]   ECG recording finished (it restarts by itself after about 1 second)
//   LEDR[2:0] echo of the noise switches
//   HEX2..HEX0  heart rate in beats per minute (decimal)
module de1soc_top #(
    parameter OPT        = 1,
    parameter N_SAMPLES  = 36000,       // 100 s of ECG stored in on-chip memory
    parameter SAMPLE_DIV = 138889,      // 50 MHz / 360 Hz  (one ECG sample every 1/360 s)
    parameter STRETCH    = 5000000,     // beat LED stays on about 100 ms
    parameter RESTART_WAIT = 50000000   // wait about 1 s after the ECG ends, then restart
)(
    input  wire        CLOCK_50,
    input  wire [0:0]  KEY,
    input  wire [2:0]  SW,
    output wire [9:0]  LEDR,
    output wire [6:0]  HEX0, HEX1, HEX2, HEX3, HEX4, HEX5
);
    // ---- reset: push button + automatic restart when the recording ends ----
    reg [1:0]  key_s;
    always @(posedge CLOCK_50) key_s <= {key_s[0], KEY[0]};
    wire       key_rst = ~key_s[1];

    wire       done;
    reg [31:0] wait_cnt = 0;
    reg [4:0]  auto_cnt = 0;
    wire       auto_rst = (auto_cnt != 0);
    wire       rst = key_rst | auto_rst;
    always @(posedge CLOCK_50) begin
        if (!done) begin wait_cnt <= 0; if (auto_cnt != 0) auto_cnt <= auto_cnt - 1'b1; end
        else if (wait_cnt < RESTART_WAIT) wait_cnt <= wait_cnt + 1'b1;
        else if (auto_cnt == 0) auto_cnt <= 5'd20;
        else auto_cnt <= auto_cnt - 1'b1;
    end

    // ---- the detector ----
    wire        rpeak_valid, bpm_valid;
    wire [31:0] rpeak_idx;
    wire [15:0] rr_samples, bpm;

    ecg_qrs_top #(
        .N_SAMPLES(N_SAMPLES), .SAMPLE_DIV(SAMPLE_DIV), .ECG_FILE("ecg.hex"), .NOISE_FILE("noise.hex"),
        .DW  (OPT ? 12 : 16), .BLW (OPT ? 20 : 24), .SEQ (OPT ? 1 : 0), .ACCW(OPT ? 32 : 48),
        .SQSH(OPT ? 4  : 0 ), .SQW (OPT ? 18 : 32), .EW  (OPT ? 24 : 40)
    ) u_det (
        .clk(CLOCK_50), .rst(rst), .sw(SW[2:0]), .done(done),
        .rpeak_valid(rpeak_valid), .rpeak_idx(rpeak_idx), .rr_samples(rr_samples), .bpm(bpm), .bpm_valid(bpm_valid));

    // ---- beat LED: stretch each one-clock beat pulse to about 100 ms ----
    reg [23:0] led_cnt = 0;
    always @(posedge CLOCK_50) begin
        if (rst) led_cnt <= 0;
        else if (rpeak_valid) led_cnt <= STRETCH;
        else if (led_cnt != 0) led_cnt <= led_cnt - 1'b1;
    end
    assign LEDR[9]   = (led_cnt != 0);
    assign LEDR[8]   = done;
    assign LEDR[7:3] = 5'b0;
    assign LEDR[2:0] = SW[2:0];

    // ---- heart rate on the 7-segment displays (decimal, up to 999) ----
    reg [9:0] bpm_hold = 0;
    always @(posedge CLOCK_50) begin
        if (rst) bpm_hold <= 0;
        else if (bpm_valid) bpm_hold <= (bpm > 16'd999) ? 10'd999 : bpm[9:0];
    end
    wire [3:0] d0 = bpm_hold % 10;
    wire [3:0] d1 = (bpm_hold / 10) % 10;
    wire [3:0] d2 = bpm_hold / 100;
    function [6:0] seg;            // active-low segments {g,f,e,d,c,b,a}
        input [3:0] v;
        case (v)
            4'd0: seg = 7'b1000000; 4'd1: seg = 7'b1111001; 4'd2: seg = 7'b0100100; 4'd3: seg = 7'b0110000;
            4'd4: seg = 7'b0011001; 4'd5: seg = 7'b0010010; 4'd6: seg = 7'b0000010; 4'd7: seg = 7'b1111000;
            4'd8: seg = 7'b0000000; 4'd9: seg = 7'b0010000; default: seg = 7'b1111111;
        endcase
    endfunction
    assign HEX0 = seg(d0);
    assign HEX1 = (bpm_hold < 10)  ? 7'b1111111 : seg(d1);
    assign HEX2 = (bpm_hold < 100) ? 7'b1111111 : seg(d2);
    assign HEX3 = 7'b1111111;
    assign HEX4 = 7'b1111111;
    assign HEX5 = 7'b1111111;
endmodule
