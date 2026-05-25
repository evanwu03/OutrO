
module reservation_station 
    import cpu_pkg::*;
#(
    parameter int RS_DEPTH = 8
) (
    
    input  logic        i_clk,
    input  logic        i_nrst,

    // Dispatch -> RS
    input  logic        i_dispatch_valid,
    input  rs_entry_t   i_dispatch_entry,
    output logic        o_dispatch_ready,

    // CDB -> RS wakeup
    input  cdb_packet_t i_cdb,

    // RS -> Functional Unit / Issue stage
    output logic        o_issue_valid,
    output rs_entry_t   o_issue_entry,
    input  logic        i_issue_ready
);

    localparam RS_WIDTH = $clog2(RS_DEPTH);
    // Reservation entries
    rs_entry_t rs [0:RS_DEPTH-1];

    // Free RS entry
    logic [RS_WIDTH-1:0] w_free_slot;
    logic w_free;

    // Issue signals
    logic [RS_WIDTH-1:0] w_issue_slot;
    logic w_issue_ready;
    logic w_dispatch_fire;
    logic w_issue_fire;
    

    // Priority encoder logic finds first available entry
    always_comb begin
        w_free = 1'b0;
        w_free_slot = '0;

        for (int i = 0; i < RS_DEPTH; i++) begin
            if(!rs[i].busy && !w_free) begin
                w_free_slot = RS_WIDTH'(i);
                w_free = 1;
            end
        end
    end

    // 1 when at least one RS entry is not busy
    // 0 when all RS entries are busy
    assign o_dispatch_ready = w_free;


    // Priority encoder selects a ready entry for issue 
    always_comb begin
        w_issue_ready = 1'b0;
        w_issue_slot  = '0;

        for (int i = 0; i < RS_DEPTH; i++) begin
            if (rs[i].busy &&
                rs[i].src1_ready &&
                rs[i].src2_ready &&
                !w_issue_ready) begin

                w_issue_ready = 1'b1;
                w_issue_slot  = RS_WIDTH'(i);
            end
        end
    end


    // Issue status
    assign o_issue_valid = w_issue_ready;
    assign w_dispatch_fire = i_dispatch_valid && o_dispatch_ready;
    assign w_issue_fire    = o_issue_valid && i_issue_ready;


    always_ff @(posedge i_clk or negedge i_nrst) begin : update_rs
        if(!i_nrst) begin 
            for (int i = 0; i < RS_DEPTH; i++) begin
                rs[i] <= '0;
            end
        end else begin
            
            // CDB wakeup
            if (i_cdb.valid) begin
                for (int i = 0; i < RS_DEPTH; i++) begin
                    if (rs[i].busy) begin
                        if (!rs[i].src1_ready && rs[i].src1_tag == i_cdb.tag) begin
                            rs[i].src1_ready <= 1'b1;
                            rs[i].src1_value <= i_cdb.value;
                        end

                        if (!rs[i].src2_ready && rs[i].src2_tag == i_cdb.tag) begin
                            rs[i].src2_ready <= 1'b1;
                            rs[i].src2_value <= i_cdb.value;
                        end
                    end
                end
            end

            // Clear issued entry
            if (w_issue_fire) begin
                rs[w_issue_slot].busy <= 1'b0;
            end

            // Insert dispatched entry
            if (w_dispatch_fire) begin
                rs[w_free_slot]      <= i_dispatch_entry;
                rs[w_free_slot].busy <= 1'b1;
            end
        end

    end

    // Issue instruction --> Functional unit (FU)
    assign o_issue_entry = rs[w_issue_slot];


endmodule

