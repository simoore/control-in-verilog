module {{ NAME }} #
(
    parameter IW = {{ IW }},
    parameter OW = {{ OW }},
    parameter N_RAM = {{ N_RAM }}
)(
    input logic clk,
    input logic ce_in,
    input logic [IW-1:0] sig_in,
    output logic ce_out,
    output logic [OW-1:0] sig_out
);

    logic ce_buf;
    logic [IW-1:0] sig_in_buf;
    logic [OW-1:0] func_lut [0:N_RAM-1];
      
    // Input buffer.
    always_ff @(posedge clk) begin
        ce_buf <= ce_in;
        if(ce_in) sig_in_buf <= sig_in;
    end
    
    // Lookup table read.
    always_ff @(posedge clk) begin
        ce_out <= ce_buf;
        sig_out <= func_lut[sig_in_buf];
    end

    initial begin
        ce_buf = 0;
        sig_in_buf = 0;
        {% for val in RAM %} 
        func_lut[{{ loop.index-1 }}] = {{ val }}; {% endfor %}
    end

endmodule