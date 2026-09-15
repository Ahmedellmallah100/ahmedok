`default_nettype none

module Bcd_Conventer (
    input  wire [7:0] binary,
    output wire [11:0] bcd
);

    wire [3:0] hundred;
    wire [3:0] tens;
    wire [3:0] ones;

    assign hundred = binary / 8'd100;
    assign tens    = (binary % 8'd100) / 8'd10;
    assign ones    = binary % 8'd10;

    assign bcd = {hundred, tens, ones};

endmodule

`default_nettype wire
