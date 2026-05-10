

// Description: Instruction fetch unit reads the next two instructions given the current PC value and 
// and enqueues instructions to instruction queue. These instructions will then be pushed to the issue/dispatch unit

module instruction_fetch_unit #(
    parameter INSTR_WIDTH = 32,
    parameter DEPTH       = 2**8,
    parameter INSTR_COUNT = 0,
    parameter BASE_ADDR = 32'h0000_0000
) (
    input logic i_clk,
    input logic i_nrst, 
    input logic [INSTR_WIDTH-1:0] i_pc,

    input logic i_instr_stall,

    output logic [INSTR_WIDTH-1:0] o_pc_next,
    output logic [INSTR_WIDTH-1:0] o_instr0,
    output logic [INSTR_WIDTH-1:0] o_instr1
);


    // Signals 
    logic [INSTR_WIDTH-1:0] w_instr0;
    logic [INSTR_WIDTH-1:0] w_instr1;

    logic wr_en0;
    logic wr_en1;
    logic rd_en0;
    logic rd_en1;

    logic fetch_valid0;
    logic fetch_valid1;


    logic [INSTR_WIDTH-1:0] w_pop_instr0;
    logic [INSTR_WIDTH-1:0] w_pop_instr1;

    logic w_pop_valid0;
    logic w_pop_valid1;

    logic w_push_valid0;
    logic w_push_valid1;
    logic [1:0] w_num_fetch_accepted;

    logic w_fifo_full;
    logic w_fifo_empty;


    // 1. Fetch next two instructions from instruction memory if available
    instruction_memory  #(
        .INSTR_WIDTH(INSTR_WIDTH),
        .DEPTH(DEPTH),
        .INSTR_COUNT(INSTR_COUNT),
        .BASE_ADDR(BASE_ADDR)
    )
    instr_mem (
        .i_pc(i_pc),
        .o_instr_0(w_instr0),
        .o_instr_1(w_instr1)
    );


    // 2. Push instructions to instruction FIFO
    instruction_fifo #(
        .DATA_WIDTH(INSTR_WIDTH),
        .QUEUE_DEPTH(2**4) // Power of 2
    )
    instr_queue (
        // Clock/Reset
        .i_clk(i_clk),
        .i_nrst(i_nrst),

        // push/pop enable pins
        .wr_en0         (wr_en0),
        .wr_en1         (wr_en1),
        .rd_en0         (rd_en0),
        .rd_en1         (rd_en1),

        // enqueue data
        .i_push_instr0  (w_instr0),
        .i_push_instr1  (w_instr1),

        // dequeue data
        .o_pop_instr0   (w_pop_instr0),
        .o_pop_instr1   (w_pop_instr1),


        // status flags
        .o_pop_valid0   (w_pop_valid0),
        .o_pop_valid1   (w_pop_valid1),
        
        .o_push_valid0  (w_push_valid0),
        .o_push_valid1  (w_push_valid1),

        .o_fifo_full    (w_fifo_full),
        .o_fifo_empty   (w_fifo_empty)
    );

    // Internal logic that determines if instructions are
    // ready to fetch or decode
    assign fetch_valid0 = ((i_pc - BASE_ADDR) >> 2) < INSTR_COUNT;
    assign fetch_valid1 = (((i_pc - BASE_ADDR) >> 2) + 1) < INSTR_COUNT;

    assign wr_en0 = fetch_valid0;
    assign wr_en1 = fetch_valid1;
    assign rd_en0 = !i_instr_stall && w_pop_valid0;
    assign rd_en1 = !i_instr_stall && w_pop_valid1;

    // 3. Assign instruction output pins
    assign o_instr0 = w_pop_instr0;
    assign o_instr1 = w_pop_instr1;

    assign w_num_fetch_accepted = w_push_valid0 + w_push_valid1;


    // Update pc depending on number of instructions pushed
    always_comb begin
        case (w_num_fetch_accepted)
            2'd2: o_pc_next = i_pc + 32'd8;
            2'd1: o_pc_next = i_pc + 32'd4;
            default: o_pc_next = i_pc;
        endcase
    end 

endmodule : instruction_fetch_unit