module Bcd_Conventer (
    input  wire [7:0] binary,
    output wire [11:0] bcd
);

wire [7:0] temp;
wire [3:0] hundred;
wire [3:0] tens;
wire [3:0] ones;

assign hundred = binary / 100;
assign temp    = binary % 100;
assign tens    = temp / 10;
assign ones    = temp % 10;

assign bcd = {hundred, tens, ones};

endmodule
