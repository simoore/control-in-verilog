module example_lti_system #
(
    parameter CW = 10,
    parameter signed [CW-1:0] A_1_1 = -16, 
    parameter signed [CW-1:0] A_1_2 = 59, 
    parameter signed [CW-1:0] A_1_3 = 24, 
    parameter signed [CW-1:0] A_1_4 = 9, 
    parameter signed [CW-1:0] A_2_1 = -59, 
    parameter signed [CW-1:0] A_2_2 = -72, 
    parameter signed [CW-1:0] A_2_3 = -109, 
    parameter signed [CW-1:0] A_2_4 = -32, 
    parameter signed [CW-1:0] A_3_1 = 24, 
    parameter signed [CW-1:0] A_3_2 = 109, 
    parameter signed [CW-1:0] A_3_3 = -179, 
    parameter signed [CW-1:0] A_3_4 = -136, 
    parameter signed [CW-1:0] A_4_1 = -9, 
    parameter signed [CW-1:0] A_4_2 = -32, 
    parameter signed [CW-1:0] A_4_3 = 136, 
    parameter signed [CW-1:0] A_4_4 = -350, 
    parameter signed [CW-1:0] B_1_1 = 107, 
    parameter signed [CW-1:0] B_2_1 = 132, 
    parameter signed [CW-1:0] B_3_1 = -83, 
    parameter signed [CW-1:0] B_4_1 = 30, 
    parameter signed [CW-1:0] C_1_1 = 107, 
    parameter signed [CW-1:0] C_1_2 = -132, 
    parameter signed [CW-1:0] C_1_3 = -83, 
    parameter signed [CW-1:0] C_1_4 = -30, 
    parameter signed [CW-1:0] D_1_1 = 0, 
    parameter IW = 16,
    parameter OW = 20,
    parameter SW = 22,
    parameter CF = 9,
    parameter SF = 18,
    parameter IF = 14,
    parameter DEL = 10,
    parameter RW = SW + CW - 1
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
    reg ce_add_1;

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
            u_1 <= { {(SW-IW-SF+IF){ sig_in_1[IW-1]}}, sig_in_1, {(SF-IF){1'b0}} };
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
        ax_1_1 <= A_1_1 * x_1;
        ax_1_2 <= A_1_2 * x_2;
        ax_1_3 <= A_1_3 * x_3;
        ax_1_4 <= A_1_4 * x_4;
        ax_2_1 <= A_2_1 * x_1;
        ax_2_2 <= A_2_2 * x_2;
        ax_2_3 <= A_2_3 * x_3;
        ax_2_4 <= A_2_4 * x_4;
        ax_3_1 <= A_3_1 * x_1;
        ax_3_2 <= A_3_2 * x_2;
        ax_3_3 <= A_3_3 * x_3;
        ax_3_4 <= A_3_4 * x_4;
        ax_4_1 <= A_4_1 * x_1;
        ax_4_2 <= A_4_2 * x_2;
        ax_4_3 <= A_4_3 * x_3;
        ax_4_4 <= A_4_4 * x_4;
        bu_1_1 <= B_1_1 * u_1;
        bu_2_1 <= B_2_1 * u_1;
        bu_3_1 <= B_3_1 * u_1;
        bu_4_1 <= B_4_1 * u_1;
        cx_1_1 <= C_1_1 * x_1;
        cx_1_2 <= C_1_2 * x_2;
        cx_1_3 <= C_1_3 * x_3;
        cx_1_4 <= C_1_4 * x_4;
        du_1_1 <= D_1_1 * u_1;
    end


    /**************************************************************************
    * The adder.
    **************************************************************************/
    always @(posedge clk) begin
        ce_add_1 <= ce_mul;
        ce_out <= ce_add_1;
        sumS_0_0_0 <= ax_1_1 + ax_1_2 + ax_1_3;
        sumS_0_0_1 <= ax_1_4 + bu_1_1;
        dx_1 <= sumS_0_0_0 + sumS_0_0_1;
        sumS_1_0_0 <= ax_2_1 + ax_2_2 + ax_2_3;
        sumS_1_0_1 <= ax_2_4 + bu_2_1;
        dx_2 <= sumS_1_0_0 + sumS_1_0_1;
        sumS_2_0_0 <= ax_3_1 + ax_3_2 + ax_3_3;
        sumS_2_0_1 <= ax_3_4 + bu_3_1;
        dx_3 <= sumS_2_0_0 + sumS_2_0_1;
        sumS_3_0_0 <= ax_4_1 + ax_4_2 + ax_4_3;
        sumS_3_0_1 <= ax_4_4 + bu_4_1;
        dx_4 <= sumS_3_0_0 + sumS_3_0_1;
        sumO_0_0_0 <= cx_1_1 + cx_1_2 + cx_1_3;
        sumO_0_0_1 <= cx_1_4 + du_1_1;
        y_long_1 <= sumO_0_0_0 + sumO_0_0_1;
    end
    
    /**************************************************************************
    * The delta/shift operator.
    **************************************************************************/
    always @(posedge clk) begin
        if(ce_out) begin
            x_long_1 <= x_long_1 + { {(DEL){ dx_1[RW-1]}}, dx_1[RW-1:DEL] };
            x_long_2 <= x_long_2 + { {(DEL){ dx_2[RW-1]}}, dx_2[RW-1:DEL] };
            x_long_3 <= x_long_3 + { {(DEL){ dx_3[RW-1]}}, dx_3[RW-1:DEL] };
            x_long_4 <= x_long_4 + { {(DEL){ dx_4[RW-1]}}, dx_4[RW-1:DEL] };
        end 
    end
  
    /**************************************************************************
    * Quantization of system outputs.
    **************************************************************************/
    assign sig_out_1 = y_long_1[OW+CF-1:CF];
    
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