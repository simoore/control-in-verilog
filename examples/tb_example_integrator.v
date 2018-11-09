`timescale 1ns / 1ps

module tb_example_integrator;

    reg clk, ce_in;
    reg [23:0] sig_in;
    wire ce_out;
    wire [23:0] sig_out;

    example_integrator dut (clk, ce_in, sig_in, ce_out, sig_out);

    initial begin
        clk = 0;
        ce_in = 0;
        sig_in = 32'b0;
    end

    always begin
        #8 ce_in = 1;
        #2 ce_in = 0;
    end

    always begin
        #100 sig_in = 24'd419430;      // ~0.1 in s(24,22)
        #10000 sig_in = 24'd4194304;   // 1 in s(24,22)
        #20000 sig_in = -24'd4194304;    // -1 in s(24,22)
        #19900;
    end

    always begin
        #1 clk = ~clk;
    end

endmodule