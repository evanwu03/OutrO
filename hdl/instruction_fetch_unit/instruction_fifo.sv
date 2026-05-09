
module instruction_fifo #(
    parameter DATA_WIDTH = 36,
    parameter DEPTH = 2**4 // Power of 2
) (
    
    // Clock/Reset
    input logic i_clk,
    input logic i_nrst,

    // push/pop enable pins
    input  logic  wr_en0,
    input  logic  wr_en1,
    
    input logic rd_en0,
    input logic rd_en1,

    // Instruction0 and Instruction1 enqueue data
    input  logic [DATA_WIDTH-1:0] i_push_instr0,
    input  logic [DATA_WIDTH-1:0] i_push_instr1,

    // Instruction0 and Instruction1 dequeue data
    output logic [DATA_WIDTH-1:0] o_pop_instr0,
    output logic [DATA_WIDTH-1:0] o_pop_instr1,

    // Status flags
    output logic o_pop_valid0,
    output logic o_pop_valid1,
    output logic o_fifo_full,
    output logic o_fifo_empty
);

localparam PTR_WIDTH   = $clog2(DEPTH);
localparam COUNT_WIDTH = $clog2(DEPTH + 1);

// queue with a depth of DEPTH (16 by default)
logic [DATA_WIDTH-1:0] queue [0:DEPTH-1];

// head/tail ptr and count
logic [PTR_WIDTH-1:0] w_head_ptr;
logic [PTR_WIDTH-1:0] w_tail_ptr;
logic [COUNT_WIDTH-1:0] w_count; 

// decide  
logic [COUNT_WIDTH-1:0] w_free_slots;
logic [COUNT_WIDTH-1:0] num_writes, num_reads;
logic wr_valid0, wr_valid1;
logic rd_valid0, rd_valid1;


// illegal patterns: no instr1 without instr0
// wr_en1 should not be high when wr_en0 is low
// rd_en1 should not be high when rd_en0 is low


always_comb begin

    // Determine how many free slots are open

    w_free_slots = DEPTH - w_count;

    // Write acceptance 
    // TO-DO: outisde logic should ensure that instr1 can not be pushed if at the
    // last program instruction. wr_en1 should not be asserted with that in mind    
    wr_valid0  = wr_en0 && (w_free_slots >= 1);
    wr_valid1  = wr_en1 && (w_free_slots >= 2);
    num_writes = wr_valid0 + wr_valid1;

    // Read acceptance
    rd_valid0  = rd_en0 && (w_count >= 1);
    rd_valid1  = rd_en1 && (w_count >= 2);
    num_reads  = rd_valid0 + rd_valid1;

    // Status Flags 
    o_fifo_full = (w_count == DEPTH);
    o_fifo_empty = (w_count == 0);
    //o_fifo_empty = (w_head_ptr == w_tail_ptr);
    
    // Combinatorial read outputs
    o_pop_instr0 = queue[w_head_ptr];
    o_pop_instr1 = queue[w_head_ptr+1'b1];

    // Output availability flags
    o_pop_valid0 = (w_count >=1);
    o_pop_valid1 = (w_count >=2);

end


always_ff @(posedge i_clk or negedge i_nrst) begin

    if(!i_nrst) begin
        // Reset head and tail pointer
        w_head_ptr  <= '0;
        w_tail_ptr  <= '0;
        w_count     <= '0;
    end

    else begin


        // push operation
        if (wr_valid0) begin
            queue[w_tail_ptr] <= i_push_instr0;

        end        

        if (wr_valid1) begin
            queue[w_tail_ptr+1'b1] <= i_push_instr1;
        end

        // Advance pointers
        w_tail_ptr <= (w_tail_ptr + num_writes);
        w_head_ptr <= (w_head_ptr + num_reads);
        w_count <= w_count + num_writes - num_reads;

    end

end



    
endmodule