`timescale 1ns/1ps
// R-peak localisation with delay compensation (project contribution 4).
// The integrated-signal peak comes ~20-48 samples AFTER the real R-peak. A 1024-sample buffer of the
// baseline-corrected ECG is kept; when a beat is accepted, the window [p-SB, p-SF] is scanned and the
// sample with the largest |amplitude| is reported as the R-peak position.
module rpeak_locator #(parameter W = 16, parameter SB = 64, parameter SF = 4) (
    input  wire               clk,
    input  wire               rst,
    input  wire               hp_valid,
    input  wire signed [W-1:0] hp,
    input  wire               det_valid,
    input  wire        [31:0] det_p,
    output reg                out_valid,
    output reg         [31:0] rpeak_idx
);
    reg signed [W-1:0] hbuf [0:1023];
    reg [31:0] wcnt, lo, i, best_i;
    reg [W-1:0] best_abs;
    reg        busy, first;
    wire [9:0]         ra = lo + i;
    wire signed [W-1:0] v  = hbuf[ra];
    wire [W-1:0] vu = v;
    wire [W-1:0] av = v[W-1] ? (~vu + 1'b1) : vu;
    wire               better = first || (av > best_abs);
    always @(posedge clk) begin
        out_valid <= 1'b0;
        if (rst) begin wcnt <= 0; busy <= 0; first <= 0; lo <= 0; i <= 0; best_i <= 0; best_abs <= 0; rpeak_idx <= 0; end
        else begin
            if (hp_valid) begin hbuf[wcnt[9:0]] <= hp; wcnt <= wcnt + 1; end
            if (det_valid) begin busy <= 1'b1; lo <= det_p - SB; i <= 0; first <= 1'b1; end
            else if (busy) begin
                if (better) begin best_abs <= av; best_i <= lo + i; first <= 1'b0; end
                if (i == SB - SF) begin
                    busy <= 1'b0; out_valid <= 1'b1;
                    rpeak_idx <= better ? (lo + i) : best_i;
                end else i <= i + 1;
            end
        end
    end
endmodule
