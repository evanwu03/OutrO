
// Description: ALU implements subset of ARM7TDMI-S instruction sets
// Author: Evan Wu
// Date: 5/21/2026

module alu 
    import cpu_pkg::*;
#(
    parameter int DATA_WIDTH = 32
) (
    input logic i_issue_valid,
    input rs_op_e i_op,
    input logic [DATA_WIDTH-1:0] i_src0,
    input logic [DATA_WIDTH-1:0] i_src1,
    input rob_tag_t i_dest_tag,



    output cdb_packet_t o_cdb 
);


cdb_packet_t w_cdb;


always_comb begin
    
    // Reset to default
    w_cdb = '0;
    w_cdb.tag   = i_dest_tag;
    
    if (i_issue_valid) begin
        // To-Do: Implement CMN and TEQ and condition fields 
        unique case(i_op) 
            RS_AND: begin
                w_cdb.data = i_src0 & i_src1;
                w_cdb.valid = 1'b1;
            end
            RS_SUB: begin 
                w_cdb.data = i_src0 - i_src1;
                w_cdb.valid = 1'b1;
            end
            RS_ADD: begin 
                w_cdb.data = i_src0 + i_src1;
                w_cdb.valid = 1'b1;
            end
            //RS_CMN: 
            //RS_TEQ: w_cdb.data = i_src0 ^ i_src1;
            RS_MVN: begin
                w_cdb.data = ~i_src1;
                w_cdb.valid = 1'b1;
            end

            default: begin
                w_cdb.data  = '0;
                w_cdb.valid = 1'b0;
            end

        endcase
    end
end

assign o_cdb = w_cdb;


endmodule