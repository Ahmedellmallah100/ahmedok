`default_nettype none

module top_module (
    input  pb1,
    input  pb2,
    input  pb3,
    input  clk,
    input  rst,
    input  [7:0] sw,
    output [3:0] an,
    output [7:0] out_seg
);

    wire slow_clk;
    wire pb1_db;
    wire pb2_db;
    wire pb3_db;

    wire [8:0] alu_result;
    wire [3:0] letters;

    wire [11:0] bcd;
    wire [1:0] sel;
    wire [3:0] mux_out;
    wire [6:0] seg7;

    // Clock divider
    clk_divider clk1 (
        .clk    (clk),
        .rstn   (rst),
        .clk_hz (slow_clk)
    );

    // Debounce
    Debounce d1 (
        .pb     (pb1),
        .pb_db  (pb1_db),
        .clk_hz (slow_clk),
        .rstn   (rst)
    );

    Debounce d2 (
        .pb     (pb2),
        .pb_db  (pb2_db),
        .clk_hz (slow_clk),
        .rstn   (rst)
    );

    Debounce d3 (
        .pb     (pb3),
        .pb_db  (pb3_db),
        .clk_hz (slow_clk),
        .rstn   (rst)
    );

    // ALU
    Alu A1 (
        .rstn          (rst),
        .clk           (clk),
        .pb1_db        (pb1_db),
        .pb2_db        (pb2_db),
        .pb3_db        (pb3_db),
        .sw            (sw),
        .c_plus_carry  (alu_result),
        .letters        (letters)
    );

    // Binary to BCD
    Bcd_Conventer B1 (
        .binary (alu_result[7:0]),
        .bcd    (bcd)
    );


    // Anode selection
    An_sel An (
        .clk  (slow_clk),
        .rstn (rst),
        .sel  (sel),
        .an   (an)
    );

    // BCD multiplexer
    mux m (
        .sel     (sel),
        .ones    (bcd[3:0]),
        .tens    (bcd[7:4]),
        .hundred (bcd[11:8]),
        .digtial (mux_out)
    );

    // 7-segment decoder
    decoder D (
        .digtial (mux_out),
        .seg     (seg7)
    );

    assign out_seg[6:0] = seg7;
    assign out_seg[7]   = 1'b0;

endmodule

`default_nettype wire
