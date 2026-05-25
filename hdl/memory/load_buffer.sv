
module load_buffer 
    import cpu_pkg::*;
#( 
    parameter int LD_DEPTH = 8,
)
(
    input logic i_clk,
    input logic i_nrst,


    // Enable
    input logic wr_en,
    input logic rd_en,

    input load_buffer_entry_t i_load,

    output load_buffer_entry_t o_addr,
    
    // Status flags
    output logic o_full,
    output logic o_empty,
    output logic o_valid

);


localparam PTR_WIDTH = $clog2(LD_DEPTH);
localparam COUNT_WIDTH = $clog2(LD_DEPTH + 1);


// Load buffer
load_buffer_entry_t load_buffer [0:LD_DEPTH-1];
load_buffer_entry_t head_entry;


// head/tail ptr and count
logic [PTR_WIDTH-1:0] w_head;
logic [PTR_WIDTH-1:0] w_tail;
logic [COUNT_WIDTH-1:0] w_count;

logic do_read;
logic do_write;

logic w_empty;
logic w_full;


// Combinatorial read head
assign head_entry = load_buffer[w_head];

// Status 
assign w_empty = (w_count == 0);
assign w_full  = (w_count == LD_DEPTH);

assign o_full = w_full;
assign o_empty = w_empty;
assign o_addr = load_buffer[w_head];
assign o_valid = !w_empty && head_entry.valid;

assign do_read  = rd_en && o_valid;
assign do_write = wr_en && !w_full;

always_ff @(posedge i_clk or negedge i_nrst) begin
    if(!i_nrst) begin
        w_head <= '0;
        w_tail <= '0;
        w_count <= '0;
        
        // clear load buffer
        for (int i = 0; i < LD_DEPTH; i++) begin
            load_buffer[i] <= '0;
        end

    end else begin

        if (do_write) begin
            load_buffer[w_tail] <= i_load;
            w_tail <= w_tail + 1'b1;

        end

        if (do_read) begin
            load_buffer[w_head].valid <= 1'b0;
            w_head <= w_head + 1'b1;

        end

        unique case ({do_write, do_read})
            2'b10: w_count <= w_count + 1'b1;
            2'b01: w_count <= w_count - 1'b1;
            default: w_count <= w_count;
        endcase

    end
end

endmodule : load_buffer