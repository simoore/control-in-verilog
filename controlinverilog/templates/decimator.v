module decimator #
(
    parameter [9:0] TOP = {{ TOP }},    // f_out = f_in / (TOP + 1)
    parameter DW = {{ DW }}
) 
(
    input wire clk, 
    input wire ce_in,
    output reg ce_out = 0,
    input wire [DW-1:0] sig_in,
    output reg [DW-1:0] sig_out = 0
);

    wire ts_pulse;
    reg [9:0] count = TOP;
    
    assign ts_pulse = count == 10'b0;
    
    always @(posedge clk) begin
        ce_out <= ts_pulse;
        
        if (ts_pulse)   count <= TOP;
        else if (ce_in) count <= count - 1;
        
        if (ts_pulse) sig_out <= sig_in;
    end
            
endmodule 
