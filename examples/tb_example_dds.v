`timescale 1ns / 1ps

module tb_example_dds;

    reg clk, ce_in, rst;
    reg [23:0] freqword, phase_offset;
    wire ce_out;
    wire [15:0] sin, cos;

    example_dds dut (
        .clk            (clk),
        .rst            (rst),
        .ce_in          (ce_in),
        .freqword       (freqword),
        .phase_offset   (phase_offset),
        .ce_out         (ce_out),
        .sin            (sin),
        .cos            (cos));

    initial begin
        clk = 0;
        rst = 1;
        ce_in = 1'b1;
        freqword = 24'd6827;
        phase_offset = 0;
        #8 rst = 0;
        #1000 phase_offset = 4194304;
    end

    always begin
        #1 clk = ~clk;
    end

endmodule
