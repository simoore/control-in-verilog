// Need to write a testbench for this module.
module delay #
(
    parameter DW = 16,  // data word length
    parameter AW = 8    // buffer address word length
)(
    input wire clk,
    input wire ce_in,
    input wire [DW-1:0] sig_in,
    input wire [AW-1:0] delay,
    output reg ce_out,
    output reg [DW-1:0] sig_out
);

    reg [AW-1:0] rd_ptr = 0;
    reg [AW-1:0] wr_ptr = 0;
    reg [DW-1:0] buffer[2**AW-1:0];
    
    // There wil be a glitch in the output at the start and upon change
    // in delay. Ensure your system can handle it.
    always @(posedge clk) begin
        ce_out <= ce_in;
        if (ce_in) begin
            buffer[wr_ptr] <= sig_in;
            sig_out <= buffer[rd_ptr];
            wr_ptr <= rd_ptr + delay; 
            rd_ptr <= rd_ptr + 1;
        end
    end

endmodule
