
# Cache Parameter Derivation

## 1. Formulas

Cache size C bytes, block size B bytes, 32-bit address.

- Number of blocks = C / B
- Offset bits = log2(B)
- Index bits = log2(number of blocks)
- Tag bits = 32 - index bits - offset bits
- Data storage = blocks x B x 8 bits
- Tag storage = blocks x tag bits
- Valid storage = blocks x 1 bit

## 2. Our Design: 1 KB Cache, 16-byte Blocks

- Blocks = 1024 / 16 = 64
- Offset = log2(16) = 4 bits, address[3:0]
- Index = log2(64) = 6 bits, address[9:4]
- Tag = 32 - 6 - 4 = 22 bits, address[31:10]
- One block = 16 bytes = 128 bits, so the CPU data bus is 128 bits wide.

## 3. Three Configurations Compared

| Configuration | Blocks | Offset | Index | Tag | Address split (tag / index / offset) |
|---|---:|---:|---:|---:|---|
| 1 KB / 16 B (our design) | 64 | 4 | 6 | 22 | [31:10] / [9:4] / [3:0] |
| 2 KB / 16 B | 128 | 4 | 7 | 21 | [31:11] / [10:4] / [3:0] |
| 1 KB / 32 B | 32 | 5 | 5 | 22 | [31:10] / [9:5] / [4:0] |

### Storage Cost

| Configuration | Data bits | Tag bits | Valid bits | Total bits | Tag + valid overhead |
|---|---:|---:|---:|---:|---:|
| 1 KB / 16 B (our design) | 8192 | 1408 | 64 | 9664 | 18.0% |
| 2 KB / 16 B | 16384 | 2688 | 128 | 19200 | 17.2% |
| 1 KB / 32 B | 8192 | 704 | 32 | 8928 | 9.0% |

Overhead = (tag bits + valid bits) / data bits. Bigger blocks mean fewer lines, so fewer tags to store.

## 4. The Same Addresses in the Three Caches

| Address | 1 KB / 16 B (tag, index, offset) | 2 KB / 16 B | 1 KB / 32 B |
|---|---|---|---|
| 0x030 | 0, 3, 0x0 | 0, 3, 0x0 | 0, 1, 0x10 |
| 0x430 | 1, 3, 0x0 | 0, 67, 0x0 | 1, 1, 0x10 |
| 0x410 | 1, 1, 0x0 | 0, 65, 0x0 | 1, 0, 0x10 |

- In our 1 KB cache, 0x030 and 0x430 both have index 3 but different tags, so they conflict.
- In the 2 KB cache, they have indexes 3 and 67, so they no longer conflict.
- With 32-byte blocks they still conflict because the cache has only 32 lines.

## 5. Sequential Trace with Other Block Sizes

The sequential trace reads 16 words at 0x100, 0x104, ... 0x13C (64 bytes).

| Configuration | Misses | Hits | Hit rate |
|---|---:|---:|---:|
| 1 KB / 16 B (simulated) | 4 | 12 | 75.0% |
| 1 KB / 32 B (calculated) | 2 | 14 | 87.5% |

With 32-byte blocks every miss brings in twice as much data, so the next 7 words hit. In our model the memory returns a whole block in one transfer. A real memory needs more time for a bigger block, so the miss penalty would also grow.

## 6. What I Understood

**My understanding:**

[The number of index bits depends on the number of cache blocks, which is determined by the cache size and block size. If the number of index bits increases, the number of tag bits decreases because the total address size is fixed at 32 bits.]
