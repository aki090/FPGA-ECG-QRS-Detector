`timescale 1ns/1ps
// Noise injector (project contribution 1): y = ecg + (noise * k) / 8,  k = SW[2:0] = 0..7
// OW = output width (16 baseline, 12 optimised); result saturates to OW bits.
module noise_injector #(parameter OW = 16) (
    input  wire               clk,
    input  wire               rst,
    input  wire               in_valid,
    input  wire signed [11:0] ecg,
    input  wire signed [11:0] noise,
    input  wire        [2:0]  k,
    output reg                out_valid,
    output reg  signed [OW-1:0] y
);
    localparam integer HI =  (1 << (OW-1)) - 1;
    localparam integer LO = -(1 << (OW-1));
    wire signed [23:0] e      = ecg;
    wire signed [23:0] nz     = noise;
    wire signed [3:0]  kk     = {1'b0, k};
    wire signed [23:0] prod   = nz * kk;
    wire signed [23:0] scaled = prod >>> 3;
    wire signed [23:0] sum    = e + scaled;
    always @(posedge clk) begin
        if (rst) begin out_valid <= 1'b0; y <= 0; end
        else begin
            out_valid <= in_valid;
            if (in_valid) y <= (sum > HI) ? HI : (sum < LO) ? LO : sum[OW-1:0];
        end
    end
endmodule
