

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
    input  var decoded_op_t i_decoded,

    // Dependencies from ROB and RS
    input  logic        i_rs_ready,
    input  logic        i_rob_ready,
    input  rob_tag_t    i_rob_tag, // Next free tag ROB --> Dispatch


    // Architectural register file read port input
    input  logic [DATA_WIDTH-1:0] i_src0_reg_value,
    input  logic [DATA_WIDTH-1:0] i_src1_reg_value,

    // From RAT lookup
    input  logic      i_src0_rat_valid,
    input  rob_tag_t  i_src0_rat_tag,
    input  logic      i_src1_rat_valid,
    input  rob_tag_t  i_src1_rat_tag,

    // To RAT lookup/update
    output arch_reg_t o_src0_arch,
    output arch_reg_t o_src1_arch,
    output logic      o_writes_rd,
    output arch_reg_t o_dest_arch,
    output rob_tag_t  o_dest_tag,
 

    // Allocated RS and ROB entry
    output rs_entry_t   o_rs_entry,
    output rob_entry_t  o_rob_entry,

    // Status
    output logic o_dispatch_ready
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


    logic w_uses_src0;
    logic w_uses_src1;
    logic w_writes_rd;
    logic w_src1_is_imm;

    logic w_dispatch_ready;
    logic w_dispatch_en;

    // Does the ROB and RS have an empty entry?
    assign w_dispatch_ready = i_rob_ready && i_rs_ready;

    // encoded instruction must also be valid to proceed
    assign w_dispatch_en = w_dispatch_ready && i_decoded.valid;

    // Valid signal --> RS
    assign o_dispatch_ready = w_dispatch_en;

    always_comb begin : dispatch

        w_uses_src0      = 1'b0;
        w_uses_src1      = 1'b0;
        w_writes_rd      = 1'b0;
        w_src1_is_imm      = 1'b0;

        o_rs_entry       = '0;
        o_rob_entry      = '0;
        o_dest_arch      = '0;
        o_dest_tag       = '0;
        o_src0_arch      = '0;
        o_src1_arch      = '0;
        o_writes_rd   = 1'b0;


        if (w_dispatch_en) begin

            // Part 1: Determine instruction type
            case (i_decoded.instr_class) 
                CLASS_ALU: begin

                    // Assign instruction type
                    o_rob_entry.instr_type = ROB_REG;
                    o_rob_entry.dest_arch_reg = i_decoded.rd;

                    // 1. Assign instruction type for RS and ROB:
                    case (i_decoded.alu_opcode) 
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
                    w_uses_src0 = 1'b1;
                    o_src0_arch = i_decoded.rn;

                    // Instruction does not use immediate value for operand 2
                    if (i_decoded.uses_imm) begin
                        w_uses_src1   = 1'b1;
                        w_src1_is_imm = 1'b1;
                    end else begin
                        w_uses_src1   = 1'b1;
                        w_src1_is_imm = 1'b0;
                        o_src1_arch   = i_decoded.rm;
                    end

                    // Register rename desination
                    w_writes_rd = 1'b1;
                    o_dest_arch = i_decoded.rd; // Update RAT: write to register rd

                
                end

                CLASS_MEM: begin
                    // Handle LDR/STR instructions separately
                    if(i_decoded.is_load) begin
                        o_rs_entry.op = RS_LOAD;
                        o_rob_entry.instr_type = ROB_REG;

                        w_writes_rd = 1'b1;
                        o_dest_arch = i_decoded.rd; // Update RAT: load to rd
                        o_rob_entry.dest_arch_reg = i_decoded.rd;
                        
                    end else begin
                        o_rs_entry.op          = RS_STORE;
                        o_rob_entry.instr_type = ROB_STORE;
                        o_dest_arch = i_decoded.rn; // Update RAT:  Store at rn
                        o_rob_entry.dest_arch_reg = i_decoded.rn;
                    end
                    
                    // Source operand assignment
                    w_uses_src0 = 1'b1;
                    o_src0_arch = i_decoded.rn;

                    if(i_decoded.uses_imm) begin  // offset is a register, not very clear
                        w_uses_src1 = 1'b1;
                        o_src1_arch = i_decoded.rm;
                        o_rs_entry.address = i_decoded.rm;
                    end else begin
                        w_src1_is_imm = 1'b1;
                        o_rs_entry.address = i_decoded.offset;
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


            // Part 2: source construction
            /* if source is not used:
                ready = 1

            else if source uses immediate:
                ready = 1
                value = immediate

            else if RAT says source has pending producer:
                ready = 0
                tag = RAT tag

            else:
                ready = 1
                value = register file value
             */

             // src0
            if (!w_uses_src0) begin
                o_rs_entry.src0_ready = 1'b1;
            end else if (i_src0_rat_valid) begin
                o_rs_entry.src0_ready = 1'b0;
                o_rs_entry.src0_tag   = i_src0_rat_tag;
            end else begin
                o_rs_entry.src0_ready = 1'b1;
                o_rs_entry.src0_value = i_src0_reg_value;
            end

             // src1 
            if (!w_uses_src1) begin
                o_rs_entry.src1_ready = 1'b1;
            end else if (w_src1_is_imm) begin
                o_rs_entry.src1_ready = 1'b1;
                o_rs_entry.src1_value = i_decoded.offset;
            end else if (i_src1_rat_valid) begin
                o_rs_entry.src1_ready = 1'b0;
                o_rs_entry.src1_tag   = i_src1_rat_tag;
            end else begin
                o_rs_entry.src1_ready = 1'b1;
                o_rs_entry.src1_value = i_src1_reg_value;
            end


            // Part 3: This tells the execution unit/CDB which ROB entry this instruction belongs to
            if (w_writes_rd) begin
                o_dest_tag = i_rob_tag;
                o_writes_rd = 1'b1;
            end

            // TO DO: Need to perform address calculations for LDR/STR and Branch


            // RS entry is now dispatched and busy
            o_rs_entry.rob_tag = i_rob_tag;
            //o_rs_entry.busy = 1'b1; This is to be set by RS instead
    
        end
    end
endmodule : dispatch_unit