
// Description: Instruction memory with dual-issue port
// Author: Evan Wu
// Date: 5/6/2026


module instruction_memory #(
    parameter INSTR_WIDTH = 32,
    parameter DEPTH       = 2**8,
    parameter INSTR_COUNT = 0,
    parameter IMEM_BASE_ADDR = 32'h0000_0000
)(
    input  logic [INSTR_WIDTH-1:0] i_pc,

    output logic [INSTR_WIDTH-1:0] o_instr_0,
    output logic [INSTR_WIDTH-1:0] o_instr_1
);

    localparam int ADDR_WIDTH = $clog2(DEPTH);

    logic w_addr_valid_0;
    logic w_addr_valid_1;

    logic [ADDR_WIDTH-1:0] w_word_addr_0;
    logic [ADDR_WIDTH-1:0] w_word_addr_1;

    // Instantiate instruction memory
    logic [INSTR_WIDTH-1:0] memory [0:DEPTH-1];


    logic [INSTR_WIDTH-1:0] w_local_addr;

    assign w_local_addr = i_pc - IMEM_BASE_ADDR;

    assign w_word_addr_0 = w_local_addr >> 2;
    assign w_word_addr_1 = w_word_addr_0 + 1;


    assign w_addr_valid_0 =
    (i_pc >= IMEM_BASE_ADDR) &&
    (w_word_addr_0 < INSTR_COUNT) &&
    (i_pc[1:0] == 2'b00);

    assign w_addr_valid_1 =
    (i_pc >= IMEM_BASE_ADDR) &&
    (w_word_addr_1 < INSTR_COUNT) &&
    (i_pc[1:0] == 2'b00);



    initial begin
        //$readmemh("program.hex", memory);
    end


    always_comb begin
        if (w_addr_valid_0)
            o_instr_0 = memory[w_word_addr_0];
        else
            o_instr_0 = '0;

        if (w_addr_valid_1)
            o_instr_1 = memory[w_word_addr_1];
        else
            o_instr_1 = '0;
    end

endmodule : instruction_memory
