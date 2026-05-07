

// Description: Instruction fetch unit reads the next two instructions given the current PC value and 
// and enqueues instructions to instruction queue. These instructions will then be pushed to the issue/dispatch unit

module instruction_fetch_unit #(
    parameter DATA_WIDTH = 36
) (
    input logic i_clk,
    input logic i_nrst, 
    input logic [DATA_WIDTH-1:0] i_pc,

    output logic [DATA_WIDTH-1:0] o_instr_0,
    output logic [DATA_WIDTH-1:0] o_instr_1
);
    


    // 1. Fetch next two instructions from instruction memory if available



    // 2. Push instructions to instruction FIFO


    // 3. Assign instruction output pins


endmodule : instruction_fetch_unit