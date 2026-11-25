`timescale 1ns/1ps
// Sample controller + ECG ROM + noise ROM  (block: "Sample controller / ECG ROM / Noise ROM")
// One ECG sample (and one noise sample) is released every SAMPLE_DIV clock cycles.
//   real board : SAMPLE_DIV = 50_000_000 / 360 = 138889  (50 MHz clock -> 360 Hz)
//   simulation : SAMPLE_DIV = 200 (faster than real time, algorithm unchanged)
module sample_source #(
    parameter N_SAMPLES  = 36000,
    parameter SAMPLE_DIV = 200,
    parameter ECG_FILE   = "sim/ecg.hex",
    parameter NOISE_FILE = "sim/noise.hex"
)(
    input  wire              clk,
    input  wire              rst,
    output reg               valid,
    output reg signed [11:0] ecg,
    output reg signed [11:0] noise,
    output reg               done
);
    reg signed [11:0] ecg_mem   [0:N_SAMPLES-1];
    reg signed [11:0] noise_mem [0:N_SAMPLES-1];
    initial begin
        $readmemh(ECG_FILE,   ecg_mem);
        $readmemh(NOISE_FILE, noise_mem);
    end

    reg [31:0] cnt;
    reg [31:0] addr;
    reg        rd;
    reg        running;

    always @(posedge clk) begin
        if (rst) begin
            cnt <= 0; addr <= 0; rd <= 0; valid <= 0; done <= 0; running <= 1'b1;
        end else begin
            valid <= rd;
            rd    <= 1'b0;
            if (running) begin
                if (cnt == SAMPLE_DIV-1) begin cnt <= 0; rd <= 1'b1; end
                else cnt <= cnt + 1;
            end
            if (rd) begin
                addr <= addr + 1;
                if (addr == N_SAMPLES-1) running <= 1'b0;
            end
            if (!running && !rd) done <= 1'b1;
        end
        ecg   <= ecg_mem[addr];
        noise <= noise_mem[addr];
    end
endmodule
