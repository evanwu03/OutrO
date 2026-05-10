

// Description: decoder module for ARM7TDMI-S instructions
// Author: Evan Wu
// Date: 5/10/2026

module decoder 
    import cpu_pkg::*;
#( 
    parameter INSTR_WIDTH = 32
) 
(
    input logic i_valid_instr,
    input logic [INSTR_WIDTH-1:0] i_instr,
    output decoded_op_t decoded
);

    // Bit fields
    logic [1:0] w_instr_class;
    logic [3:0] w_alu_opcode;
    logic       w_uses_imm;

    //assign w_alu_opcode = i_instr[24:21];
    
    always_comb begin : decode_packet
        decoded = '0;
        decoded.valid     = i_valid_instr;
        decoded.raw_instr = i_instr;
        decoded.cond = i_instr[31:28];

        // Extract bits 27:26
        w_instr_class = i_instr[27:26];
        w_uses_imm    = i_instr[25];

        case (w_instr_class)
            CLASS_ALU: begin // Data processing instructions
                decoded.instr_class = CLASS_ALU;   
                decoded.uses_imm    = w_uses_imm    // I-bit  
                decoded.set_cond    = i_instr[20];      // S-bit
                decoded.rn          = i_instr[19:16];   // rn 
                decoded.rd          = i_instr[15:12];   // rd
                decoded.op2         = i_instr[11:0];    // Operand 2
                
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


            end
            


            CLASS_MEM: begin // Data memory instructions
                decoded.instr_class = CLASS_MEM;
            end

            CLASS_BRANCH: begin // Branch instructions
                decoded.instr_class = CLASS_BRANCH;
            end

            CLASS_OTHER: begin // Co-processor instructions / Software interrupts
                decoded.instr_class = CLASS_OTHER;
            end

            default: begin // Illegal instruction
                decoded.valid = 1'b0;
            end
        
        endcase        


    end 






endmodule : decoder
