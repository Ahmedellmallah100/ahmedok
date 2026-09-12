/*
 * Copyright (c) 2024 Your Name
 * SPDX-License-Identifier: Apache-2.0
 */

`default_nettype none

module tt_um_example (
    input  wire [7:0] ui_in,    // Dedicated inputs
    output wire [7:0] uo_out,   // Dedicated outputs
    input  wire [7:0] uio_in,   // IOs: Input path
    output wire [7:0] uio_out,  // IOs: Output path
    output wire [7:0] uio_oe,   // IOs: Enable path (active high: 0=input, 1=output)
    input  wire       ena,      // always 1 when the design is powered, so you can ignore it
    input  wire       clk,      // clock
    input  wire       rst_n     // reset_n - low to reset
);

    //---------------- إعادة تسمية الإشارات الأصلية زي ما هي بالظبط ----------------
    wire pb1, pb2, pb3;
    wire [7:0] sw;
    wire [7:0] led;
    wire [7:0] out_seg;
    wire [3:0] an;

    // ===== ربط المداخل =====
    assign sw  = ui_in;         // السويتشات على البنات المخصصة للدخول
    assign pb1 = uio_in[0];     // البوتونات على بنات الـ bidirectional (كدخول)
    assign pb2 = uio_in[1];
    assign pb3 = uio_in[2];

    // ===== ربط المخارج =====
    assign uo_out       = out_seg;   // السفن سيجمنت على البنات المخصصة للخروج
    assign uio_out[2:0] = 3'b000;    // مش مستخدمة (نفس بنات البوتونات دي input فعليًا)
    assign uio_out[6:3] = an;        // اختيار الـ anode
    assign uio_out[7]   = 1'b0;      // بن فاضي

    // تحديد اتجاه بنات الـ uio: 0..2 دخول (بوتونات) - 3..7 خروج
    assign uio_oe = 8'b11111000;

    // الـ led مش طالعة على أي بن خارجي (مفيش بنات كفاية)
    wire _unused_led = &led;
    wire _unused = &{ena, 1'b0};

    //====================== باقي الموديول زي ما هو بالظبط ============================

    wire slow_clk;
    wire pb1_db, pb2_db, pb3_db;
    wire [8:0] alu_result;
    wire [3:0] letters;
    wire [11:0] bcd;
    wire [1:0] sel;
    wire [3:0] mux_out;

    //====================== Clock Divider ============================
    clk_divider clk1 (.clk(clk), .rstn(rst_n), .clk_hz(slow_clk));

    //=================== Debounce for Push Buttons ===================
    Debounce d1 (.pb(pb1), .pb_db(pb1_db), .clk_hz(slow_clk), .rstn(rst_n));
    Debounce d2 (.pb(pb2), .pb_db(pb2_db), .clk_hz(slow_clk), .rstn(rst_n));
    Debounce d3 (.pb(pb3), .pb_db(pb3_db), .clk_hz(slow_clk), .rstn(rst_n));

    //============================ ALU =================================
    Alu A1 (
        .rstn(rst_n),
        .clk(clk),
        .pb1_db(pb1_db),
        .pb2_db(pb2_db),
        .pb3_db(pb3_db),
        .sw(sw),
        .c_plus_carry(alu_result),
        .letters(letters)
    );

    //========================= Binary to BCD =========================
    Bcd_Conventer B1 (.binary(alu_result[7:0]), .bcd(bcd));

    assign led = alu_result[7:0];

    //====================== Anode Selection ==========================
    An_sel An (.clk(slow_clk), .sel(sel), .an(an));

    //====================== Multiplexer for BCD ======================
    mux m (
        .sel(sel),
        .ones(bcd[3:0]),
        .tens(bcd[7:4]),
        .hundred(bcd[11:8]),
        .digtial(mux_out)
    );

    //====================== 7-Segment Decoder ========================
    decoder D (.digtial(mux_out), .seg(out_seg));

endmodule // tt_um_example
