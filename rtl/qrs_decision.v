`timescale 1ns/1ps
// QRS decision block: peak detector + adaptive threshold + refractory period + T-wave check + search-back.
//   * first INIT samples (2 s): learn signal / noise levels, no detection
//   * a "peak" is a local maximum of the integrated signal (env[n-1] > env[n-2] and env[n-1] >= env[n])
//   * THR = NPKI + (SPKI - NPKI)/4 ; SPKI/NPKI are running signal-peak / noise-peak levels (shift-only updates)
//   * accepted only if peak > THR and >= REFR samples (200 ms) after the previous beat
//   * a peak that is too soon (< 360 ms) and less than half the previous peak is treated as a T-wave
//   * search-back: if no beat for 1.75 x average RR, accept the strongest rejected peak above THR/2
module qrs_decision #(
    parameter EW        = 40,
    parameter INIT      = 720,
    parameter REFR      = 72,
    parameter TWAVE_GAP = 130
)(
    input  wire        clk,
    input  wire        rst,
    input  wire        in_valid,
    input  wire [EW-1:0] env,
    output reg         det_valid,
    output reg  [31:0] det_p,       // sample index of the envelope peak
    output reg  [EW-1:0] thr_out
);
    reg [31:0] n;
    reg [EW-1:0] e1, e2, mx, spki, npki, thr, last_pk, cand_v;
    reg [EW+10:0] sm;
    reg        have, cand_ok;
    reg [31:0] last_p, cand_i, p, gap, limit, ra;
    reg signed [31:0] rr_avg, rr;
    reg        okgap;

    always @(posedge clk) begin
        det_valid <= 1'b0;
        if (rst) begin
            n <= 0; e1 <= 0; e2 <= 0; mx <= 0; sm <= 0; spki <= 0; npki <= 0; thr <= 0;
            last_pk <= 0; cand_v <= 0; have <= 0; cand_ok <= 0; last_p <= 0; cand_i <= 0;
            rr_avg <= 0; rr <= 0; det_p <= 0; thr_out <= 0;
        end else if (in_valid) begin
            if (n < INIT) begin
                if (env > mx) mx = env;
                sm = sm + env;
                if (n == INIT-1) begin spki = mx >> 2; npki = sm >> 11; end
            end else begin
                thr = (spki > npki) ? (npki + ((spki - npki) >> 2)) : npki;
                thr_out <= thr;
                if (e1 > e2 && e1 >= env) begin
                    p     = n - 1;
                    gap   = p - last_p;
                    okgap = (!have) || (gap >= REFR);
                    if (e1 > thr && okgap) begin
                        if (have && gap < TWAVE_GAP && e1 < (last_pk >> 1)) begin
                            npki = npki - (npki >> 3) + (e1 >> 3);               // T-wave: treat as noise
                        end else begin
                            spki = spki - (spki >> 3) + (e1 >> 3);
                            if (have) begin
                                rr = gap;
                                rr_avg = (rr_avg == 0) ? rr : rr_avg + ((rr - rr_avg) >>> 3);
                            end
                            det_valid <= 1'b1; det_p <= p;
                            last_p = p; last_pk = e1; have = 1'b1; cand_ok = 1'b0;
                        end
                    end else if (e1 <= thr) begin
                        npki = npki - (npki >> 3) + (e1 >> 3);
                        if (e1 > (thr >> 1) && okgap && (!cand_ok || e1 > cand_v)) begin
                            cand_v = e1; cand_i = p; cand_ok = 1'b1;
                        end
                    end
                end
                // search-back for a missed beat
                ra    = rr_avg;
                limit = ra + (ra >> 1) + (ra >> 2);
                if (have && rr_avg != 0 && cand_ok && ((n - last_p) > limit)) begin
                    spki = spki - (spki >> 2) + (cand_v >> 2);
                    rr = cand_i - last_p;
                    rr_avg = rr_avg + ((rr - rr_avg) >>> 3);
                    det_valid <= 1'b1; det_p <= cand_i;
                    last_p = cand_i; last_pk = cand_v; have = 1'b1; cand_ok = 1'b0;
                end
            end
            e2 = e1; e1 = env; n = n + 1;
        end
    end
endmodule
