
# Configuration parameters used by test runners
DATA_WIDTH = 32
INSTRUCTION_FIFO_DEPTH = 16

CLK_PERIOD_NS = 10

ARCH_REG_COUNT = 16
ARCH_PC = 15

ROB_DEPTH = 8
ROB_TAG_MAX = ROB_DEPTH - 1


# ARM data-processing opcode values
ARM_AND = 0b0000
ARM_SUB = 0b0010
ARM_ADD = 0b0100
ARM_CMN = 0b1011
ARM_TEQ = 0b1001
ARM_MVN = 0b1111

CLASS_ALU    = 0b00
CLASS_MEM    = 0b01
CLASS_BRANCH = 0b10
CLASS_OTHER  = 0b11


RS_NOP         = 0
RS_AND         = 1
RS_SUB         = 2
RS_ADD         = 3
RS_CMN         = 4
RS_TEQ         = 5
RS_MVN         = 6
RS_LOAD        = 7
RS_STORE       = 8
RS_BRANCH      = 9
RS_BRANCH_LINK = 10

ROB_NOP    = 0b00
ROB_STORE  = 0b01
ROB_BRANCH = 0b10
ROB_REG    = 0b11




DECODED_WIDTH = 76

VALID_BIT = 75

COND_HI = 74
COND_LO = 71

INSTR_CLASS_HI = 70
INSTR_CLASS_LO = 69

RN_HI = 68
RN_LO = 65

RM_HI = 64
RM_LO = 61

RD_HI = 60
RD_LO = 57

ALU_OPCODE_HI = 56
ALU_OPCODE_LO = 53

SET_COND_BIT = 52
USES_IMM_BIT = 51

OP2_HI = 50
OP2_LO = 39

OFFSET_HI = 38
OFFSET_LO = 7

PRE_INDEX_BIT = 6
OFFSET_DIR_BIT = 5
IS_BYTE_BIT = 4
WRITE_BACK_BIT = 3
IS_LOAD_BIT = 2

IS_BRANCH_BIT = 1
IS_LINK_BIT = 0


# rob_entry_t packed layout
# typedef struct packed {
#     rob_instr_e instr_type;       # 2
#     arch_reg_t dest_arch_reg;     # 4
#     logic [31:0] value;           # 32
#     logic [31:0] addr;            # 32
#     logic ready;                  # 1
#     logic addr_ready;             # 1
# } rob_entry_t;

ROB_ENTRY_WIDTH = 72

ROB_INSTR_TYPE_HI = 71
ROB_INSTR_TYPE_LO = 70

ROB_DEST_ARCH_HI = 69
ROB_DEST_ARCH_LO = 66

ROB_VALUE_HI = 65
ROB_VALUE_LO = 34

ROB_ADDR_HI = 33
ROB_ADDR_LO = 2

ROB_READY_BIT = 1
ROB_ADDR_READY_BIT = 0



# rs_entry_t packed layout
# typedef struct packed {
#     logic busy;                 // 1
#     rs_op_e op;                 // 4
#     logic src0_ready;           // 1
#     logic [31:0] src0_value;    // 32
#     rob_tag_t src0_tag;         // 3
#     logic src1_ready;           // 1
#     logic [31:0] src1_value;    // 32
#     rob_tag_t src1_tag;         // 3
#     rob_tag_t rob_tag;          // 3
#     logic [31:0] address;       // 32
# } rs_entry_t;

RS_ENTRY_WIDTH = 112

RS_BUSY_BIT = RS_ENTRY_WIDTH - 1          # 111

RS_OP_HI = 110
RS_OP_LO = 107

RS_SRC0_READY_BIT = 106

RS_SRC0_VALUE_HI = 105
RS_SRC0_VALUE_LO = 74

RS_SRC0_TAG_HI = 73
RS_SRC0_TAG_LO = 71

RS_SRC1_READY_BIT = 70

RS_SRC1_VALUE_HI = 69
RS_SRC1_VALUE_LO = 38

RS_SRC1_TAG_HI = 37
RS_SRC1_TAG_LO = 35

RS_ROB_TAG_HI = 34
RS_ROB_TAG_LO = 32

RS_ADDRESS_HI = 31
RS_ADDRESS_LO = 0