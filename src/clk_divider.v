module clk_divider (
    input  wire clk,
    input  wire rstn,
    output reg  clk_hz
);

    reg [17:0] count;

    always @(posedge clk or negedge rstn) begin
        if (!rstn) begin
            count <= 18'd0;
            clk_hz <= 1'b0;
        end
        else begin
            if (count == 18'd250000) begin
                count <= 18'd0;
                clk_hz <= ~clk_hz;
            end
            else begin
                count <= count + 18'd1;
            end
        end
    end

endmodule
