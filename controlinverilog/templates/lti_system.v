module {{ name }} #
(
    {% for p in params %}
    parameter signed [CW-1:0] {{ p["name"] }} = {{ p["value"] }}, 
    {% endfor %}
    parameter IW = {{ iw }},
    parameter OW = {{ ow }},
    parameter CW = {{ cw }},
    parameter SW = {{ sw }},
    parameter RW = SW + CW - 1,
    parameter CF = {{ cf }},
    parameter DEL = {{ del }}
)
(
    {% for i in sig_ins %}
    input wire [IW-1:0] {{ i }}, 
    {% endfor %}
    {% for o in sig_outs %}
    output wire [OW-1:0] {{ o }}, 
    {% endfor %}
    input wire clk,
    input wire ce_in,
    output reg ce_out
);

    reg ce_mul;
    reg ce_buf;
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
    {% for s in sig_prods %}
    reg signed [RW-1:0] {{ s }};
    {% endfor %}
    
    /**************************************************************************
    * The input and quantized state buffer.
    **************************************************************************/
    always @(posedge clk) begin
        ce_buf <= ce_in;
        if(ce_in) begin
            {% for ib in input_buffers %}
            {{ ib[0] }} <= $signed({{ ib[1] }})
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
        {% for p in prods %}
        {{ p["o"] }} <= {{ p["a"] }} * {{ p["b"] }} 
        {% endfor %}
    end


    /**************************************************************************
    * The addition pipeline.
    **************************************************************************/
    always @(posedge clk) begin
        {% for stage in adder %}
        {% for exp in stage %}
        {{ exp[0] }} <= {{ exp[1] }}
        {% endfor %}
    
        {% endfor %}
    end


    /**************************************************************************
    * The delta operator.
    **************************************************************************/
    always @(posedge clk) begin
        if(ce_out) begin
            {% for d in deltas %}
            {{ d[0] }} <= {{ d[0] }} + $signed({{ d[1] }}[RX-1:DEL]);
            {% endfor %}
        end 
    end
  
    /**************************************************************************
    * Quantization of system outputs.
    **************************************************************************/
    {% for o in outputs %}
    assign {{ o[0] }} = {{ o[1] }}[OW+CF-1:CF]
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
        {% for s in sig_prods %}
        {{ s }} = 0;
        {% endfor %}
    end

endmodule