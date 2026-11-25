`timescale 1ns/1ps
// Five-point derivative (Pan-Tompkins):  d[n] = ( 2x[n] + x[n-1] - x[n-3] - 2x[n-4] ) >>> 3   (saturates to W bits)
module derivative #(parameter W = 16) (
    input  wire               clk,
    input  wire               rst,
    input  wire               in_valid,
    input  wire signed [W-1:0] x,
    output reg                out_valid,
    output reg  signed [W-1:0] d
);
    localparam integer HI =  (1 << (W-1)) - 1;
    localparam integer LO = -(1 << (W-1));
    reg signed [W-1:0] h1, h2, h3, h4;
    wire signed [W+3:0] e0 = x, e1 = h1, e3 = h3, e4 = h4;
    wire signed [W+3:0] t  = (e0 <<< 1) + e1 - e3 - (e4 <<< 1);
    wire signed [W+3:0] q  = t >>> 3;
    always @(posedge clk) begin
        if (rst) begin h1<=0; h2<=0; h3<=0; h4<=0; d<=0; out_valid<=1'b0; end
        else begin
            out_valid <= in_valid;
            if (in_valid) begin
                d <= (q > HI) ? HI : (q < LO) ? LO : q[W-1:0];
                h4 <= h3; h3 <= h2; h2 <= h1; h1 <= x;
            end
        end
    end
endmodule
