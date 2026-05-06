

module register_file  #(
    parameter NUM_REGS = 16,
    parameter DATA_WIDTH = 32,
    parameter ADDR_WIDTH = $clog2(NUM_REGS)
)
( 
    input logic i_clk,
    input logic i_nrst,


    // Program counter next value
    input logic [DATA_WIDTH-1:0] i_pc_next,

    //////////////////////////////
    // Read ports for decode/issue
    //////////////////////////////

    // Issue slot 0 
    input  logic [ADDR_WIDTH-1:0] i_rs1_0,
    input  logic [ADDR_WIDTH-1:0] i_rs2_0,


    // Issue slot 1
    input  logic [ADDR_WIDTH-1:0] i_rs1_1,
    input  logic [ADDR_WIDTH-1:0] i_rs2_1,

    // Write port for commit stage
    input logic   i_write_en_0,
    input logic   i_write_en_1,

    // Commit slot 0/1
    input  logic [DATA_WIDTH-1:0] i_commit0_wdata,
    input  logic [DATA_WIDTH-1:0] i_commit1_wdata,

    // Write destination addressses
    input logic [ADDR_WIDTH-1:0] i_rd_0,
    input logic [ADDR_WIDTH-1:0] i_rd_1,

    // Data Read slot 0
    output logic [DATA_WIDTH-1:0] o_rs1_0,
    output logic [DATA_WIDTH-1:0] o_rs2_0,

    // Data Read slot 1
    output logic [DATA_WIDTH-1:0] o_rs1_1,
    output logic [DATA_WIDTH-1:0] o_rs2_1


);


// R0-R13: General purpose registers
// R15: Program Counter register
// R14: Link Register
localparam logic [ADDR_WIDTH-1:0] PC_REG = 4'd15;
localparam logic [ADDR_WIDTH-1:0] LR_REG = 4'd14;

// Instantiate register file
logic [DATA_WIDTH-1:0] r_regs [0:NUM_REGS-1];

// Asynchronous Reads 
always_comb begin : async_read

    // Read slot 0
     o_rs1_0 = r_regs[i_rs1_0];
     o_rs2_0 = r_regs[i_rs2_0];

    // Read slot 1 
     o_rs1_1 = r_regs[i_rs1_1];
     o_rs2_1 = r_regs[i_rs2_1];
    
end


// Synchronous writes 
always_ff @(posedge i_clk or negedge i_nrst) begin : sync_write

        // Reset registers
        if (!i_nrst) begin
            for (int i  = 0; i < NUM_REGS; i++) begin
                r_regs[i] <= '0;
            end                    
        end else begin

            // Should only write to R0-R14
            if (i_write_en_0 && (i_rd_0 != PC_REG)) begin
                r_regs[i_rd_0] <= i_commit0_wdata;
            end

            if (i_write_en_1 && (i_rd_1 != PC_REG)) begin
                r_regs[i_rd_1] <= i_commit1_wdata;
            end

            // Update R15 PC value given by Instruction fetch unit
            r_regs[PC_REG] <= i_pc_next;
        end
 end
 

endmodule