
module rob 
    import cpu_pkg::*;
#(
    parameter DATA_WIDTH = 32
) (

    // Clock/Reset
    input logic i_clk,
    input logic i_nrst,


    // Push/pop enable pin
    input logic wr_en,
    input logic commit_en,

    // Dispatch unit --> ROB
    input rob_entry_t i_dispatch_entry,

    // From address unit for LDR/STR operations
    //input logic [DATA_WIDTH-1:0] i_address; // To be implemented

    // CDB writeback
    input cdb_packet_t i_cdb,

    // Output --> Register file / Load/store unit (LSU)
    output arch_reg_t o_commit_arch_reg,
    output logic [DATA_WIDTH-1:0] o_commit_data,
    output rob_tag_t o_commit_tag, // to clear entry in RAT


    // ROB status
    output logic o_empty,
    output logic o_commit_valid
);
    









endmodule