

// Description: Dispatches instructions to reservation station
// Author: Evan Wu
// Date:  5/16/2025

module  dispatch_unit 
    import cpu_pkg::*;
#(
    
) (
    //input  logic        i_clk,
    //input  logic        i_nrst,

    // Incoming instruction
    input  decoded_op_t i_decoded,

    // Dependencies from ROB and RS
    input  logic        i_rs_ready,
    input  logic        i_rob_ready,
    input  rob_tag_t    i_rob_tag,


    // From RAT lookup
    input  logic      i_src0_rat_valid,
    input  rob_tag_t  i_src0_rat_tag,
    input  logic      i_src1_rat_valid,
    input  rob_tag_t  i_src1_rat_tag,

    // To RAT lookup/update
    output arch_reg_t o_src0_arch,
    output arch_reg_t o_src1_arch,
    output logic      o_rename_valid,
    output arch_reg_t o_dest_arch,
    output rob_tag_t  o_dest_tag,
 

    // Allocated RS and ROB entry
    output rs_entry_t   o_rs_entry,
    output rob_entry_t  o_rob_entry


);
    
// Dispatch Procedure: 
/* 1. Drive source architectural registers to RAT
   o_src0_arch = decoded source 0
   o_src1_arch = decoded source 1

2. Receive RAT lookup result
   if RAT valid:
       RS source waits on ROB tag
   else:
       RS source uses register file value, once you add regfile inputs

3. Receive next ROB tag from ROB
   This becomes:
       RS entry rob_tag
       RAT destination tag
       ROB allocation index externally

4. Build ROB entry
   Store commit metadata:
       instruction type
       destination architectural register
       ready = 0 initially

5. If dispatch actually fires:
   update RAT destination mapping
   send RS entry to RS
   send ROB entry to ROB
 */


    logic w_dispatch_ready;
    logic w_dispatch_en;

    // Does the ROB and RS have an empty entry?
    assign w_dispatch_ready = i_rob_ready && i_rs_ready;

    // encoded instruction must also be valid to proceed
    assign w_dispatch_en = w_dispatch_ready && i_decoded.valid;


    always_comb begin :

        if (w_dispatch_en) begin

            // Determine the instruction type
            case (i_decoded.instr_class) 
                CLASS_ALU: begin

                    // 1. Assign instruction type for RS and ROB:
                    case (i_decoded.opcode) 
                        ARM_AND: o_rs_entry.op  = RS_AND;
                        ARM_SUB: o_rs_entry.op  = RS_SUB;
                        ARM_ADD: o_rs_entry.op  = RS_ADD;
                        ARM_CMN: o_rs_entry.op  = RS_CMN;
                        ARM_TEQ: o_rs_entry.op  = RS_TEQ;
                        ARM_MVN: o_rs_entry.op  = RS_MVN;
                        default: o_rs_entry.op  = RS_NOP;

                    endcase

                    // 2. Assign source operands and destination registers 
                    // for RAT lookup
                    o_src0_arch = i_decoded.rn;

                    // Instruction does not use immediate value for operand 2
                    if (!i_decoded.uses_imm) begin
                        o_src1_arch = i_decoded.rm;
                    end

                    o_rename_valid = 1'b1;
                    o_dest_arch = i_decoded.rd;


                    // Assign instruction type
                    o_rob_entry.instr_type = ROB_REG;

                end

                CLASS_MEM: begin

                    
                    if(i_decoded.is_load) begin
                        o_rs_entry.op = RS_LOAD;
                        o_rob_entry.instr_type = ROB_REG;
                        o_dest_arch = i_decoded.rd;
                        o_rename_valid = 1'b1;
                        
                    end else begin
                        o_rs_entry.op          = RS_STORE;
                        o_rob_entry.instr_type = ROB_STORE;
                    end
                    
                    o_src0_arch = i_decoded.rn;

                    if(i_decoded.use_imm) begin
                        o_src1_arch = i_decoded.rm;
                    end

                    
                    
                
                end

                CLASS_BRANCH: begin 

                    if (i_decoded.is_link) begin
                        o_rs_entry.op = RS_BRANCH_LINK;
                    end else begin
                        o_rs_entry.op = RS_BRANCH;
                    end


                    o_rob_entry.instr_type = ROB_BRANCH;

                    
                end

                // Other instructions not support
                default: begin
                    
                end 
            endcase
        

            
        end else begin

            // set default values
            o_rs_entry  = '0;
            o_rob_entry = '0;

            o_dest_arch = '0;
            o_dest_tag  = '0;

            o_rename_valid = 1'b0;
        end

    end





endmodule : dispatch_unit