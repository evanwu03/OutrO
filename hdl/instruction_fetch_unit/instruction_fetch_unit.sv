

// Description: Instruction fetch unit reads the next two instructions given the current PC value and 
// and enqueues instructions to instruction queue. These instructions will then be pushed to the issue/dispatch unit

module instruction_fetch_unit #(
    parameter DATA_WIDTH = 36,
    parameter DEPTH       = 2**8,
    parameter INSTR_COUNT = 0,
    parameter IMEM_BASE_ADDR = 32'h0000_0000
) (
    input logic i_clk,
    input logic i_nrst, 
    input logic [DATA_WIDTH-1:0] i_pc,

    output logic [DATA_WIDTH-1:0] o_instr_0,
    output logic [DATA_WIDTH-1:0] o_instr_1
);


    // Signals 
    logic [DATA_WIDTH-1:0] w_instr_0;
    logic [DATA_WIDTH-1:0] w_instr_1;

    logic wr_en0;
    logic wr_en1;
    logic rd_en0;
    logic rd_en1;

    logic w_pop_instr0;
    logic w_pop_instr1;

    logic w_pop_valid0;
    logic w_pop_valid1;
    logic w_fifo_full;
    logic w_fifo_empty;


    // 1. Fetch next two instructions from instruction memory if available
    instruction_memory  #(
        .INSTR_WIDTH(INSTR_WIDTH),
        .DEPTH(DEPTH),
        .INSTR_COUNT(INSTR_COUNT),
        .IMEM_BASE_ADDR(IMEM_BASE_ADDR)
    )
    instr_mem (
        .i_pc(i_pc),
        .o_instr_0(w_instr_0),
        .o_instr_1(w_instr_1)
    );


    instruction_fifo #(


    )
    instr_queue (
        // Clock/Reset
        .i_clk(i_clk),
        .i_nrst(i_nrst)

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
        .o_fifo_full    (w_fifo_full),
        .o_fifo_empty   (w_fifo_empty)
    );


    // 2. Push instructions to instruction FIFO


    // 3. Assign instruction output pins


endmodule : instruction_fetch_unit