module {{ name }} #
(
    parameter CW = {{ cw }},
    {% for p in A_params %}
    parameter signed [CW-1:0] {{ p["name"] }} = {{ p["value"] }}, 
    {% endfor %}
    {% for p in B_params %}
    parameter signed [CW-1:0] {{ p["name"] }} = {{ p["value"] }}, 
    {% endfor %}
    {% for p in C_params %}
    parameter signed [CW-1:0] {{ p["name"] }} = {{ p["value"] }}, 
    {% endfor %}
    {% for p in D_params %}
    parameter signed [CW-1:0] {{ p["name"] }} = {{ p["value"] }}, 
    {% endfor %}
    parameter IW = {{ iw }},
    parameter OW = {{ ow }},
    parameter SW = {{ sw }},
    parameter CF = {{ cf }},
    parameter SF = {{ sf }},
    parameter IF = {{ if_ }},
    {% if del is not none %}
    parameter DEL = {{ del }},
    {% endif %}
    parameter RW = SW + CW - 1
)
(
    {% for i in sig_in %}
    input wire [IW-1:0] {{ i }}, 
    {% endfor %}
    {% for o in sig_out %}
    output wire [OW-1:0] {{ o }}, 
    {% endfor %}
    input wire clk,
    input wire ce_in,
    output reg ce_out
);

    reg ce_mul;
    reg ce_buf;
    {% for s in reg_ce_add %}
    reg {{ s }};
    {% endfor %}

    {% for s in sig_u %}
    reg signed [SW-1:0] {{ s }};
    {% endfor %}
    {% for s in sig_x %}
    reg signed [SW-1:0] {{ s }};
    {% endfor %}
    {% for s in sig_x_long %}
    reg signed [RW-1:0] {{ s }};
    {% endfor %}
    {% for s in sig_dx %}
    reg signed [RW-1:0] {{ s }};
    {% endfor %}
    {% for s in sig_y_long %}
    reg signed [RW-1:0] {{ s }};
    {% endfor %}
    {% for s in A_sig_prod %}
    reg signed [RW-1:0] {{ s }};
    {% endfor %}
    {% for s in B_sig_prod %}
    reg signed [RW-1:0] {{ s }};
    {% endfor %}
    {% for s in C_sig_prod %}
    reg signed [RW-1:0] {{ s }};
    {% endfor %}
    {% for s in D_sig_prod %}
    reg signed [RW-1:0] {{ s }};
    {% endfor %}
    
    {% for s in state_sig_add %}
    reg signed [RW-1:0] {{ s }};
    {% endfor %}
    {% for s in output_sig_add %}
    reg signed [RW-1:0] {{ s }};
    {% endfor %}
    
    /**************************************************************************
    * The input and quantized state buffer.
    **************************************************************************/
    always @(posedge clk) begin
        ce_buf <= ce_in;
        if(ce_in) begin
            {% for ib in input_buffers %}
            {{ ib[0] }} <= { {(SW-IW-SF+IF){ {{ ib[1] }}[IW-1]}}, {{ ib[1] }}, {(SF-IF){1'b0}} };
            {% endfor %}
            {% for sb in state_buffers %}
            {{ sb[0] }} <= {{ sb[1] }}[SW+CF-1:CF];
            {% endfor %}
        end 
    end

    /**************************************************************************
    * The multiplication operations.
    **************************************************************************/
    always @(posedge clk) begin
        ce_mul <= ce_buf;
        {% for p in A_prods %}
        {{ p["o"] }} <= {{ p["a"] }} * {{ p["b"] }};
        {% endfor %}
        {% for p in B_prods %}
        {{ p["o"] }} <= {{ p["a"] }} * {{ p["b"] }};
        {% endfor %}
        {% for p in C_prods %}
        {{ p["o"] }} <= {{ p["a"] }} * {{ p["b"] }};
        {% endfor %}
        {% for p in D_prods %}
        {{ p["o"] }} <= {{ p["a"] }} * {{ p["b"] }};
        {% endfor %}
    end


    /**************************************************************************
    * The adder.
    **************************************************************************/
    always @(posedge clk) begin
        {% for exp in adder_ce %}
        {{ exp[0] }} <= {{ exp[1] }};
        {% endfor %}
        {% for exp in state_adders %}
        {{ exp[0] }} <= {{ exp[1] }};
        {% endfor %}
        {% for exp in output_adders %}
        {{ exp[0] }} <= {{ exp[1] }};
        {% endfor %}
    end
    
    /**************************************************************************
    * The delta/shift operator.
    **************************************************************************/
    always @(posedge clk) begin
        if(ce_out) begin
            {% for d in deltas %}
            {% if del is not none %}
            {{ d[0] }} <= {{ d[0] }} + { {(DEL){ {{ d[1] }}[RW-1]}}, {{ d[1] }}[RW-1:DEL] };
            {% else %}
            {{ d[0] }} <= {{ d[1] }};
            {% endif %}
            {% endfor %}
        end 
    end
  
    /**************************************************************************
    * Quantization of system outputs.
    **************************************************************************/
    {% for o in outputs %}
    assign {{ o[0] }} = {{ o[1] }}[OW+CF-1:CF];
    {% endfor %}
    
    initial begin
        {% for s in sig_u %}
        {{ s }} = 0;
        {% endfor %}
        {% for s in sig_x %}
        {{ s }} = 0;
        {% endfor %}
        {% for s in sig_x_long %}
        {{ s }} = 0;
        {% endfor %}
        {% for s in sig_dx %}
        {{ s }} = 0;
        {% endfor %}
        {% for s in A_sig_prod %}
        {{ s }} = 0;
        {% endfor %}
        {% for s in B_sig_prod %}
        {{ s }} = 0;
        {% endfor %}
        {% for s in C_sig_prod %}
        {{ s }} = 0;
        {% endfor %}
        {% for s in D_sig_prod %}
        {{ s }} = 0;
        {% endfor %}
    end

endmodule