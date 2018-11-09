/******************************************************************************
* If ki is the integral gain of the analog controller, KI = ki*Ts/2 is the gain
* of the digital control where Ts is the sampling period.
******************************************************************************/
module example_integrator (clk, ce_in, sig_in, ce_out, sig_out);

    parameter DW = 24;          // data word length
    parameter CW = 16;          // coefficient word length
    parameter CF = 16;          // coefficient fractional length
    parameter IW = DW + CW;
    parameter signed [CW-1:0] KI = 16'sd98;              
    parameter signed [IW-1:0] MAX = 40'sd412316860416;
    parameter signed [IW-1:0] MIN = -40'sd412316860416;

    
    input wire clk; 
    input wire ce_in;
    input wire signed [DW-1:0] sig_in;
    output reg ce_out = 0;
    output wire signed [DW-1:0] sig_out;
    
    reg ce_buf = 0;
    wire overflow;
    reg signed [DW-1:0] un = 0;
    reg signed [IW-1:0] yn = 0;
    reg signed [IW-1:0] xn = 0;
    wire signed [IW-1:0] kiun, yn_ovf; 
    
    /**************************************************************************
    * Input buffer.
    **************************************************************************/
    always @(posedge clk) begin   
        ce_buf <= ce_in;
        if (ce_in)  un <= sig_in;
    end

    /**************************************************************************
    * Trapezoidal rule.
    **************************************************************************/
    assign kiun = KI * un;
    assign yn_ovf = yn + xn + kiun;
    assign overflow = (yn_ovf > MAX) | (yn_ovf < MIN);
    
    always @(posedge clk) begin
        ce_out <= ce_buf;
        if (ce_buf) xn <= kiun; 
        if (ce_buf) yn <= overflow ? yn : yn_ovf;
    end
    
    assign sig_out = yn[DW+CF-1:CF];
    
endmodule