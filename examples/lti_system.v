module lti_system #
(
    parameter signed [CW-1:0] A_1_1 = -1018, 
    parameter signed [CW-1:0] A_1_2 = 3793, 
    parameter signed [CW-1:0] A_1_3 = 1504, 
    parameter signed [CW-1:0] A_1_4 = 567, 
    parameter signed [CW-1:0] A_2_1 = -3793, 
    parameter signed [CW-1:0] A_2_2 = -4632, 
    parameter signed [CW-1:0] A_2_3 = -6949, 
    parameter signed [CW-1:0] A_2_4 = -2057, 
    parameter signed [CW-1:0] A_3_1 = 1504, 
    parameter signed [CW-1:0] A_3_2 = 6949, 
    parameter signed [CW-1:0] A_3_3 = -11454, 
    parameter signed [CW-1:0] A_3_4 = -8731, 
    parameter signed [CW-1:0] A_4_1 = -567, 
    parameter signed [CW-1:0] A_4_2 = -2057, 
    parameter signed [CW-1:0] A_4_3 = 8731, 
    parameter signed [CW-1:0] A_4_4 = -22406, 
    parameter signed [CW-1:0] B_1_1 = 6834, 
    parameter signed [CW-1:0] B_2_1 = 8451, 
    parameter signed [CW-1:0] B_3_1 = -5322, 
    parameter signed [CW-1:0] B_4_1 = 1897, 
    parameter signed [CW-1:0] C_1_1 = 6834, 
    parameter signed [CW-1:0] C_1_2 = -8451, 
    parameter signed [CW-1:0] C_1_3 = -5322, 
    parameter signed [CW-1:0] C_1_4 = -1897, 
    parameter signed [CW-1:0] D_1_1 = 0, 
    parameter IW = 16,
    parameter OW = 16,
    parameter CW = 16,
    parameter SW = 25,
    parameter RW = SW + CW - 1,
    parameter CF = 15,
    parameter DEL = 10
)
(
    input wire [IW-1:0] sig_in_1, 
    output wire [OW-1:0] sig_out_1, 
    input wire clk,
    input wire ce_in,
    output reg ce_out
);

    reg ce_mul;
    reg ce_buf;
    reg signed [SW-1:0] u_1;
    reg signed [SW-1:0] x_1;
    reg signed [SW-1:0] x_2;
    reg signed [SW-1:0] x_3;
    reg signed [SW-1:0] x_4;
    reg signed [RW-1:0] x_long_1;
    reg signed [RW-1:0] x_long_2;
    reg signed [RW-1:0] x_long_3;
    reg signed [RW-1:0] x_long_4;
    reg signed [RW-1:0] dx_1;
    reg signed [RW-1:0] dx_2;
    reg signed [RW-1:0] dx_3;
    reg signed [RW-1:0] dx_4;
    reg signed [RW-1:0] y_long_1;
    reg signed [RW-1:0] ax_1_1;
    reg signed [RW-1:0] ax_1_2;
    reg signed [RW-1:0] ax_1_3;
    reg signed [RW-1:0] ax_1_4;
    reg signed [RW-1:0] ax_2_1;
    reg signed [RW-1:0] ax_2_2;
    reg signed [RW-1:0] ax_2_3;
    reg signed [RW-1:0] ax_2_4;
    reg signed [RW-1:0] ax_3_1;
    reg signed [RW-1:0] ax_3_2;
    reg signed [RW-1:0] ax_3_3;
    reg signed [RW-1:0] ax_3_4;
    reg signed [RW-1:0] ax_4_1;
    reg signed [RW-1:0] ax_4_2;
    reg signed [RW-1:0] ax_4_3;
    reg signed [RW-1:0] ax_4_4;
    reg signed [RW-1:0] bu_1_1;
    reg signed [RW-1:0] bu_2_1;
    reg signed [RW-1:0] bu_3_1;
    reg signed [RW-1:0] bu_4_1;
    reg signed [RW-1:0] cx_1_1;
    reg signed [RW-1:0] cx_1_2;
    reg signed [RW-1:0] cx_1_3;
    reg signed [RW-1:0] cx_1_4;
    reg signed [RW-1:0] du_1_1;
    
    reg signed [RW-1:0] sumS_0_0_0;
    reg signed [RW-1:0] sumS_0_0_1;
    reg signed [RW-1:0] sumS_1_0_0;
    reg signed [RW-1:0] sumS_1_0_1;
    reg signed [RW-1:0] sumS_2_0_0;
    reg signed [RW-1:0] sumS_2_0_1;
    reg signed [RW-1:0] sumS_3_0_0;
    reg signed [RW-1:0] sumS_3_0_1;
    reg signed [RW-1:0] sumO_0_0_0;
    reg signed [RW-1:0] sumO_0_0_1;
    
    /**************************************************************************
    * The input and quantized state buffer.
    **************************************************************************/
    always @(posedge clk) begin
        ce_buf <= ce_in;
        if(ce_in) begin
            u_1 <= $signed(sig_in_1)
            x_1 <= x_long_1[SW+CF-1:CF];
            x_2 <= x_long_2[SW+CF-1:CF];
            x_3 <= x_long_3[SW+CF-1:CF];
            x_4 <= x_long_4[SW+CF-1:CF];
        end 
    end

    /**************************************************************************
    * The multiplication operations.
    **************************************************************************/
    always @(posedge clk) begin
        ce_mul <= ce_buf;
        ax_1_1 <= A_1_1 * x_1 
        ax_1_2 <= A_1_2 * x_2 
        ax_1_3 <= A_1_3 * x_3 
        ax_1_4 <= A_1_4 * x_4 
        ax_2_1 <= A_2_1 * x_1 
        ax_2_2 <= A_2_2 * x_2 
        ax_2_3 <= A_2_3 * x_3 
        ax_2_4 <= A_2_4 * x_4 
        ax_3_1 <= A_3_1 * x_1 
        ax_3_2 <= A_3_2 * x_2 
        ax_3_3 <= A_3_3 * x_3 
        ax_3_4 <= A_3_4 * x_4 
        ax_4_1 <= A_4_1 * x_1 
        ax_4_2 <= A_4_2 * x_2 
        ax_4_3 <= A_4_3 * x_3 
        ax_4_4 <= A_4_4 * x_4 
        bu_1_1 <= B_1_1 * u_1 
        bu_2_1 <= B_2_1 * u_1 
        bu_3_1 <= B_3_1 * u_1 
        bu_4_1 <= B_4_1 * u_1 
        cx_1_1 <= C_1_1 * x_1 
        cx_1_2 <= C_1_2 * x_2 
        cx_1_3 <= C_1_3 * x_3 
        cx_1_4 <= C_1_4 * x_4 
        du_1_1 <= D_1_1 * u_1 
    end


    /**************************************************************************
    * The adder.
    **************************************************************************/
    always @(posedge clk) begin
        ce_add_1 <= ce_mul
        ce_out <= ce_add_1
        sumS_0_0_0 <= ax_1_1 + ax_1_2 + ax_1_3
        sumS_0_0_1 <= ax_1_4 + bu_1_1
        dx_1 <= sumS_0_0_0 + sumS_0_0_1
        sumS_1_0_0 <= ax_2_1 + ax_2_2 + ax_2_3
        sumS_1_0_1 <= ax_2_4 + bu_2_1
        dx_2 <= sumS_1_0_0 + sumS_1_0_1
        sumS_2_0_0 <= ax_3_1 + ax_3_2 + ax_3_3
        sumS_2_0_1 <= ax_3_4 + bu_3_1
        dx_3 <= sumS_2_0_0 + sumS_2_0_1
        sumS_3_0_0 <= ax_4_1 + ax_4_2 + ax_4_3
        sumS_3_0_1 <= ax_4_4 + bu_4_1
        dx_4 <= sumS_3_0_0 + sumS_3_0_1
        sumO_0_0_0 <= cx_1_1 + cx_1_2 + cx_1_3
        sumO_0_0_1 <= cx_1_4 + du_1_1
        y_long_1 <= sumO_0_0_0 + sumO_0_0_1
    end
    
    /**************************************************************************
    * The delta operator.
    **************************************************************************/
    always @(posedge clk) begin
        if(ce_out) begin
            x_long_1 <= x_long_1 + $signed(dx_1[RX-1:DEL]);
            x_long_2 <= x_long_2 + $signed(dx_2[RX-1:DEL]);
            x_long_3 <= x_long_3 + $signed(dx_3[RX-1:DEL]);
            x_long_4 <= x_long_4 + $signed(dx_4[RX-1:DEL]);
        end 
    end
  
    /**************************************************************************
    * Quantization of system outputs.
    **************************************************************************/
    assign sig_out_1 = y_long_1[OW+CF-1:CF]
    
    initial begin
        u_1 = 0;
        x_1 = 0;
        x_2 = 0;
        x_3 = 0;
        x_4 = 0;
        x_long_1 = 0;
        x_long_2 = 0;
        x_long_3 = 0;
        x_long_4 = 0;
        dx_1 = 0;
        dx_2 = 0;
        dx_3 = 0;
        dx_4 = 0;
        ax_1_1 = 0;
        ax_1_2 = 0;
        ax_1_3 = 0;
        ax_1_4 = 0;
        ax_2_1 = 0;
        ax_2_2 = 0;
        ax_2_3 = 0;
        ax_2_4 = 0;
        ax_3_1 = 0;
        ax_3_2 = 0;
        ax_3_3 = 0;
        ax_3_4 = 0;
        ax_4_1 = 0;
        ax_4_2 = 0;
        ax_4_3 = 0;
        ax_4_4 = 0;
        bu_1_1 = 0;
        bu_2_1 = 0;
        bu_3_1 = 0;
        bu_4_1 = 0;
        cx_1_1 = 0;
        cx_1_2 = 0;
        cx_1_3 = 0;
        cx_1_4 = 0;
        du_1_1 = 0;
    end

endmodule