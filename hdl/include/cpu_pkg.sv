
package cpu_pkg;


    typedef enum logic [3:0] {  
        ARM_AND = 4'b0000,
        ARM_SUB = 4'b0010,
        ARM_ADD = 4'b0100,
        ARM_CMN = 4'b1011,
        ARM_TEQ = 4'b1001,
        ARM_MVN = 4'b1111
        
    } opcode_t;

    
    typedef enum logic [2:0] {
        OP_INVALID = 3'd0,
        OP_ALU     = 3'd1,
        OP_LOAD    = 3'd2,
        OP_STORE   = 3'd3,
        OP_BRANCH  = 3'd4
    } op_class_t;

    typedef struct packed {
        // Packet status
        logic        valid;

        // Useful for ROB / branch recovery / debugging
        logic [31:0] pc;
        logic [31:0] raw_instr;

        // Common ARM fields
        logic [3:0]  cond;
        logic [1:0]  instr_class;   // Raw instr[27:26]
        op_class_t   op_class;      // Normalized semantic class

        // Register fields from ARM encoding
        logic [3:0]  rn;            // Base reg / first operand
        logic [3:0]  rm;            // Second operand register
        logic [3:0]  rd;            // Dest reg, or store-data reg for STR

        // Normalized dependency info for OoO backend
        logic [3:0]  src1_arch;
        logic [3:0]  src2_arch;
        logic [3:0]  dst_arch;
        logic [3:0]  store_data_arch;

        logic        uses_src1;
        logic        uses_src2;
        logic        uses_store_data;
        logic        writes_dst;

        // Data processing
        opcode_t     opcode;
        logic        set_cond;
        logic        uses_imm;
        logic [11:0] op2;           // Raw Operand2, useful for debug/shift decode

        // Decoded immediate / offset / branch displacement
        logic [31:0] imm_value;

        // Single data transfer: LDR / STR
        logic        pre_index;     // P bit
        logic        add_offset;    // U bit
        logic        byte_transfer; // B bit
        logic        write_back;    // W bit

        logic        mem_read;
        logic        mem_write;

        // Branch / branch with link
        logic        is_branch;
        logic        link;

    } decoded_op_t;


    
endpackage : cpu_pkg
