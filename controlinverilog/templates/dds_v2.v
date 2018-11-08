module {{ name }} #
(
    localparam AW = {{ aw }},   // amplitude width
    localparam PW = {{ pw }},   // phase width
    localparam SW = {{ sw }},   // sine LUT address width
    localparam FW = {{ fw }},   // fine LUT address width
    localparam FAW = {{ faw }}, // fine angle width
    localparam FAF = {{ faf }}  // fine angle fractional width
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
    * x is the course angle taken as bit {{ pw-3 }}:{{ pw-sw-2 }} of the phase, while y is the fine
    * angle taken as bit {{ pw-sw-3 }}:{{ pw-sw-fw-2 }} of the phase. To simplify, the approximation is
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
    * Sine lookup table. {{ sw }} bit address representing the phase [0,pi/2]. The
    * amplitude resolution is {{ aw }} bit with the [0,{{ 2**(aw-1) }}] range representing
    * [0,1]. The fine lookup table has a {{ fw }} 6 bit address representing
    * the phase [0,pi/{{ 2 * 2**sw }}] to more finely tune the accuracy of the DDS. It
    * has an amplitude of [0,{{ 2**(faw-1)-1 }}] representing the magnitude
    * [0,{{ (2**(faw-1)-1)*2**-faf }}].
    **************************************************************************/
    initial begin
        // The fine LUT format is s({{ aw }},{{ aw-1 }})
        {% for val in sine_lut %}
        sin_lut[{{ loop.index-1 }}] = {{ val }};
        {% endfor %}

        // The fine LUT format is s({{ faw }},{{ faf }})
        {% for val in fine_lut %}
        fine_lut[{{ loop.index-1 }}] = {{ val }};
        {% endfor %}
    end
endmodule