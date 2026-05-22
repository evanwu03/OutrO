
module rob 
    import cpu_pkg::*;
#(
    parameter DATA_WIDTH = 32,
    parameter ROB_DEPTH  = 8
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
    output rob_instr_e o_commit_type,
    output logic [DATA_WIDTH-1:0] o_commit_data,
    output rob_tag_t o_commit_tag, 

    // ROB status
    output logic o_empty,
    output logic o_full,
    output logic o_commit_valid
);

localparam PTR_WIDTH = $clog2(ROB_DEPTH);
localparam COUNT_WIDTH = $clog2(ROB_DEPTH + 1);

// ROB with a depth specified by ROB_DEPTH (default is 8)
rob_entry_t rob [0:ROB_DEPTH-1]; 
rob_entry_t head_entry;

// head/tail ptr and count
logic [PTR_WIDTH-1:0] w_head;
logic [PTR_WIDTH-1:0] w_tail;
logic [COUNT_WIDTH-1:0] w_count;

logic do_dispatch;
logic do_commit;

logic w_full;
logic w_empty;


// Status 
assign w_empty = w_count == 0;
assign w_full  = w_count == ROB_DEPTH;

assign o_full = w_full;
assign o_empty = w_empty;


// Combinatorial head read
assign head_entry = rob[w_head];

assign o_commit_valid = !w_empty && head_entry.ready;
assign o_commit_arch_reg = head_entry.dest_arch_reg;
assign o_commit_data = head_entry.value;
assign o_commit_tag = w_head;
assign o_commit_type = head_entry.instr_type;

assign do_commit = commit_en && o_commit_valid;
assign do_dispatch = wr_en && !w_full;

always_ff @(posedge i_clk or negedge i_nrst) begin
    if (!i_nrst) begin
        w_head <= '0;
        w_tail <= '0;
        w_count <= '0;

        // clear ROB
        for (int i = 0; i < ROB_DEPTH; i++) begin
            rob[i] <= '0;
        end
        
    // Update from CDB 
    end else begin
        // CDB writeback
        if (i_cdb.valid) begin
            rob[i_cdb.rob_tag].value <= i_cdb.data;
            rob[i_cdb.rob_tag].ready <= 1'b1;
        end
        
        // Dispatch allocation
        if (do_dispatch) begin
            rob[w_tail] <= i_dispatch_entry;
            w_tail <= w_tail + 1'b1;

        end     

        // Commit retirement
        if (do_commit) begin
            rob[w_head].valid <= 1'b0;
            w_head <= w_head + 1'b1;

        end

        // Update count 
        unique case ({do_dispatch, do_commit}) 
            2'b10: w_count <= w_count + 1'b1;
            2'b01: w_count <= w_count - 1'b1;
            default: w_count <= w_count;
        endcase
    end

    



end









endmodule