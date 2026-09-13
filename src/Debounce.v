module Debounce (
    pb,
    pb_db,
    clk_hz,
    rstn
);

    input  pb;
    input  clk_hz;
    input  rstn;
    output pb_db;

    wire q1;
    wire q2;

    D_flipflop f1 (.Q(q1),.D(pb),.clk(clk_hz),.rstn(rstn));
D_flipflop f2 (.Q(q2),.D(q1),.clk(clk_hz),.rstn(rstn));

    assign pb_db = q1 & ~q2;

endmodule
