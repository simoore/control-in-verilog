`timescale 1ns / 1ps

module tb_example_lti_system;

    reg clk, ce_in;
    reg [15:0] sig_in;
    wire ce_out;
    wire [19:0] sig_out;

    example_lti_system dut (
        .clk        (clk),
        .ce_in      (ce_in),
        .sig_in_1   (sig_in),
        .ce_out     (ce_out),
        .sig_out_1  (sig_out)
    );

    initial begin
        clk = 0;
        ce_in = 0;
        sig_in = 16'b0;
        #100 sig_in = 16'h4000;
    end

    always begin
        #2 ce_in = 0;
        #8 ce_in = 1;
    end

    always begin
        #1 clk = !clk;
    end

endmodule
