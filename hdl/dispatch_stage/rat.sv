
// Description: Register Alias Table
// Author: Evan Wu
// Date: 5/19/2026

module rat  
    import cpu_pkg::*;
#( 
    parameter int RAT_DEPTH=16
)
(
    input logic i_clk,
    input logic i_nrst,


    // From Commit/ROB
    input logic      i_commit_valid,
    input logic      i_commit_writes_rd,
    input arch_reg_t i_commit_arch,
    input rob_tag_t  i_commit_tag,

    // From Dispatch unit: source lookup
    input arch_reg_t i_src0_arch,
    input arch_reg_t i_src1_arch,

    // From Dispatch unit: destination rename
    input logic      i_writes_rd,
    input arch_reg_t i_dest_arch,
    input rob_tag_t  i_dest_tag,

    // To Dispatch unit
    output  logic      o_src0_rat_valid,
    output  rob_tag_t  o_src0_rat_tag,
    output  logic      o_src1_rat_valid,
    output  rob_tag_t  o_src1_rat_tag


    // add commit logic later
);


localparam RAT_WIDTH = $clog2(RAT_DEPTH);

// Define RAT 
rat_entry_t rat [0:RAT_DEPTH-1];


// Combinational lookup
assign o_src0_rat_valid = rat[i_src0_arch].valid;
assign o_src0_rat_tag   = rat[i_src0_arch].tag;

assign o_src1_rat_valid = rat[i_src1_arch].valid;
assign o_src1_rat_tag   = rat[i_src1_arch].tag;

// Sequential rename/update
always_ff @(posedge i_clk or negedge i_nrst) begin
    if (!i_nrst) begin
        for (int i = 0; i < RAT_DEPTH; i++) begin
            rat[i].valid <= 1'b0;
            rat[i].tag   <= '0;
        end
    end else begin

        // Commit clear
        if (i_commit_valid && i_commit_writes_rd && i_commit_arch != ARCH_PC) begin
            if (rat[i_commit_arch].valid && rat[i_commit_arch].tag == i_commit_tag) begin
                rat[i_commit_arch].valid <= 1'b0;
                rat[i_commit_arch].tag   <= '0;
            end
        end

        // Rename/update
        if (i_writes_rd && (i_dest_arch !== ARCH_PC)) begin // Should PC register rename be invalid?
            rat[i_dest_arch].valid <= 1'b1;
            rat[i_dest_arch].tag   <= i_dest_tag;
        end
    end
end

endmodule : rat