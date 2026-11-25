`timescale 1ns/1ps
// RR interval and heart rate:  RR = R-peak[n] - R-peak[n-1] (samples) ;  BPM = 60 * 360 / RR = 21600 / RR
module rr_bpm (
    input  wire        clk,
    input  wire        rst,
    input  wire        r_valid,
    input  wire [31:0] r_idx,
    output reg  [15:0] rr,
    output reg  [15:0] bpm,
    output reg         bpm_valid
);
    reg        have, start;
    reg [31:0] prev, den;
    wire       dv;
    wire [31:0] dq;
    seq_div u_div (.clk(clk), .rst(rst), .start(start), .num(32'd21600), .den(den), .done(dv), .quot(dq));
    always @(posedge clk) begin
        start <= 1'b0; bpm_valid <= 1'b0;
        if (rst) begin have <= 0; prev <= 0; den <= 1; rr <= 0; bpm <= 0; end
        else begin
            if (r_valid) begin
                if (have && (r_idx > prev)) begin den <= r_idx - prev; rr <= r_idx - prev; start <= 1'b1; end
                prev <= r_idx; have <= 1'b1;
            end
            if (dv) begin bpm <= dq[15:0]; bpm_valid <= 1'b1; end
        end
    end
endmodule
