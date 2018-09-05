module modulator_dds 
(
    input wire clk, 
    input wire rst, 
    input wire ce_in, 
    input wire [23:0] freqword,
    input wire [23:0] phase_offset,
    output reg ce_out = 0, 
    output reg signed [15:0] sin = 0, 
    output reg signed [15:0] cos = 0
);
        
    wire quad;
    reg rst_lcl = 0;
    reg ce_dds = 0;
    reg ce_lut = 0;
    reg ce_adj = 0; 
    reg ce_sho = 0; 
    reg ce_sin = 0;
    reg [6:0] fine_lut[63:0];
    reg [9:0] sin_lut[255:0];
    wire [23:0] phase;
    wire [5:0] fine_addr;
    wire [7:0] sin_addr;
    wire [7:0] cos_addr;
    reg [23:0] phase_reg = 0;
    reg signed [10:0] sin_short = 0;  // 10 frac bits 
    reg signed [10:0] cos_short = 0;  // 10 frac bits
    reg signed [10:0] sin_abs = 0;	  // 10 frac bits
    reg signed [10:0] cos_abs = 0;    // 10 frac bits
    reg signed [7:0] fine = 0;        // 14 frac bits
    wire signed [24:0] sin_long;		  // 24 frac bits
    wire signed [24:0] cos_long;      // 24 frac bits
    reg signed [24:0] sin_adj = 0;	  // 24 frac bits
    reg signed [24:0] cos_adj = 0;    // 24 frac bits
    
    /**************************************************************************
    * Local reset.
    **************************************************************************/
    always @(posedge clk) 
        rst_lcl <= rst;
    
    /**************************************************************************
    * Direct digital synthesiser:  http://www.fpga4fun.com/DDS.html
    * The phase accumulator is 24 bit.
    * The frequency is given by:   f = freqword/2^24 * f_exe
    **************************************************************************/
    always @(posedge clk) begin
        ce_dds <= ce_in;
        if (rst_lcl)        phase_reg <= 0;
        else if (ce_in)     phase_reg <= phase_reg + freqword;
    end
    
    assign phase = phase_reg + phase_offset;
    assign sin_addr = phase[22] ? ~phase[21:14] : phase[21:14];
    assign cos_addr = phase[22] ? phase[21:14] : ~phase[21:14];
    assign fine_addr = phase[13:8];
    
    always @(posedge clk) begin
        ce_lut <= ce_dds;
        if (rst_lcl)        sin_abs <= {1'b0,sin_lut[0]};
        else if (ce_dds)    sin_abs <= {1'b0,sin_lut[sin_addr]};
        if (rst_lcl)        cos_abs <= {1'b0,sin_lut[0]};
        else if (ce_dds)    cos_abs <= {1'b0,sin_lut[cos_addr]};
        if (rst_lcl)        fine <= {1'b0,fine_lut[0]};
        else if (ce_dds)    fine <= {1'b0,fine_lut[fine_addr]};
    end

    /**************************************************************************
    * Interpolation increases the purity of the DDS sine wave. Circular 
    * interpolation using the following trig identities.
    *      sin(x+y) = sin(x)cos(y) + cos(x)sin(y)
    *      cos(x+y) = cos(x)cos(y) - sin(x)sin(y)
    * x is the course angle taken as bit 15:6 of the phase, while y is the fine
    * angle taken as bit 5:0 of the phase. To simplify, the approximation is
    * used for the fine angle cos(y) ~ 1.
    * Reference.
    *      A digital frequency synthesizer by Tierney, Rader and Gold in 
    *      IEEE Transactions on Audio and Electroacoustics (1971)
    **************************************************************************/
    assign quad = phase[23] ^ phase[22];
    always @(posedge clk) begin
        ce_sho <= ce_lut;
        if (rst_lcl)        sin_short <= 0;
        else if (ce_lut)    sin_short <= phase[23] ? -sin_abs : sin_abs;
        if (rst_lcl)        cos_short <= 0;
        else if (ce_lut)    cos_short <= quad ? -cos_abs : cos_abs;
    end

    always @(posedge clk) begin
        ce_adj <= ce_sho;
        if (rst_lcl)        sin_adj <= 0;
        else if (ce_sho)    sin_adj <= fine*cos_short;
        if (rst_lcl)        cos_adj <= 0;
        else if (ce_sho)    cos_adj <= fine*sin_short;
    end
                
    assign sin_long = {sin_short,14'b0} + sin_adj;
    assign cos_long = {cos_short,14'b0} - cos_adj;
        
    always @(posedge clk) begin
        ce_out <= ce_adj;
        if (rst_lcl)        sin <= 0;
        else if (ce_adj)    sin <= sin_long[24:9];
        if (rst_lcl)        cos <= 0;
        else if (ce_adj)    cos <= cos_long[24:9];
    end
                          
    /**************************************************************************
    * Sine lookup table. 8 bit address representing the phase [0,pi/2]. The 
    * amplitude resolution is 10 bit with the [0,1023] range representing
    * [0,1]. The fine lookup table has a 6 bit address representing
    * the phase [0,pi/512] to more finely tune the accuracy of the DDS. It
    * has an amplitude of [0,101] representing the magnitude [0,0.0061359].
    **************************************************************************/
    initial begin
        sin_lut[0] = 10'd0;
        sin_lut[1] = 10'd6;
        sin_lut[2] = 10'd13;
        sin_lut[3] = 10'd19;
        sin_lut[4] = 10'd25;
        sin_lut[5] = 10'd32;
        sin_lut[6] = 10'd38;
        sin_lut[7] = 10'd44;
        sin_lut[8] = 10'd50;
        sin_lut[9] = 10'd57;
        sin_lut[10] = 10'd63;
        sin_lut[11] = 10'd69;
        sin_lut[12] = 10'd76;
        sin_lut[13] = 10'd82;
        sin_lut[14] = 10'd88;
        sin_lut[15] = 10'd94;
        sin_lut[16] = 10'd101;
        sin_lut[17] = 10'd107;
        sin_lut[18] = 10'd113;
        sin_lut[19] = 10'd120;
        sin_lut[20] = 10'd126;
        sin_lut[21] = 10'd132;
        sin_lut[22] = 10'd138;
        sin_lut[23] = 10'd145;
        sin_lut[24] = 10'd151;
        sin_lut[25] = 10'd157;
        sin_lut[26] = 10'd163;
        sin_lut[27] = 10'd170;
        sin_lut[28] = 10'd176;
        sin_lut[29] = 10'd182;
        sin_lut[30] = 10'd188;
        sin_lut[31] = 10'd194;
        sin_lut[32] = 10'd201;
        sin_lut[33] = 10'd207;
        sin_lut[34] = 10'd213;
        sin_lut[35] = 10'd219;
        sin_lut[36] = 10'd225;
        sin_lut[37] = 10'd231;
        sin_lut[38] = 10'd238;
        sin_lut[39] = 10'd244;
        sin_lut[40] = 10'd250;
        sin_lut[41] = 10'd256;
        sin_lut[42] = 10'd262;
        sin_lut[43] = 10'd268;
        sin_lut[44] = 10'd274;
        sin_lut[45] = 10'd280;
        sin_lut[46] = 10'd286;
        sin_lut[47] = 10'd292;
        sin_lut[48] = 10'd298;
        sin_lut[49] = 10'd304;
        sin_lut[50] = 10'd310;
        sin_lut[51] = 10'd316;
        sin_lut[52] = 10'd322;
        sin_lut[53] = 10'd328;
        sin_lut[54] = 10'd334;
        sin_lut[55] = 10'd340;
        sin_lut[56] = 10'd346;
        sin_lut[57] = 10'd352;
        sin_lut[58] = 10'd358;
        sin_lut[59] = 10'd364;
        sin_lut[60] = 10'd370;
        sin_lut[61] = 10'd376;
        sin_lut[62] = 10'd382;
        sin_lut[63] = 10'd387;
        sin_lut[64] = 10'd393;
        sin_lut[65] = 10'd399;
        sin_lut[66] = 10'd405;
        sin_lut[67] = 10'd411;
        sin_lut[68] = 10'd416;
        sin_lut[69] = 10'd422;
        sin_lut[70] = 10'd428;
        sin_lut[71] = 10'd434;
        sin_lut[72] = 10'd439;
        sin_lut[73] = 10'd445;
        sin_lut[74] = 10'd451;
        sin_lut[75] = 10'd456;
        sin_lut[76] = 10'd462;
        sin_lut[77] = 10'd468;
        sin_lut[78] = 10'd473;
        sin_lut[79] = 10'd479;
        sin_lut[80] = 10'd484;
        sin_lut[81] = 10'd490;
        sin_lut[82] = 10'd496;
        sin_lut[83] = 10'd501;
        sin_lut[84] = 10'd507;
        sin_lut[85] = 10'd512;
        sin_lut[86] = 10'd517;
        sin_lut[87] = 10'd523;
        sin_lut[88] = 10'd528;
        sin_lut[89] = 10'd534;
        sin_lut[90] = 10'd539;
        sin_lut[91] = 10'd544;
        sin_lut[92] = 10'd550;
        sin_lut[93] = 10'd555;
        sin_lut[94] = 10'd560;
        sin_lut[95] = 10'd566;
        sin_lut[96] = 10'd571;
        sin_lut[97] = 10'd576;
        sin_lut[98] = 10'd581;
        sin_lut[99] = 10'd586;
        sin_lut[100] = 10'd592;
        sin_lut[101] = 10'd597;
        sin_lut[102] = 10'd602;
        sin_lut[103] = 10'd607;
        sin_lut[104] = 10'd612;
        sin_lut[105] = 10'd617;
        sin_lut[106] = 10'd622;
        sin_lut[107] = 10'd627;
        sin_lut[108] = 10'd632;
        sin_lut[109] = 10'd637;
        sin_lut[110] = 10'd642;
        sin_lut[111] = 10'd647;
        sin_lut[112] = 10'd652;
        sin_lut[113] = 10'd657;
        sin_lut[114] = 10'd661;
        sin_lut[115] = 10'd666;
        sin_lut[116] = 10'd671;
        sin_lut[117] = 10'd676;
        sin_lut[118] = 10'd680;
        sin_lut[119] = 10'd685;
        sin_lut[120] = 10'd690;
        sin_lut[121] = 10'd695;
        sin_lut[122] = 10'd699;
        sin_lut[123] = 10'd704;
        sin_lut[124] = 10'd708;
        sin_lut[125] = 10'd713;
        sin_lut[126] = 10'd717;
        sin_lut[127] = 10'd722;
        sin_lut[128] = 10'd726;
        sin_lut[129] = 10'd731;
        sin_lut[130] = 10'd735;
        sin_lut[131] = 10'd740;
        sin_lut[132] = 10'd744;
        sin_lut[133] = 10'd748;
        sin_lut[134] = 10'd752;
        sin_lut[135] = 10'd757;
        sin_lut[136] = 10'd761;
        sin_lut[137] = 10'd765;
        sin_lut[138] = 10'd769;
        sin_lut[139] = 10'd774;
        sin_lut[140] = 10'd778;
        sin_lut[141] = 10'd782;
        sin_lut[142] = 10'd786;
        sin_lut[143] = 10'd790;
        sin_lut[144] = 10'd794;
        sin_lut[145] = 10'd798;
        sin_lut[146] = 10'd802;
        sin_lut[147] = 10'd806;
        sin_lut[148] = 10'd810;
        sin_lut[149] = 10'd813;
        sin_lut[150] = 10'd817;
        sin_lut[151] = 10'd821;
        sin_lut[152] = 10'd825;
        sin_lut[153] = 10'd828;
        sin_lut[154] = 10'd832;
        sin_lut[155] = 10'd836;
        sin_lut[156] = 10'd839;
        sin_lut[157] = 10'd843;
        sin_lut[158] = 10'd847;
        sin_lut[159] = 10'd850;
        sin_lut[160] = 10'd854;
        sin_lut[161] = 10'd857;
        sin_lut[162] = 10'd861;
        sin_lut[163] = 10'd864;
        sin_lut[164] = 10'd867;
        sin_lut[165] = 10'd871;
        sin_lut[166] = 10'd874;
        sin_lut[167] = 10'd877;
        sin_lut[168] = 10'd880;
        sin_lut[169] = 10'd884;
        sin_lut[170] = 10'd887;
        sin_lut[171] = 10'd890;
        sin_lut[172] = 10'd893;
        sin_lut[173] = 10'd896;
        sin_lut[174] = 10'd899;
        sin_lut[175] = 10'd902;
        sin_lut[176] = 10'd905;
        sin_lut[177] = 10'd908;
        sin_lut[178] = 10'd911;
        sin_lut[179] = 10'd914;
        sin_lut[180] = 10'd917;
        sin_lut[181] = 10'd919;
        sin_lut[182] = 10'd922;
        sin_lut[183] = 10'd925;
        sin_lut[184] = 10'd928;
        sin_lut[185] = 10'd930;
        sin_lut[186] = 10'd933;
        sin_lut[187] = 10'd935;
        sin_lut[188] = 10'd938;
        sin_lut[189] = 10'd941;
        sin_lut[190] = 10'd943;
        sin_lut[191] = 10'd945;
        sin_lut[192] = 10'd948;
        sin_lut[193] = 10'd950;
        sin_lut[194] = 10'd953;
        sin_lut[195] = 10'd955;
        sin_lut[196] = 10'd957;
        sin_lut[197] = 10'd959;
        sin_lut[198] = 10'd962;
        sin_lut[199] = 10'd964;
        sin_lut[200] = 10'd966;
        sin_lut[201] = 10'd968;
        sin_lut[202] = 10'd970;
        sin_lut[203] = 10'd972;
        sin_lut[204] = 10'd974;
        sin_lut[205] = 10'd976;
        sin_lut[206] = 10'd978;
        sin_lut[207] = 10'd980;
        sin_lut[208] = 10'd981;
        sin_lut[209] = 10'd983;
        sin_lut[210] = 10'd985;
        sin_lut[211] = 10'd987;
        sin_lut[212] = 10'd988;
        sin_lut[213] = 10'd990;
        sin_lut[214] = 10'd992;
        sin_lut[215] = 10'd993;
        sin_lut[216] = 10'd995;
        sin_lut[217] = 10'd996;
        sin_lut[218] = 10'd998;
        sin_lut[219] = 10'd999;
        sin_lut[220] = 10'd1000;
        sin_lut[221] = 10'd1002;
        sin_lut[222] = 10'd1003;
        sin_lut[223] = 10'd1004;
        sin_lut[224] = 10'd1005;
        sin_lut[225] = 10'd1007;
        sin_lut[226] = 10'd1008;
        sin_lut[227] = 10'd1009;
        sin_lut[228] = 10'd1010;
        sin_lut[229] = 10'd1011;
        sin_lut[230] = 10'd1012;
        sin_lut[231] = 10'd1013;
        sin_lut[232] = 10'd1014;
        sin_lut[233] = 10'd1015;
        sin_lut[234] = 10'd1015;
        sin_lut[235] = 10'd1016;
        sin_lut[236] = 10'd1017;
        sin_lut[237] = 10'd1018;
        sin_lut[238] = 10'd1018;
        sin_lut[239] = 10'd1019;
        sin_lut[240] = 10'd1020;
        sin_lut[241] = 10'd1020;
        sin_lut[242] = 10'd1021;
        sin_lut[243] = 10'd1021;
        sin_lut[244] = 10'd1022;
        sin_lut[245] = 10'd1022;
        sin_lut[246] = 10'd1022;
        sin_lut[247] = 10'd1023;
        sin_lut[248] = 10'd1023;
        sin_lut[249] = 10'd1023;
        sin_lut[250] = 10'd1023;
        sin_lut[251] = 10'd1023;
        sin_lut[252] = 10'd1023;
        sin_lut[253] = 10'd1023;
        sin_lut[254] = 10'd1023;
        sin_lut[255] = 10'd1023;
        
        fine_lut[0] = 7'd0;
        fine_lut[1] = 7'd2;
        fine_lut[2] = 7'd3;
        fine_lut[3] = 7'd5;
        fine_lut[4] = 7'd6;
        fine_lut[5] = 7'd8;
        fine_lut[6] = 7'd10;
        fine_lut[7] = 7'd11;
        fine_lut[8] = 7'd13;
        fine_lut[9] = 7'd14;
        fine_lut[10] = 7'd16;
        fine_lut[11] = 7'd18;
        fine_lut[12] = 7'd19;
        fine_lut[13] = 7'd21;
        fine_lut[14] = 7'd22;
        fine_lut[15] = 7'd24;
        fine_lut[16] = 7'd26;
        fine_lut[17] = 7'd27;
        fine_lut[18] = 7'd29;
        fine_lut[19] = 7'd30;
        fine_lut[20] = 7'd32;
        fine_lut[21] = 7'd34;
        fine_lut[22] = 7'd35;
        fine_lut[23] = 7'd37;
        fine_lut[24] = 7'd38;
        fine_lut[25] = 7'd40;
        fine_lut[26] = 7'd41;
        fine_lut[27] = 7'd43;
        fine_lut[28] = 7'd45;
        fine_lut[29] = 7'd46;
        fine_lut[30] = 7'd48;
        fine_lut[31] = 7'd49;
        fine_lut[32] = 7'd51;
        fine_lut[33] = 7'd53;
        fine_lut[34] = 7'd54;
        fine_lut[35] = 7'd56;
        fine_lut[36] = 7'd57;
        fine_lut[37] = 7'd59;
        fine_lut[38] = 7'd61;
        fine_lut[39] = 7'd62;
        fine_lut[40] = 7'd64;
        fine_lut[41] = 7'd65;
        fine_lut[42] = 7'd67;
        fine_lut[43] = 7'd69;
        fine_lut[44] = 7'd70;
        fine_lut[45] = 7'd72;
        fine_lut[46] = 7'd73;
        fine_lut[47] = 7'd75;
        fine_lut[48] = 7'd77;
        fine_lut[49] = 7'd78;
        fine_lut[50] = 7'd80;
        fine_lut[51] = 7'd81;
        fine_lut[52] = 7'd83;
        fine_lut[53] = 7'd85;
        fine_lut[54] = 7'd86;
        fine_lut[55] = 7'd88;
        fine_lut[56] = 7'd89;
        fine_lut[57] = 7'd91;
        fine_lut[58] = 7'd93;
        fine_lut[59] = 7'd94;
        fine_lut[60] = 7'd96;
        fine_lut[61] = 7'd97;
        fine_lut[62] = 7'd99;
        fine_lut[63] = 7'd101;
    end
endmodule