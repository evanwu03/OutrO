
module address_unit 
    import cpu_pkg::*;
#(
    parameter int  ADDR_WIDTH=32
) (

    input logic  i_issue_valid,
    input logic [ADDR_WIDTH-1:0] i_base,
    input logic [ADDR_WIDTH-1:0] i_offset,
    input rob_tag_t i_dest_tag,

    output load_buffer_entry_t o_load
);
    
always_comb begin

    o_load = '0;
    
    if (i_issue_valid) begin
        o_load.valid = 1'b1;
        o_load.tag   = i_dest_tag;
        o_load.addr  = i_base + i_offset;
    end
end

endmodule : address_unit