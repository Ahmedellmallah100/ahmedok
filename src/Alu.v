module Alu (
    input        rstn, clk, pb1_db, pb2_db, pb3_db,
    input  [7:0] sw,
    output reg [7:0] c_plus_carry,

);

reg [7:0] a, b;


    always @(posedge clk or negedge rstn) begin

        if (!rstn) begin
        a            <= 8'd0;
        b            <= 8'd0;
        c_plus_carry <= 9'd0;
        letters      <= 4'd0;
        opcode       <= 3'd0;
    end else begin
        if (pb1_db) begin
            a       <= sw;
            letters <= 4'hA;
        end else if (pb2_db) begin
            b       <= sw;
            letters <= 4'hB;
        end else if (pb3_db) begin
               
            case (sw[2:0])
                3'b001 : begin
                    c_plus_carry <= {1'b0, a} + {1'b0, b};
                end
                3'b010 : begin
                    c_plus_carry <= {1'b0, a} - {1'b0, b};
                end
                3'b011 : begin
                    c_plus_carry <= {1'b0, (~a + 8'd1)};
                end
                3'b100 : begin
                    c_plus_carry <= {1'b0, (a & b)};
                end
                3'b101 : begin
                    c_plus_carry <= {1'b0, (a | b)};
                end
                3'b110 : begin
                    c_plus_carry <= {1'b0, (a ^ b)};
                end
                default: begin
                    c_plus_carry <= 9'd0;
                end
            endcase
        end
    end
end

endmodule
