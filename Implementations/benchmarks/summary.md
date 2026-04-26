# Kylin Package Metrics

- Host: `Linux-6.6.87.2-microsoft-standard-WSL2-x86_64-with-glibc2.39`
- Compiler: `gcc (Ubuntu 13.3.0-6ubuntu2~24.04.1) 13.3.0`
- Benchmark method: host-local wall-clock milliseconds from the automated `bench_sig` driver on a 32-byte message.
- Memory method: GCC `-fstack-usage` maximum single-frame stack report plus `size bench_sig` section sizes.

| Instance | Impl | KeyGen (ms) | Sign (ms) | Verify (ms) | Max frame (bytes) | Max-frame function | .text | .data | .bss |
| --- | --- | ---: | ---: | ---: | ---: | --- | ---: | ---: | ---: |
| Kylin-128 | opt | 75.058 | 592.035 | 1.989 | 2176 | `thash_wots_chain_4x` | 55041 | 648 | 438032 |
| Kylin-128 | ref | 288.953 | 1813.298 | 5.141 | 704 | `sm3_bit_compress` | 28557 | 688 | 437968 |
| Kylin-256 | opt | 52.720 | 878.207 | 3.299 | 2176 | `SPX_merkle_gen_root` | 57364 | 688 | 2293872 |
| Kylin-256 | ref | 225.417 | 2491.528 | 9.088 | 1904 | `kylin_sign_verify` | 28981 | 688 | 2293832 |
| Kylin-512 | opt | 171.051 | 4369.834 | 22.940 | 6048 | `SPX_merkle_gen_root` | 60996 | 688 | 21847952 |
| Kylin-512 | ref | 1006.842 | 13801.995 | 86.494 | 5648 | `kylin_sign_verify` | 30021 | 688 | 21847912 |
