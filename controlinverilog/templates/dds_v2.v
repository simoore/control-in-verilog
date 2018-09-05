module {{ name }} #
(
    localparam AW = 16, // amplitude width
    localparam PW = 24, // phase width
    localparam SW = 8,  // sine LUT address width
    localparam FW = 6,  // fine LUT address width
    localparam FAW = 8, // fine angle width
    localparam FAF = 14 // fine angle fractional width
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
    * x is the course angle taken as bit 15:6 of the phase, while y is the fine
    * angle taken as bit 5:0 of the phase. To simplify, the approximation is
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
    * amplitude resolution is 10 bit with the [0,1023] range representing
    * [0,1]. The fine lookup table has a 6 bit address representing
    * the phase [0,pi/512] to more finely tune the accuracy of the DDS. It
    * has an amplitude of [0,101] representing the magnitude [0,0.0061359].
    **************************************************************************/
    initial begin
        // The fine LUT format is s(16,15)
        sin_lut[0] = 0;
        sin_lut[1] = 201;
        sin_lut[2] = 402;
        sin_lut[3] = 603;
        sin_lut[4] = 803;
        sin_lut[5] = 1004;
        sin_lut[6] = 1205;
        sin_lut[7] = 1406;
        sin_lut[8] = 1606;
        sin_lut[9] = 1807;
        sin_lut[10] = 2007;
        sin_lut[11] = 2208;
        sin_lut[12] = 2408;
        sin_lut[13] = 2608;
        sin_lut[14] = 2809;
        sin_lut[15] = 3009;
        sin_lut[16] = 3209;
        sin_lut[17] = 3408;
        sin_lut[18] = 3608;
        sin_lut[19] = 3808;
        sin_lut[20] = 4007;
        sin_lut[21] = 4206;
        sin_lut[22] = 4406;
        sin_lut[23] = 4604;
        sin_lut[24] = 4803;
        sin_lut[25] = 5002;
        sin_lut[26] = 5200;
        sin_lut[27] = 5398;
        sin_lut[28] = 5596;
        sin_lut[29] = 5794;
        sin_lut[30] = 5992;
        sin_lut[31] = 6189;
        sin_lut[32] = 6386;
        sin_lut[33] = 6583;
        sin_lut[34] = 6780;
        sin_lut[35] = 6976;
        sin_lut[36] = 7172;
        sin_lut[37] = 7368;
        sin_lut[38] = 7564;
        sin_lut[39] = 7759;
        sin_lut[40] = 7954;
        sin_lut[41] = 8149;
        sin_lut[42] = 8343;
        sin_lut[43] = 8537;
        sin_lut[44] = 8731;
        sin_lut[45] = 8924;
        sin_lut[46] = 9117;
        sin_lut[47] = 9310;
        sin_lut[48] = 9503;
        sin_lut[49] = 9695;
        sin_lut[50] = 9886;
        sin_lut[51] = 10078;
        sin_lut[52] = 10268;
        sin_lut[53] = 10459;
        sin_lut[54] = 10649;
        sin_lut[55] = 10839;
        sin_lut[56] = 11028;
        sin_lut[57] = 11217;
        sin_lut[58] = 11406;
        sin_lut[59] = 11594;
        sin_lut[60] = 11781;
        sin_lut[61] = 11968;
        sin_lut[62] = 12155;
        sin_lut[63] = 12341;
        sin_lut[64] = 12527;
        sin_lut[65] = 12713;
        sin_lut[66] = 12897;
        sin_lut[67] = 13082;
        sin_lut[68] = 13266;
        sin_lut[69] = 13449;
        sin_lut[70] = 13632;
        sin_lut[71] = 13814;
        sin_lut[72] = 13996;
        sin_lut[73] = 14177;
        sin_lut[74] = 14358;
        sin_lut[75] = 14538;
        sin_lut[76] = 14718;
        sin_lut[77] = 14897;
        sin_lut[78] = 15076;
        sin_lut[79] = 15254;
        sin_lut[80] = 15431;
        sin_lut[81] = 15608;
        sin_lut[82] = 15784;
        sin_lut[83] = 15960;
        sin_lut[84] = 16135;
        sin_lut[85] = 16310;
        sin_lut[86] = 16483;
        sin_lut[87] = 16657;
        sin_lut[88] = 16829;
        sin_lut[89] = 17001;
        sin_lut[90] = 17173;
        sin_lut[91] = 17343;
        sin_lut[92] = 17513;
        sin_lut[93] = 17683;
        sin_lut[94] = 17851;
        sin_lut[95] = 18019;
        sin_lut[96] = 18187;
        sin_lut[97] = 18353;
        sin_lut[98] = 18519;
        sin_lut[99] = 18685;
        sin_lut[100] = 18849;
        sin_lut[101] = 19013;
        sin_lut[102] = 19176;
        sin_lut[103] = 19339;
        sin_lut[104] = 19500;
        sin_lut[105] = 19661;
        sin_lut[106] = 19822;
        sin_lut[107] = 19981;
        sin_lut[108] = 20140;
        sin_lut[109] = 20298;
        sin_lut[110] = 20455;
        sin_lut[111] = 20611;
        sin_lut[112] = 20767;
        sin_lut[113] = 20922;
        sin_lut[114] = 21076;
        sin_lut[115] = 21229;
        sin_lut[116] = 21382;
        sin_lut[117] = 21533;
        sin_lut[118] = 21684;
        sin_lut[119] = 21834;
        sin_lut[120] = 21984;
        sin_lut[121] = 22132;
        sin_lut[122] = 22280;
        sin_lut[123] = 22426;
        sin_lut[124] = 22572;
        sin_lut[125] = 22717;
        sin_lut[126] = 22862;
        sin_lut[127] = 23005;
        sin_lut[128] = 23147;
        sin_lut[129] = 23289;
        sin_lut[130] = 23430;
        sin_lut[131] = 23569;
        sin_lut[132] = 23708;
        sin_lut[133] = 23846;
        sin_lut[134] = 23984;
        sin_lut[135] = 24120;
        sin_lut[136] = 24255;
        sin_lut[137] = 24390;
        sin_lut[138] = 24523;
        sin_lut[139] = 24656;
        sin_lut[140] = 24787;
        sin_lut[141] = 24918;
        sin_lut[142] = 25048;
        sin_lut[143] = 25177;
        sin_lut[144] = 25305;
        sin_lut[145] = 25432;
        sin_lut[146] = 25558;
        sin_lut[147] = 25683;
        sin_lut[148] = 25807;
        sin_lut[149] = 25930;
        sin_lut[150] = 26052;
        sin_lut[151] = 26173;
        sin_lut[152] = 26293;
        sin_lut[153] = 26412;
        sin_lut[154] = 26531;
        sin_lut[155] = 26648;
        sin_lut[156] = 26764;
        sin_lut[157] = 26879;
        sin_lut[158] = 26993;
        sin_lut[159] = 27106;
        sin_lut[160] = 27218;
        sin_lut[161] = 27329;
        sin_lut[162] = 27439;
        sin_lut[163] = 27548;
        sin_lut[164] = 27656;
        sin_lut[165] = 27763;
        sin_lut[166] = 27869;
        sin_lut[167] = 27974;
        sin_lut[168] = 28078;
        sin_lut[169] = 28181;
        sin_lut[170] = 28282;
        sin_lut[171] = 28383;
        sin_lut[172] = 28482;
        sin_lut[173] = 28581;
        sin_lut[174] = 28678;
        sin_lut[175] = 28775;
        sin_lut[176] = 28870;
        sin_lut[177] = 28964;
        sin_lut[178] = 29057;
        sin_lut[179] = 29149;
        sin_lut[180] = 29240;
        sin_lut[181] = 29330;
        sin_lut[182] = 29418;
        sin_lut[183] = 29506;
        sin_lut[184] = 29592;
        sin_lut[185] = 29678;
        sin_lut[186] = 29762;
        sin_lut[187] = 29845;
        sin_lut[188] = 29927;
        sin_lut[189] = 30008;
        sin_lut[190] = 30087;
        sin_lut[191] = 30166;
        sin_lut[192] = 30243;
        sin_lut[193] = 30320;
        sin_lut[194] = 30395;
        sin_lut[195] = 30469;
        sin_lut[196] = 30542;
        sin_lut[197] = 30613;
        sin_lut[198] = 30684;
        sin_lut[199] = 30753;
        sin_lut[200] = 30822;
        sin_lut[201] = 30889;
        sin_lut[202] = 30955;
        sin_lut[203] = 31019;
        sin_lut[204] = 31083;
        sin_lut[205] = 31145;
        sin_lut[206] = 31207;
        sin_lut[207] = 31267;
        sin_lut[208] = 31326;
        sin_lut[209] = 31383;
        sin_lut[210] = 31440;
        sin_lut[211] = 31495;
        sin_lut[212] = 31549;
        sin_lut[213] = 31602;
        sin_lut[214] = 31654;
        sin_lut[215] = 31705;
        sin_lut[216] = 31754;
        sin_lut[217] = 31802;
        sin_lut[218] = 31849;
        sin_lut[219] = 31895;
        sin_lut[220] = 31940;
        sin_lut[221] = 31983;
        sin_lut[222] = 32025;
        sin_lut[223] = 32066;
        sin_lut[224] = 32106;
        sin_lut[225] = 32145;
        sin_lut[226] = 32182;
        sin_lut[227] = 32218;
        sin_lut[228] = 32253;
        sin_lut[229] = 32287;
        sin_lut[230] = 32320;
        sin_lut[231] = 32351;
        sin_lut[232] = 32381;
        sin_lut[233] = 32410;
        sin_lut[234] = 32437;
        sin_lut[235] = 32464;
        sin_lut[236] = 32489;
        sin_lut[237] = 32513;
        sin_lut[238] = 32536;
        sin_lut[239] = 32557;
        sin_lut[240] = 32578;
        sin_lut[241] = 32597;
        sin_lut[242] = 32615;
        sin_lut[243] = 32631;
        sin_lut[244] = 32647;
        sin_lut[245] = 32661;
        sin_lut[246] = 32674;
        sin_lut[247] = 32685;
        sin_lut[248] = 32696;
        sin_lut[249] = 32705;
        sin_lut[250] = 32713;
        sin_lut[251] = 32720;
        sin_lut[252] = 32725;
        sin_lut[253] = 32730;
        sin_lut[254] = 32733;
        sin_lut[255] = 32735;
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