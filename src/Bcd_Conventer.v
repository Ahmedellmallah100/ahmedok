
module Bcd_Conventer (
    input  wire [7:0] binary,
    output wire [11:0] bcd
);

    wire [7:0] temp;
    wire [7:0] hundred_result;
    wire [7:0] tens_result;
    wire [7:0] ones_result;

    assign hundred_result = binary / 8'd100;
    assign temp           = binary % 8'd100;
    assign tens_result    = temp / 8'd10;
    assign ones_result    = temp % 8'd10;

    assign bcd = {
        hundred_result[3:0],
        tens_result[3:0],
        ones_result[3:0]
    };

endmodule

