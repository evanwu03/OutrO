

// Description: decoder module for ARM7TDMI-S instructions
// Author: Evan Wu
// Date: 5/10/2026

module decoder 
    import cpu_pkg::*;
#( 
    parameter INSTR_WIDTH = 32
) 
(
    input logic [INSTR_WIDTH-1:0] i_instr,
    output decoded_op_t decoded
);

    // Bit fields
    logic [3:0]  w_cond;
    logic [1:0]  w_instr_class;
    logic [3:0]  w_alu_opcode;
    logic        w_uses_imm;
    logic        w_set_cond;
    logic [3:0]  w_rn;
    logic [3:0]  w_rd;
    logic [3:0]  w_rm;
    logic [11:0] w_op2;

    // Single Data Transfer fields
    logic w_pre_index;   // P-bit Pre/Post indexing
    logic w_offset_dir;  // U-bit Up/Down Bit
    logic w_is_byte;     // B-bit 
    logic w_writeback;   // W-bit Write-back bit
    logic w_is_load;     // L-bit Load/Store bit, 
                         // 1 if Load from memory, 0 if store to memory
    logic [23:0] w_offset;

    // Branch
    //logic w_is_branch;
    logic w_is_link;

    always_comb begin : decode_packet
        decoded = '0;
        decoded.valid     = 1'b1;
        
        w_cond        = i_instr[31:28];
        w_instr_class = i_instr[27:26];
        
        w_uses_imm    = i_instr[25];
        w_rn          = i_instr[19:16];
        w_rd          = i_instr[15:12];
        w_rm          = i_instr[3:0];
        
        decoded.cond = w_cond;

        case (w_instr_class)
            CLASS_ALU: begin // Data processing instructions

                w_set_cond   = i_instr[20];
                w_op2        = i_instr[11:0];
                

                decoded.instr_class = CLASS_ALU;   
                decoded.uses_imm    = w_uses_imm;    // I-bit  
                decoded.set_cond    = w_set_cond;      // S-bit
                decoded.rn          = w_rn;     // rn 
                decoded.rd          = w_rd;     // rd
                
                if (decoded.uses_imm) begin
                    w_offset        = {32'b0, i_instr[7:0]};
                    decoded.offset  = w_offset;
                end else begin
                    decoded.rm      = w_rm;     // rm
                end

                decoded.op2         = w_op2;    // Operand 2 
                
                
                w_alu_opcode  = i_instr[24:21]; // Extract OP code 

                case (w_alu_opcode)
                    ARM_AND: decoded.alu_opcode = ARM_AND;
                    ARM_SUB: decoded.alu_opcode = ARM_SUB;
                    ARM_ADD: decoded.alu_opcode = ARM_ADD;
                    ARM_CMN: decoded.alu_opcode = ARM_CMN;
                    ARM_TEQ: decoded.alu_opcode = ARM_TEQ;
                    ARM_MVN: decoded.alu_opcode = ARM_MVN;
                    
                    default:
                        decoded.valid = 1'b0; // not a valid opcode
                endcase
                    
            end
            
            CLASS_MEM: begin // Data memory instructions

                w_pre_index  = i_instr[24];
                w_offset_dir = i_instr[23];
                w_is_byte    = i_instr[22];
                w_writeback  = i_instr[21];
                w_is_load    = i_instr[20]; 
                w_offset     = {32'b0, i_instr[11:0]};


                decoded.instr_class = CLASS_MEM;  
                decoded.uses_imm    = w_uses_imm;   // I-bit  
                decoded.pre_index   = w_pre_index;  // P-bit
                decoded.offset_dir  = w_offset_dir; // U-bit
                decoded.is_byte     = w_is_byte;    // B-bot
                decoded.write_back  = w_writeback;  // W-bit
                decoded.is_load     = w_is_load;    // L-bit
                decoded.rn          = w_rn;         // rn 
                decoded.rd          = w_rd;         // rd

                if (decoded.uses_imm) begin
                    decoded.rm      = w_rm;         // rm
                end else begin
                    decoded.offset  = w_offset;     // offset   
                end
            end

            CLASS_BRANCH: begin // Branch instructions

                w_is_link   = i_instr[24];
                w_offset    = i_instr[23:0];

                decoded.instr_class = CLASS_BRANCH;
                decoded.is_branch   = 1'b1;;
                decoded.is_link     = w_is_link;
                decoded.offset      = w_offset;
            end

            CLASS_OTHER: begin // Co-processor instructions / Software interrupts
                // NOT CURRENTLY SUPPORTED
                decoded.instr_class = CLASS_OTHER;
            end

            default: begin // Illegal instruction
                decoded.valid = 1'b0;
            end
        
        endcase        
    end 
endmodule : decoder
