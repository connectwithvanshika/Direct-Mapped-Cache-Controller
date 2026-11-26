// synth_wrapper.v
// Only for FPGA synthesis and timing. cache_top has more than 300 I/O pins
// (two 128-bit buses), which does not fit on a small FPGA package. This wrapper
// feeds the cache from shift registers and compresses the result into 1 output
// bit, so the cache runs with registered inputs and outputs. The reported
// maximum frequency is then the speed of the cache itself.
module synth_wrapper (
    input  wire clk,
    input  wire reset,
    input  wire cpu_req_in,
    input  wire cpu_write_in,
    input  wire ser_in,          // serial data in: fills address and write data
    output reg  ser_out,         // XOR of all read-data bits
    output reg  cpu_ready_out,
    output reg  cache_miss_out
);

    reg [159:0] in_sr;           // [31:0] address, [159:32] write data
    reg cpu_req_r, cpu_write_r;

    wire [127:0] cpu_read_data;
    wire cpu_ready, cache_miss;
    reg  [127:0] rd_r;

    always @(posedge clk) begin
        in_sr       <= {in_sr[158:0], ser_in};
        cpu_req_r   <= cpu_req_in;
        cpu_write_r <= cpu_write_in;
        rd_r           <= cpu_read_data;
        ser_out        <= ^rd_r;
        cpu_ready_out  <= cpu_ready;
        cache_miss_out <= cache_miss;
    end

    cache_top cache (
        .clk(clk),
        .reset(reset),
        .cpu_req(cpu_req_r),
        .cpu_write(cpu_write_r),
        .cpu_address(in_sr[31:0]),
        .cpu_write_data(in_sr[159:32]),
        .cpu_read_data(cpu_read_data),
        .cpu_ready(cpu_ready),
        .cache_miss(cache_miss)
    );

endmodule
