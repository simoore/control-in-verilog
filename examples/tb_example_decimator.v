`timescale 1ns / 1ps

module tb_example_decimator;

    reg clk;
    wire ce_out;
    reg [15:0] sig_in;
    wire [15:0] sig_out;

    example_decimator dut (
        .clk       (clk),
        .ce_in     (1'b1),
        .ce_out    (ce_out),
        .sig_in    (sig_in),
        .sig_out   (sig_out));

    initial begin
        clk = 0;
        sig_in = 0;
    end

    always begin
        #1 clk = !clk;
    end

    always @(posedge clk)
        sig_in = sig_in + 1;

endmodule