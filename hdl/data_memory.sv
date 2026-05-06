
module data_memory #(
    parameter DATA_WIDTH = 32,
    parameter DEPTH      = 2**8
) (

    input logic i_clk,
    input logic i_nrst,

    input logic                  i_mem_write_en,
    input logic [DATA_WIDTH-1:0] i_addr,
    input logic [DATA_WIDTH-1:0] i_wdata,

    output logic [DATA_WIDTH-1:0] o_rdata
);

localparam int ADDR_WIDTH = $clog2(DEPTH);

logic w_addr_valid;

// 256 entries of 32-bit words = 1024 bytes total
logic [DATA_WIDTH-1:0] memory [0:DEPTH-1];
logic [ADDR_WIDTH-1:0] w_word_addr;

assign w_word_addr = i_addr >> 2;


// Check bounds + word alignment
assign w_addr_valid =
    (i_addr < DEPTH * 4) &&
    (i_addr[1:0] == 2'b00);

// Asynchronous reads
always_comb begin
    if (w_addr_valid)
        o_rdata = memory[w_word_addr];
    else
        o_rdata = '0;
end

// Synchronous writes
always_ff @(posedge i_clk or negedge i_nrst) begin
    if (!i_nrst) begin
        for (int i = 0; i < DEPTH; i++) begin
            memory[i] <= '0;
        end
    end else begin
        if (i_mem_write_en && w_addr_valid) begin
            memory[w_word_addr] <= i_wdata;
        end
    end
end

endmodule : data_memory