`timescale 1ns / 1ps

module tb_example_saturation;

    reg [21:0] sig_in;
    wire [15:0] sig_out;

    example_saturation dut (
        .sig_in    (sig_in),
        .sig_out   (sig_out));

    initial begin
        sig_in = 0;
    end

    always begin
        #2 sig_in = sig_in + 100;
    end

endmodule
