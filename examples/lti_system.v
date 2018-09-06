module lti_system #
(
    parameter signed [CW-1:0] A1_1 = -1018, 
    parameter signed [CW-1:0] A1_2 = 3793, 
    parameter signed [CW-1:0] A1_3 = 1504, 
    parameter signed [CW-1:0] A1_4 = 567, 
    parameter signed [CW-1:0] A2_1 = -3793, 
    parameter signed [CW-1:0] A2_2 = -4632, 
    parameter signed [CW-1:0] A2_3 = -6949, 
    parameter signed [CW-1:0] A2_4 = -2057, 
    parameter signed [CW-1:0] A3_1 = 1504, 
    parameter signed [CW-1:0] A3_2 = 6949, 
    parameter signed [CW-1:0] A3_3 = -11454, 
    parameter signed [CW-1:0] A3_4 = -8731, 
    parameter signed [CW-1:0] A4_1 = -567, 
    parameter signed [CW-1:0] A4_2 = -2057, 
    parameter signed [CW-1:0] A4_3 = 8731, 
    parameter signed [CW-1:0] A4_4 = -22406, 
    parameter signed [CW-1:0] B1_1 = 6834, 
    parameter signed [CW-1:0] B2_1 = 8451, 
    parameter signed [CW-1:0] B3_1 = -5322, 
    parameter signed [CW-1:0] B4_1 = 1897, 
    parameter signed [CW-1:0] C1_1 = 6834, 
    parameter signed [CW-1:0] C1_2 = -8451, 
    parameter signed [CW-1:0] C1_3 = -5322, 
    parameter signed [CW-1:0] C1_4 = -1897, 
    parameter signed [CW-1:0] D1_1 = 0, 
    parameter IW = 16,
    parameter OW = 16,
    parameter CW = 16,
    parameter SW = 25,
    parameter RW = SW + CW - 1,
    parameter CF = 15,
    parameter DEL = 10
)
(
    input wire [IW-1:0] sig_in1, 
    output wire [OW-1:0] sig_out1, 
    input wire clk,
    input wire ce_in,
    output reg ce_out
);

    reg ce_mul;
    reg ce_buf;
    reg signed [SW-1:0] u1;
    reg signed [SW-1:0] x1;
    reg signed [SW-1:0] x2;
    reg signed [SW-1:0] x3;
    reg signed [SW-1:0] x4;
    reg signed [RW-1:0] x_long1;
    reg signed [RW-1:0] x_long2;
    reg signed [RW-1:0] x_long3;
    reg signed [RW-1:0] x_long4;
    reg signed [RW-1:0] dx1;
    reg signed [RW-1:0] dx2;
    reg signed [RW-1:0] dx3;
    reg signed [RW-1:0] dx4;
    reg signed [RW-1:0] y_long1;
    reg signed [RW-1:0] ax1_1;
    reg signed [RW-1:0] ax1_2;
    reg signed [RW-1:0] ax1_3;
    reg signed [RW-1:0] ax1_4;
    reg signed [RW-1:0] ax2_1;
    reg signed [RW-1:0] ax2_2;
    reg signed [RW-1:0] ax2_3;
    reg signed [RW-1:0] ax2_4;
    reg signed [RW-1:0] ax3_1;
    reg signed [RW-1:0] ax3_2;
    reg signed [RW-1:0] ax3_3;
    reg signed [RW-1:0] ax3_4;
    reg signed [RW-1:0] ax4_1;
    reg signed [RW-1:0] ax4_2;
    reg signed [RW-1:0] ax4_3;
    reg signed [RW-1:0] ax4_4;
    reg signed [RW-1:0] bu1_1;
    reg signed [RW-1:0] bu2_1;
    reg signed [RW-1:0] bu3_1;
    reg signed [RW-1:0] bu4_1;
    reg signed [RW-1:0] cx1_1;
    reg signed [RW-1:0] cx1_2;
    reg signed [RW-1:0] cx1_3;
    reg signed [RW-1:0] cx1_4;
    reg signed [RW-1:0] du1_1;
    
    /**************************************************************************
    * The input and quantized state buffer.
    **************************************************************************/
    always @(posedge clk) begin
        ce_buf <= ce_in;
        if(ce_in) begin
            u1 <= $signed(sig_in1)
            x1 <= x_long1[SW+CF-1:CF];
            x2 <= x_long2[SW+CF-1:CF];
            x3 <= x_long3[SW+CF-1:CF];
            x4 <= x_long4[SW+CF-1:CF];
        end 
    end

    /**************************************************************************
    * The multiplication operations.
    **************************************************************************/
    always @(posedge clk) begin
        ce_mul <= ce_buf;
        ax1_1 <= A1_1 * x1 
        ax1_2 <= A1_2 * x2 
        ax1_3 <= A1_3 * x3 
        ax1_4 <= A1_4 * x4 
        ax2_1 <= A2_1 * x1 
        ax2_2 <= A2_2 * x2 
        ax2_3 <= A2_3 * x3 
        ax2_4 <= A2_4 * x4 
        ax3_1 <= A3_1 * x1 
        ax3_2 <= A3_2 * x2 
        ax3_3 <= A3_3 * x3 
        ax3_4 <= A3_4 * x4 
        ax4_1 <= A4_1 * x1 
        ax4_2 <= A4_2 * x2 
        ax4_3 <= A4_3 * x3 
        ax4_4 <= A4_4 * x4 
        bu1_1 <= B1_1 * u1 
        bu2_1 <= B2_1 * u1 
        bu3_1 <= B3_1 * u1 
        bu4_1 <= B4_1 * u1 
        cx1_1 <= C1_1 * x1 
        cx1_2 <= C1_2 * x2 
        cx1_3 <= C1_3 * x3 
        cx1_4 <= C1_4 * x4 
        du1_1 <= D1_1 * u1 
    end


    /**************************************************************************
    * The adder.
    **************************************************************************/
    always @(posedge clk) begin
        sum000 <= ax1_1 + ax1_2 + ax1_3
        sum001 <= ax1_4 + bu1_1
        dx1 <= sum000 + sum001
        sum100 <= ax2_1 + ax2_2 + ax2_3
        sum101 <= ax2_4 + bu2_1
        dx2 <= sum100 + sum101
        sum200 <= ax3_1 + ax3_2 + ax3_3
        sum201 <= ax3_4 + bu3_1
        dx3 <= sum200 + sum201
        sum300 <= ax4_1 + ax4_2 + ax4_3
        sum301 <= ax4_4 + bu4_1
        dx4 <= sum300 + sum301
        sum400 <= cx1_1 + cx1_2 + cx1_3
        sum401 <= cx1_4 + du1_1
        y_long1 <= sum400 + sum401
    end
    
    /**************************************************************************
    * The delta operator.
    **************************************************************************/
    always @(posedge clk) begin
        if(ce_out) begin
            x_long1 <= x_long1 + $signed(dx1[RX-1:DEL]);
            x_long2 <= x_long2 + $signed(dx2[RX-1:DEL]);
            x_long3 <= x_long3 + $signed(dx3[RX-1:DEL]);
            x_long4 <= x_long4 + $signed(dx4[RX-1:DEL]);
        end 
    end
  
    /**************************************************************************
    * Quantization of system outputs.
    **************************************************************************/
    assign sig_out1 = y_long1[OW+CF-1:CF]
    
    initial begin
        u1 = 0;
        x1 = 0;
        x2 = 0;
        x3 = 0;
        x4 = 0;
        x_long1 = 0;
        x_long2 = 0;
        x_long3 = 0;
        x_long4 = 0;
        dx1 = 0;
        dx2 = 0;
        dx3 = 0;
        dx4 = 0;
        ax1_1 = 0;
        ax1_2 = 0;
        ax1_3 = 0;
        ax1_4 = 0;
        ax2_1 = 0;
        ax2_2 = 0;
        ax2_3 = 0;
        ax2_4 = 0;
        ax3_1 = 0;
        ax3_2 = 0;
        ax3_3 = 0;
        ax3_4 = 0;
        ax4_1 = 0;
        ax4_2 = 0;
        ax4_3 = 0;
        ax4_4 = 0;
        bu1_1 = 0;
        bu2_1 = 0;
        bu3_1 = 0;
        bu4_1 = 0;
        cx1_1 = 0;
        cx1_2 = 0;
        cx1_3 = 0;
        cx1_4 = 0;
        du1_1 = 0;
    end

endmodule