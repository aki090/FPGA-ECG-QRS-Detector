`timescale 1ns/1ps
// DEMO testbench for presentation: prints every detected heartbeat on the console and writes a VCD file for GTKWave.
//   vvp sim/demo.vvp +SW=0 +VCD=sim/demo_overview.vcd                     -> 10 s of ECG, all main signals
//   vvp sim/demo.vvp +SW=0 +VCD=sim/demo_zoom.vcd +ZOOM=<sample>          -> only ~450 clock cycles around ECG sample <sample>
module tb_demo;
    parameter N_SAMPLES  = 3600;        // 10 seconds of ECG at 360 Hz
    parameter SAMPLE_DIV = 100;         // clock cycles per ECG sample (simulation speed-up)
    parameter ZOOM_CLKS  = 450;

    reg        clk = 0;
    reg        rst = 1;
    reg  [2:0] sw;
    always #10 clk = ~clk;              // 50 MHz clock

    // ---- DUT: only the main ports are connected ----
    wire        done, beat_pulse, bpm_valid;
    wire [31:0] rpeak_index;
    wire [15:0] rr_samples, bpm;
    ecg_qrs_top #(.N_SAMPLES(N_SAMPLES), .SAMPLE_DIV(SAMPLE_DIV), .ECG_FILE("sim/ecg_demo.hex"), .NOISE_FILE("sim/noise_demo.hex")) dut (
        .clk(clk), .rst(rst), .sw(sw), .done(done),
        .rpeak_valid(beat_pulse), .rpeak_idx(rpeak_index), .rr_samples(rr_samples), .bpm(bpm), .bpm_valid(bpm_valid));

    // ---- internal pipeline signals, read hierarchically for the zoom pictures (not ports) ----
    wire        sample_valid = dut.x_v, baseline_valid = dut.hp_v, filtered_valid = dut.bp_v, deriv_valid = dut.d_v,
                envelope_valid = dut.env_v, peak_found = dut.det_v;
    wire signed [15:0] ecg_in = dut.x_dbg, baseline_removed = dut.hp_dbg, filtered = dut.bp_dbg, derivative = dut.d_dbg;
    wire [39:0] envelope = dut.env_dbg;
    wire [31:0] envelope_peak_index = dut.det_p_dbg;

    integer sw_i, z0, nbeats;
    reg [8*80-1:0] vcdname;

    initial begin
        if (!$value$plusargs("SW=%d", sw_i)) sw_i = 0;
        sw = sw_i[2:0];
        if (!$value$plusargs("VCD=%s", vcdname)) vcdname = "sim/demo.vcd";
        $dumpfile(vcdname);
        nbeats = 0;
        $display("=== ECG QRS detector simulation: %0d samples (%0d s of ECG), noise switch SW = %0d ===", N_SAMPLES, N_SAMPLES/360, sw_i);
        if ($value$plusargs("ZOOM=%d", z0)) begin
            $dumpvars(1, tb_demo); $dumpoff;
            repeat (10) @(posedge clk); rst = 0;
            wait (dut.u_src.addr == z0);
            $dumpon;
            repeat (ZOOM_CLKS) @(posedge clk);
            $dumpoff;
            $display("=== zoom window written (%0d clock cycles around ECG sample %0d) ===", ZOOM_CLKS, z0);
            $finish;
        end else begin
            $dumpvars(1, tb_demo);
            repeat (10) @(posedge clk); rst = 0;
            wait (done);
            repeat (3000) @(posedge clk);
            $display("=== SIMULATION COMPLETE: %0d heartbeats detected ===", nbeats);
            $finish;
        end
    end

    always @(posedge clk) if (!rst) begin
        if (beat_pulse) begin
            nbeats = nbeats + 1;
            $display("t = %0d ns | HEARTBEAT %0d detected at ECG sample %0d (%0.2f s)", $time, nbeats, rpeak_index, rpeak_index/360.0);
        end
        if (bpm_valid) $display("                    RR = %0d samples  ->  heart rate = %0d BPM", rr_samples, bpm);
    end
endmodule
