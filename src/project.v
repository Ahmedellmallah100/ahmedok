
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

    wire [7:0] sw;
    wire pb1;
    wire pb2;
    wire pb3;

    wire [7:0] out_seg;
    wire [3:0] an;

    assign sw  = ui_in;

    assign pb1 = uio_in[0];
    assign pb2 = uio_in[1];
    assign pb3 = uio_in[2];

    top_module core (
        .pb1     (pb1),
        .pb2     (pb2),
        .pb3     (pb3),
        .sw      (sw),
        .clk     (clk),
        .rst     (rst_n),
        .led     (),
        .an      (an),
        .out_seg (out_seg)
    );

    // 7-segment
    assign uo_out = out_seg;

    // Digit select
    assign uio_out[3] = an[0];
    assign uio_out[4] = an[1];
    assign uio_out[5] = an[2];
    assign uio_out[6] = an[3];

    // Unused pins
    assign uio_out[2:0] = 3'b000;
    assign uio_out[7]   = 1'b0;

    // Output enable
    assign uio_oe[6:3] = 4'b1111;
    assign uio_oe[2:0] = 3'b000;
    assign uio_oe[7]   = 1'b0;

endmodule

