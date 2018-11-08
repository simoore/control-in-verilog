module example_dds #
(
    localparam AW = 16,   // amplitude width
    localparam PW = 24,   // phase width
    localparam SW = 8,   // sine LUT address width
    localparam FW = 6,   // fine LUT address width
    localparam FAW = 8, // fine angle width
    localparam FAF = 14  // fine angle fractional width
)(
    input wire clk, 
    input wire rst, 
    input wire ce_in, 
    input wire [PW-1:0] freqword,
    input wire [PW-1:0] phase_offset,
    output reg ce_out = 0, 
    output wire signed [AW-1:0] sin, 
    output wire signed [AW-1:0] cos
);

    reg rst_lcl = 0;
    reg [2:0] ce = 0;
    reg signed [FAW-1:0] fine_lut[2**FW-1:0];
    reg signed [AW-1:0] sin_lut[2**SW-1:0];
        
    wire [PW-1:0] phase;
    reg [PW-1:0] phase_reg = 0;
    reg quad = 0;
    reg half = 0;
    reg [FW-1:0] fine_addr = 0;
    wire [SW-1:0] sin_addr;
    wire [SW-1:0] cos_addr;
    
    reg signed [AW-1:0] sin_course = 0; // s(AW,AW-1) 
    reg signed [AW-1:0] cos_course = 0; // s(AW,AW-1)
    reg signed [AW-1:0] sin_abs = 0;    // s(AW,AW-1)
    reg signed [AW-1:0] cos_abs = 0;    // s(AW,AW-1)
    reg signed [FAW-1:0] fine = 0;      // s(FAW,FAF)
    
    wire signed [AW+FAW-1:0] sin_adj;	        // s(AW+FAW, AW+FAF-1)
    wire signed [AW+FAW-1:0] cos_adj;           // s(AW+FAW, AW+FAF-1)
    wire signed [AW+FAF-1:0] sin_adj_ext;       // s(AW+FAF, AW+FAF-1)
    wire signed [AW+FAF-1:0] cos_adj_ext;       // s(AW+FAF, AW+FAF-1)
    wire signed [AW+FAF-1:0] sin_course_ext;    // s(AW+FAF, AW+FAF-1)
    wire signed [AW+FAF-1:0] cos_course_ext;    // s(AW+FAF, AW+FAF-1)
    reg signed [AW+FAF-1:0] sin_long = 0;       // s(AW+FAF, AW+FAF-1)
    reg signed [AW+FAF-1:0] cos_long = 0;       // s(AW+FAF, AW+FAF-1)
    
    /**************************************************************************
    * Local reset.
    **************************************************************************/
    always @(posedge clk) 
        rst_lcl <= rst;
    
    /**************************************************************************
    * Direct digital synthesiser:  http://www.fpga4fun.com/DDS.html
    * The frequency is given by:   f = freqword/2^PW * f_exe
    **************************************************************************/
    always @(posedge clk) begin
        ce[0] <= ce_in;
        if (rst_lcl)        phase_reg <= 0;
        else if (ce_in)     phase_reg <= phase_reg + freqword;
    end
    
    assign phase = phase_reg + phase_offset;
    assign sin_addr = phase[PW-2] ? ~phase[PW-3:PW-SW-2] : phase[PW-3:PW-SW-2];
    assign cos_addr = phase[PW-2] ? phase[PW-3:PW-SW-2] : ~phase[PW-3:PW-SW-2];
    
    // The lookup table stores the sine wave from 0->pi/2.
    always @(posedge clk) begin
        ce[1] <= ce[0];
        if (rst_lcl) begin        
            sin_abs <= sin_lut[0];
            cos_abs <= sin_lut[0];
        end else if (ce[0]) begin
            sin_abs <= sin_lut[sin_addr];
            cos_abs <= sin_lut[cos_addr];
            quad <= phase[PW-1] ^ phase[PW-2];
            half <= phase[PW-1];
            fine_addr <= phase[PW-SW-3:PW-SW-FW-2];
        end
    end
    
    always @(posedge clk) begin
        ce[2] <= ce[1];
        if (rst_lcl)        sin_course <= 0;
        else if (ce[1])     sin_course <= half ? -sin_abs : sin_abs;
        if (rst_lcl)        cos_course <= 0;
        else if (ce[1])     cos_course <= quad ? -cos_abs : cos_abs;
        if (rst_lcl)        fine <= fine_lut[0];
        else if (ce[1])     fine <= fine_lut[fine_addr];
    end

    /**************************************************************************
    * Interpolation increases the purity of the DDS sine wave. Circular 
    * interpolation using the following trig identities.
    *      sin(x+y) = sin(x)cos(y) + cos(x)sin(y)
    *      cos(x+y) = cos(x)cos(y) - sin(x)sin(y)
    * x is the course angle taken as bit 21:14 of the phase, while y is the fine
    * angle taken as bit 13:8 of the phase. To simplify, the approximation is
    * used for the fine angle cos(y) ~ 1.
    * Reference.
    *      A digital frequency synthesizer by Tierney, Rader and Gold in 
    *      IEEE Transactions on Audio and Electroacoustics (1971)
    **************************************************************************/
    
    assign sin_adj = fine*cos_course;
    assign cos_adj = fine*sin_course;
    assign sin_adj_ext = { {(FAF-FAW){sin_adj[AW+FAW-1]}}, sin_adj };
    assign cos_adj_ext = { {(FAF-FAW){cos_adj[AW+FAW-1]}}, cos_adj };
    assign sin_course_ext = { sin_course, {FAF{1'b0}}};
    assign cos_course_ext = { cos_course, {FAF{1'b0}}}; 
    
    always @(posedge clk) begin
        ce_out <= ce[2];
        if (rst_lcl)        sin_long <= 0;
        else if (ce[2])     sin_long <= sin_course_ext + sin_adj_ext;
        if (rst_lcl)        cos_long <= 0;
        else if (ce[2])     cos_long <= cos_course_ext - cos_adj_ext;
    end
    
    // Circular interpolation output.      
    assign sin = sin_long[AW+FAF-1:FAF];
    assign cos = cos_long[AW+FAF-1:FAF];
    
    // No interpolation output.
    //assign sin = sin_course;
    //assign cos = cos_course;
                 
    /**************************************************************************
    * Sine lookup table. 8 bit address representing the phase [0,pi/2]. The
    * amplitude resolution is 16 bit with the [0,32768] range representing
    * [0,1]. The fine lookup table has a 6 6 bit address representing
    * the phase [0,pi/512] to more finely tune the accuracy of the DDS. It
    * has an amplitude of [0,127] representing the magnitude
    * [0,0.00775146484375].
    **************************************************************************/
    initial begin
        // The fine LUT format is s(16,15)
        sin_lut[0] = 0;
        sin_lut[1] = 201;
        sin_lut[2] = 402;
        sin_lut[3] = 603;
        sin_lut[4] = 804;
        sin_lut[5] = 1005;
        sin_lut[6] = 1206;
        sin_lut[7] = 1407;
        sin_lut[8] = 1608;
        sin_lut[9] = 1809;
        sin_lut[10] = 2009;
        sin_lut[11] = 2210;
        sin_lut[12] = 2410;
        sin_lut[13] = 2611;
        sin_lut[14] = 2811;
        sin_lut[15] = 3012;
        sin_lut[16] = 3212;
        sin_lut[17] = 3412;
        sin_lut[18] = 3612;
        sin_lut[19] = 3811;
        sin_lut[20] = 4011;
        sin_lut[21] = 4210;
        sin_lut[22] = 4410;
        sin_lut[23] = 4609;
        sin_lut[24] = 4808;
        sin_lut[25] = 5007;
        sin_lut[26] = 5205;
        sin_lut[27] = 5404;
        sin_lut[28] = 5602;
        sin_lut[29] = 5800;
        sin_lut[30] = 5998;
        sin_lut[31] = 6195;
        sin_lut[32] = 6393;
        sin_lut[33] = 6590;
        sin_lut[34] = 6786;
        sin_lut[35] = 6983;
        sin_lut[36] = 7179;
        sin_lut[37] = 7375;
        sin_lut[38] = 7571;
        sin_lut[39] = 7767;
        sin_lut[40] = 7962;
        sin_lut[41] = 8157;
        sin_lut[42] = 8351;
        sin_lut[43] = 8545;
        sin_lut[44] = 8739;
        sin_lut[45] = 8933;
        sin_lut[46] = 9126;
        sin_lut[47] = 9319;
        sin_lut[48] = 9512;
        sin_lut[49] = 9704;
        sin_lut[50] = 9896;
        sin_lut[51] = 10087;
        sin_lut[52] = 10278;
        sin_lut[53] = 10469;
        sin_lut[54] = 10659;
        sin_lut[55] = 10849;
        sin_lut[56] = 11039;
        sin_lut[57] = 11228;
        sin_lut[58] = 11417;
        sin_lut[59] = 11605;
        sin_lut[60] = 11793;
        sin_lut[61] = 11980;
        sin_lut[62] = 12167;
        sin_lut[63] = 12353;
        sin_lut[64] = 12539;
        sin_lut[65] = 12725;
        sin_lut[66] = 12910;
        sin_lut[67] = 13094;
        sin_lut[68] = 13279;
        sin_lut[69] = 13462;
        sin_lut[70] = 13645;
        sin_lut[71] = 13828;
        sin_lut[72] = 14010;
        sin_lut[73] = 14191;
        sin_lut[74] = 14372;
        sin_lut[75] = 14553;
        sin_lut[76] = 14732;
        sin_lut[77] = 14912;
        sin_lut[78] = 15090;
        sin_lut[79] = 15269;
        sin_lut[80] = 15446;
        sin_lut[81] = 15623;
        sin_lut[82] = 15800;
        sin_lut[83] = 15976;
        sin_lut[84] = 16151;
        sin_lut[85] = 16325;
        sin_lut[86] = 16499;
        sin_lut[87] = 16673;
        sin_lut[88] = 16846;
        sin_lut[89] = 17018;
        sin_lut[90] = 17189;
        sin_lut[91] = 17360;
        sin_lut[92] = 17530;
        sin_lut[93] = 17700;
        sin_lut[94] = 17869;
        sin_lut[95] = 18037;
        sin_lut[96] = 18204;
        sin_lut[97] = 18371;
        sin_lut[98] = 18537;
        sin_lut[99] = 18703;
        sin_lut[100] = 18868;
        sin_lut[101] = 19032;
        sin_lut[102] = 19195;
        sin_lut[103] = 19357;
        sin_lut[104] = 19519;
        sin_lut[105] = 19680;
        sin_lut[106] = 19841;
        sin_lut[107] = 20000;
        sin_lut[108] = 20159;
        sin_lut[109] = 20317;
        sin_lut[110] = 20475;
        sin_lut[111] = 20631;
        sin_lut[112] = 20787;
        sin_lut[113] = 20942;
        sin_lut[114] = 21096;
        sin_lut[115] = 21250;
        sin_lut[116] = 21403;
        sin_lut[117] = 21554;
        sin_lut[118] = 21705;
        sin_lut[119] = 21856;
        sin_lut[120] = 22005;
        sin_lut[121] = 22154;
        sin_lut[122] = 22301;
        sin_lut[123] = 22448;
        sin_lut[124] = 22594;
        sin_lut[125] = 22739;
        sin_lut[126] = 22884;
        sin_lut[127] = 23027;
        sin_lut[128] = 23170;
        sin_lut[129] = 23311;
        sin_lut[130] = 23452;
        sin_lut[131] = 23592;
        sin_lut[132] = 23731;
        sin_lut[133] = 23870;
        sin_lut[134] = 24007;
        sin_lut[135] = 24143;
        sin_lut[136] = 24279;
        sin_lut[137] = 24413;
        sin_lut[138] = 24547;
        sin_lut[139] = 24680;
        sin_lut[140] = 24811;
        sin_lut[141] = 24942;
        sin_lut[142] = 25072;
        sin_lut[143] = 25201;
        sin_lut[144] = 25329;
        sin_lut[145] = 25456;
        sin_lut[146] = 25582;
        sin_lut[147] = 25708;
        sin_lut[148] = 25832;
        sin_lut[149] = 25955;
        sin_lut[150] = 26077;
        sin_lut[151] = 26198;
        sin_lut[152] = 26319;
        sin_lut[153] = 26438;
        sin_lut[154] = 26556;
        sin_lut[155] = 26674;
        sin_lut[156] = 26790;
        sin_lut[157] = 26905;
        sin_lut[158] = 27019;
        sin_lut[159] = 27133;
        sin_lut[160] = 27245;
        sin_lut[161] = 27356;
        sin_lut[162] = 27466;
        sin_lut[163] = 27575;
        sin_lut[164] = 27683;
        sin_lut[165] = 27790;
        sin_lut[166] = 27896;
        sin_lut[167] = 28001;
        sin_lut[168] = 28105;
        sin_lut[169] = 28208;
        sin_lut[170] = 28310;
        sin_lut[171] = 28411;
        sin_lut[172] = 28510;
        sin_lut[173] = 28609;
        sin_lut[174] = 28706;
        sin_lut[175] = 28803;
        sin_lut[176] = 28898;
        sin_lut[177] = 28992;
        sin_lut[178] = 29085;
        sin_lut[179] = 29177;
        sin_lut[180] = 29268;
        sin_lut[181] = 29358;
        sin_lut[182] = 29447;
        sin_lut[183] = 29534;
        sin_lut[184] = 29621;
        sin_lut[185] = 29706;
        sin_lut[186] = 29791;
        sin_lut[187] = 29874;
        sin_lut[188] = 29956;
        sin_lut[189] = 30037;
        sin_lut[190] = 30117;
        sin_lut[191] = 30195;
        sin_lut[192] = 30273;
        sin_lut[193] = 30349;
        sin_lut[194] = 30424;
        sin_lut[195] = 30498;
        sin_lut[196] = 30571;
        sin_lut[197] = 30643;
        sin_lut[198] = 30714;
        sin_lut[199] = 30783;
        sin_lut[200] = 30852;
        sin_lut[201] = 30919;
        sin_lut[202] = 30985;
        sin_lut[203] = 31050;
        sin_lut[204] = 31113;
        sin_lut[205] = 31176;
        sin_lut[206] = 31237;
        sin_lut[207] = 31297;
        sin_lut[208] = 31356;
        sin_lut[209] = 31414;
        sin_lut[210] = 31470;
        sin_lut[211] = 31526;
        sin_lut[212] = 31580;
        sin_lut[213] = 31633;
        sin_lut[214] = 31685;
        sin_lut[215] = 31736;
        sin_lut[216] = 31785;
        sin_lut[217] = 31833;
        sin_lut[218] = 31880;
        sin_lut[219] = 31926;
        sin_lut[220] = 31971;
        sin_lut[221] = 32014;
        sin_lut[222] = 32057;
        sin_lut[223] = 32098;
        sin_lut[224] = 32137;
        sin_lut[225] = 32176;
        sin_lut[226] = 32213;
        sin_lut[227] = 32250;
        sin_lut[228] = 32285;
        sin_lut[229] = 32318;
        sin_lut[230] = 32351;
        sin_lut[231] = 32382;
        sin_lut[232] = 32412;
        sin_lut[233] = 32441;
        sin_lut[234] = 32469;
        sin_lut[235] = 32495;
        sin_lut[236] = 32521;
        sin_lut[237] = 32545;
        sin_lut[238] = 32567;
        sin_lut[239] = 32589;
        sin_lut[240] = 32609;
        sin_lut[241] = 32628;
        sin_lut[242] = 32646;
        sin_lut[243] = 32663;
        sin_lut[244] = 32678;
        sin_lut[245] = 32692;
        sin_lut[246] = 32705;
        sin_lut[247] = 32717;
        sin_lut[248] = 32728;
        sin_lut[249] = 32737;
        sin_lut[250] = 32745;
        sin_lut[251] = 32752;
        sin_lut[252] = 32757;
        sin_lut[253] = 32761;
        sin_lut[254] = 32765;
        sin_lut[255] = 32766;

        // The fine LUT format is s(8,14)
        fine_lut[0] = 0;
        fine_lut[1] = 2;
        fine_lut[2] = 3;
        fine_lut[3] = 5;
        fine_lut[4] = 6;
        fine_lut[5] = 8;
        fine_lut[6] = 9;
        fine_lut[7] = 11;
        fine_lut[8] = 13;
        fine_lut[9] = 14;
        fine_lut[10] = 16;
        fine_lut[11] = 17;
        fine_lut[12] = 19;
        fine_lut[13] = 20;
        fine_lut[14] = 22;
        fine_lut[15] = 24;
        fine_lut[16] = 25;
        fine_lut[17] = 27;
        fine_lut[18] = 28;
        fine_lut[19] = 30;
        fine_lut[20] = 31;
        fine_lut[21] = 33;
        fine_lut[22] = 35;
        fine_lut[23] = 36;
        fine_lut[24] = 38;
        fine_lut[25] = 39;
        fine_lut[26] = 41;
        fine_lut[27] = 42;
        fine_lut[28] = 44;
        fine_lut[29] = 46;
        fine_lut[30] = 47;
        fine_lut[31] = 49;
        fine_lut[32] = 50;
        fine_lut[33] = 52;
        fine_lut[34] = 53;
        fine_lut[35] = 55;
        fine_lut[36] = 57;
        fine_lut[37] = 58;
        fine_lut[38] = 60;
        fine_lut[39] = 61;
        fine_lut[40] = 63;
        fine_lut[41] = 64;
        fine_lut[42] = 66;
        fine_lut[43] = 68;
        fine_lut[44] = 69;
        fine_lut[45] = 71;
        fine_lut[46] = 72;
        fine_lut[47] = 74;
        fine_lut[48] = 75;
        fine_lut[49] = 77;
        fine_lut[50] = 79;
        fine_lut[51] = 80;
        fine_lut[52] = 82;
        fine_lut[53] = 83;
        fine_lut[54] = 85;
        fine_lut[55] = 86;
        fine_lut[56] = 88;
        fine_lut[57] = 90;
        fine_lut[58] = 91;
        fine_lut[59] = 93;
        fine_lut[60] = 94;
        fine_lut[61] = 96;
        fine_lut[62] = 97;
        fine_lut[63] = 99;
    end
endmodule