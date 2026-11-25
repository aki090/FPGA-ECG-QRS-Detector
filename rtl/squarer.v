`timescale 1ns/1ps
// Squaring, then an optional right shift (SQSHIFT) to save bits; result saturates to SW bits.
module squarer #(parameter DW = 16, parameter SQSHIFT = 0, parameter SW = 32) (
    input  wire                clk,
    input  wire                rst,
    input  wire                in_valid,
    input  wire signed [DW-1:0] d,
    output reg                 out_valid,
    output reg  [SW-1:0]       sq
);
    localparam [2*DW-1:0] MAXP = {(2*DW){1'b1}} >> (2*DW-SW);   // largest value that fits in SW bits
    wire [2*DW-1:0] maxs = MAXP;
    wire signed [2*DW-1:0] p  = d * d;
    wire        [2*DW-1:0] pu = p;
    wire        [2*DW-1:0] ps = pu >> SQSHIFT;
    always @(posedge clk) begin
        if (rst) begin sq <= 0; out_valid <= 1'b0; end
        else begin
            out_valid <= in_valid;
            if (in_valid) sq <= (ps > maxs) ? maxs[SW-1:0] : ps[SW-1:0];
        end
    end
endmodule
