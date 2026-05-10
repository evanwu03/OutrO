


// Includes
import cpu_pkg::decoded_op_t;
import cpu_pkg::opcode_t;


module decoder # ( 
    parameter INSTR_WIDTH = 32
) (

    input logic [INSTR_WIDTH-1:0] instr,

    output decoded_op_t op
);








endmodule : decoder
