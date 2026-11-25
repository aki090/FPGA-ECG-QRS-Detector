`timescale 1ns/1ps
// Sequential restoring divider (32 clock cycles) - used for BPM = 21600 / RR.
module seq_div (
    input  wire        clk,
    input  wire        rst,
    input  wire        start,
    input  wire [31:0] num,
    input  wire [31:0] den,
    output reg         done,
    output reg  [31:0] quot
);
    reg [31:0] rem, q, d;
    reg [5:0]  cnt;
    reg        busy;
    reg [31:0] rem_n, q_n;
    always @(posedge clk) begin
        done <= 1'b0;
        if (rst) begin busy <= 0; cnt <= 0; quot <= 0; rem <= 0; q <= 0; d <= 1; end
        else if (start && !busy) begin rem <= 0; q <= num; d <= den; cnt <= 6'd32; busy <= 1'b1; end
        else if (busy) begin
            rem_n = {rem[30:0], q[31]}; q_n = {q[30:0], 1'b0};
            if (rem_n >= d) begin rem_n = rem_n - d; q_n[0] = 1'b1; end
            rem <= rem_n; q <= q_n; cnt <= cnt - 1;
            if (cnt == 6'd1) begin busy <= 1'b0; done <= 1'b1; quot <= q_n; end
        end
    end
endmodule
