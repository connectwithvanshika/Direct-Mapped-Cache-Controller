# Interview Preparation: Direct-Mapped Cache Controller

Every member should be able to answer all of these, not only the questions about their own part.

## Design
1. **What is a direct-mapped cache?**
   Every memory block can be stored in exactly one cache line, chosen by the index bits of the
   address. A lookup needs only one tag comparison.
2. **How are the tag, index and offset sizes derived?**
   1 KB / 16 bytes = 64 blocks. Index = log2(64) = 6 bits, offset = log2(16) = 4 bits,
   tag = 32 - 6 - 4 = 22 bits. Address[31:10] = tag, [9:4] = index, [3:0] = offset.
3. **What does the valid bit do?**
   It tells whether a line holds real data. After start or reset all valid bits are 0. Without it,
   an empty line whose stored tag is 0 would give a wrong hit for an address with tag 0.
4. **When is a request a hit?**
   When the requested tag equals the stored tag AND the valid bit is 1.
5. **Why does the FSM have LOOKUP and RELOAD states?**
   The RAMs register their output, so the data for a new index appears one clock later. LOOKUP waits
   for the tag and valid bit, RELOAD waits for the block that was written in REFILL to appear at the
   data RAM output.
6. **Why does a hit take 4 cycles and a read miss 7?**
   Hit: LOOKUP, CHECK, HIT, HIT_DONE. Read miss: LOOKUP, CHECK, MISS, WAIT_MEM, REFILL, RELOAD,
   COMPLETE. The miss penalty is 3 extra cycles because our memory answers in 1 cycle.
7. **Which write policy is used and why?**
   Write-through with no-write-allocate. A write hit updates cache and memory. A write miss
   updates only memory. It is simple (no dirty bits) and memory is always up to date.
8. **After a write miss, why is the next read of the same address a miss?**
   No-write-allocate: the block was not loaded into the cache by the write.
9. **What does the offset do in your design?**
   It is decoded, but the interface moves a whole 128-bit block, so it is not used to select a word.
   This is a known limitation.

## Results
10. **What is AMAT?** AMAT = hit time + miss rate x miss penalty = 4 + miss rate x 3.
11. **Why does the sequential trace give 75% hits?** Four words per 16-byte block: 1 miss and 3 hits.
12. **Why does the conflict trace give 0% hits?** 0x30 and 0x430 have the same index and different tags.
13. **Why does a longer memory latency not change the miss rate, but change AMAT?**
    The memory speed does not decide which accesses hit. It only changes the miss penalty.
14. **When is the cache faster than no cache?**
    Only if memory is slower than about 6.5 cycles in our test (baseline comparison).

## Verification
15. **How does the testbench know the design is correct?**
    A reference model predicts hit or miss for every request and compares it with the design.
    Read-after-write tests check the data.
16. **How do you know the testbench can find bugs?**
    Changing the comparator from == to != made 47 of 103 checks fail. Also the valid-reset test fails
    on the old valid RAM.

## Phase II
17. **What was changed in Phase II and why?**
    Reset for the valid bits (valid-bit handling), baseline without cache (comparison), trace files with a
    trace-driven testbench, and FPGA synthesis for resource use and frequency.
18. **Is the design synthesizable?**
    Yes. It was synthesized with Yosys for an iCE40 FPGA (see `documentation/synthesis_report.md`).

## My own questions (write 5 questions and answers in your own words)
1. **What happens when the cache is reset?**  
   When reset is activated, all valid bits are cleared to 0. This means the cache treats every line as empty, so the next access to an address results in a miss.

2. **Why do we use a direct-mapped cache instead of a fully associative cache?**  
   In a direct-mapped cache, each memory block has only one possible cache location. This makes the hardware simpler because we only need to check one tag.

3. **What is a cache conflict miss?**  
   A conflict miss happens when two different memory blocks map to the same cache index. They cannot stay in that cache line together, so accessing one after the other can cause repeated misses.

4. **Why do we compare cache performance with a no-cache design?**  
   The comparison helps us understand whether the cache actually reduces memory access time. It also shows how memory latency affects the benefit of using a cache.

5. **What is the role of the testbench in our project?**  
   The testbench applies different read and write requests to the cache and checks whether the outputs are correct. It helps us verify cache hits, misses, memory operations and reset behavior.
