`timescale 1ns/1ps
// Moving-window integrator: sum of the last WINDOW squared values (54 samples = 150 ms at 360 Hz).
// Running sum: add the newest value, subtract the oldest. SW = input width, EW = sum width.
module mwi #(parameter WINDOW = 54, parameter SW = 32, parameter EW = 40) (
    input  wire          clk,
    input  wire          rst,
    input  wire          in_valid,
    input  wire [SW-1:0] sq,
    output reg           out_valid,
    output reg  [EW-1:0] env
);
    reg [SW-1:0] buffer [0:WINDOW-1];
    reg [EW-1:0] sum;
    reg [EW-1:0] new_sum;
    integer idx;
    integer i;
    always @(posedge clk) begin
        if (rst) begin
            for (i = 0; i < WINDOW; i = i + 1) buffer[i] <= 0;
            sum <= 0; idx <= 0; env <= 0; out_valid <= 1'b0;
        end else begin
            out_valid <= in_valid;
            if (in_valid) begin
                new_sum = sum + sq - buffer[idx];
                buffer[idx] <= sq;
                idx <= (idx == WINDOW-1) ? 0 : idx + 1;
                sum <= new_sum;
                env <= new_sum;
            end
        end
    end
endmodule
