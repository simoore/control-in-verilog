module saturation #
(
    parameter IW = 22,
    parameter OW = 16
) 
(
    input wire [IW-1:0] sig_in,
    output wire [OW-1:0] sig_out
);
    
    localparam [OW-1:0] MAX = { 1'b0, {(OW-1){1'b1}} };
    localparam [OW-1:0] MIN = { 1'b1, {(OW-1){1'b0}} };
    
    wire [IW-OW-1:0] top;
    wire overflow_max;
    wire overflow_min;
    
    assign top = sig_in[IW-2:OW-1];
    assign overflow_max = (sig_in[IW-1] == 0) && (|top == 1);
    assign overflow_min = (sig_in[IW-1] == 1) && (&top == 0);
    assign sig_out = overflow_max ?  MAX : overflow_min ? MIN : sig_in;
    
endmodule
