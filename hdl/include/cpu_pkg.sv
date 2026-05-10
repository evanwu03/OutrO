
package cpu_pkg;


    typedef enum logic [3:0] {  
        ARM_AND = 4'b0000,
        ARM_SUB = 4'b0010,
        ARM_ADD = 4'b0100,
        ARM_CMN = 4'b1011,
        ARM_TEQ = 4'b1001,
        ARM_MVN = 4'b1111
        
    } opcode_e;

    
    typedef enum logic [1:0] {
        CLASS_ALU     = 2'b00,
        CLASS_MEM     = 2'b01,
        CLASS_BRANCH  = 2'b10,
        CLASS_OTHER   = 2'b11 // To support co-processors operations and software interrupts in the future
    } instr_class_e;

    typedef struct packed {
        // Packet status
        logic        valid;

        // Useful for ROB / branch recovery / debugging
        logic [31:0] pc;
        logic [31:0] raw_instr;

        // Common ARM fields
        logic [3:0]  cond;
        instr_class_e   instr_class;      // Normalized semantic class

        // Register fields from ARM encoding
        logic [3:0]  rn;            // Base reg / first operand
        logic [3:0]  rm;            // Second operand register
        logic [3:0]  rd;            // Dest reg, or store-data reg for STR

        // Normalized dependency info for OoO backend
        /* logic [3:0]  src1_arch;
        logic [3:0]  src2_arch;
        logic [3:0]  dst_arch;
        logic [3:0]  store_data_arch;

        logic        uses_src1;
        logic        uses_src2;
        logic        uses_store_data;
        logic        writes_dst;
        */


        // Data processing
        opcode_e     alu_opcode;
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
