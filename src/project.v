/*
 * Copyright (c) 2024 Your Name
 * SPDX-License-Identifier: Apache-2.0
 */

`default_nettype none

module tt_um_example (
    input  wire [7:0] ui_in,
    output wire [7:0] uo_out,

    input  wire [7:0] uio_in,
    output wire [7:0] uio_out,
    output wire [7:0] uio_oe,

    input  wire       ena,
    input  wire       clk,
    input  wire       rst_n
);

    // -----------------------------
    // Internal signals
    // -----------------------------

    wire        pb1;
    wire        pb2;
    wire        pb3;

    wire [7:0]  sw;
    wire [7:0]  led;
    wire [7:0]  out_seg;
    wire [3:0]  an;

    // -----------------------------
    // Inputs
    // -----------------------------

    assign sw  = ui_in;

    assign pb1 = uio_in[0];
    assign pb2 = uio_in[1];
    assign pb3 = uio_in[2];

    // -----------------------------
    // Your original design
    // -----------------------------

    top_module core (
        .pb1(pb1),
        .pb2(pb2),
        .pb3(pb3),
        .sw(sw),
        .clk(clk),
        .rst(rst_n),
        .led(led),
        .an(an),
        .out_seg(out_seg)
    );

    // -----------------------------
    // Outputs
    // -----------------------------

    // 7-segment segments
    assign uo_out = out_seg;

    // 7-segment anodes
    assign uio_out[6:3] = an;

    // Unused pins
    assign uio_out[2:0] = 3'b000;
    assign uio_out[7]   = 1'b0;

    // -----------------------------
    // UIO direction
    // -----------------------------

    // uio[2:0] = inputs  (PB1, PB2, PB3)
    // uio[6:3] = outputs (AN[3:0])
    // uio[7]   = unused output

    assign uio_oe = 8'b11111000;

    // Prevent unused signal warning
    wire _unused = &{ena, led};

endmodule

