
package cpu_pkg;


    // Architectural register types
    parameter int ARCH_REG_COUNT = 16;
    parameter int ARCH_REG_WIDTH = $clog2(ARCH_REG_COUNT);

    typedef logic [ARCH_REG_WIDTH-1:0] arch_reg_t;



    // Instruction types
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
        //logic [31:0] pc;
        //logic [31:0] raw_instr;

        // Common ARM fields
        logic [3:0]  cond;                // TO-DO add condition field semantics
        instr_class_e   instr_class;      // Normalized semantic class

        // Register fields from ARM encoding
        logic [3:0]  rn;            // Base reg / first operand
        logic [3:0]  rm;            // Second operand register
        logic [3:0]  rd;            // Dest reg, or store-data reg for STR


        // Data processing
        opcode_e     alu_opcode;
        logic        set_cond;      // CPSR condition fields
        logic        uses_imm;      // I bit in data processing or LDR/ST
        logic [11:0] op2;           // Raw Operand2, useful for debug/shift decode
        logic [23:0] offset;

        // Single data transfer: LDR / STR
        logic        pre_index;     // P bit
        logic        offset_dir;    // U bit
        logic        is_byte;       // B bit
        logic        write_back;    // W bit
        logic        is_load;       // L bit

        // Branch / branch with link
        logic        is_branch;
        logic        is_link;

    } decoded_op_t;



    // ROB types
    parameter int ROB_DEPTH = 8;
    parameter int ROB_TAG_WIDTH = $clog2(ROB_DEPTH);


    typedef logic [ROB_TAG_WIDTH-1:0] rob_tag_t;


    typedef enum logic [1:0] {  
        ROB_NOP      = 2'b00,
        ROB_STORE    = 2'b01,
        ROB_BRANCH   = 2'b10,
        ROB_REG      = 2'b11
    } rob_instr_e;


    typedef struct packed {
        rob_instr_e instr_type;
        arch_reg_t dest_arch_reg; 
        logic [31:0] value;
        logic ready; 
    } rob_entry_t;




    // Reservation station types 
    typedef enum logic [3:0] { 
        RS_NOP = 4'b0000,
        // ALU Ops 
        RS_AND,
        RS_SUB, 
        RS_ADD, 
        RS_CMN, 
        RS_TEQ, 
        RS_MVN, 

        // Memory Ops
        RS_LOAD, 
        RS_STORE,

        // Branch ops
        RS_BRANCH,
        RS_BRANCH_LINK
    } rs_op_e;



    typedef struct packed {

        logic busy;
        rs_op_e op;

        // Reservations that produce source operand, 0 means operation is already available or is unused
        
        logic src0_ready;
        logic [31:0] src0_value;
        rob_tag_t src0_tag;
        
        
        logic src1_ready;
        logic [31:0] src1_value;
        rob_tag_t src1_tag;
        
        // ROB entry that result placed on CDB corresponds to
        rob_tag_t rob_tag;


        // Address for Load/Store instructions
        logic [31:0] address;
        

    } rs_entry_t;


    
endpackage : cpu_pkg
