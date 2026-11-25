`timescale 1ns/1ps
// Baseline-wander removal: IIR baseline estimate (fc ~ 0.45 Hz) subtracted from the input.
//   bl[n] = bl[n-1] + ((x[n]<<8) - bl[n-1]) >> 7   (8 fractional bits)     y[n] = x[n] - (bl[n] >> 8)
// W = data width, BLW = width of the baseline register (must hold W+8 bits).
module baseline_remove #(parameter W = 16, parameter BLW = 24) (
    input  wire               clk,
    input  wire               rst,
    input  wire               in_valid,
    input  wire signed [W-1:0] x,
    output reg                out_valid,
    output reg  signed [W-1:0] y
);
    localparam integer HI =  (1 << (W-1)) - 1;
    localparam integer LO = -(1 << (W-1));
    reg  signed [BLW-1:0] bl;
    wire signed [BLW-1:0] xs     = x;
    wire signed [BLW-1:0] xq     = xs <<< 8;
    wire signed [BLW-1:0] bl_new = bl + ((xq - bl) >>> 7);
    wire signed [BLW-1:0] bl_i   = bl_new >>> 8;
    wire signed [BLW-1:0] diff   = xs - bl_i;
    always @(posedge clk) begin
        if (rst) begin bl <= 0; y <= 0; out_valid <= 1'b0; end
        else begin
            out_valid <= in_valid;
            if (in_valid) begin
                bl <= bl_new;
                y  <= (diff > HI) ? HI : (diff < LO) ? LO : diff[W-1:0];
            end
        end
    end
endmodule
