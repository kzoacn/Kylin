# Kylin Package Metrics

- Host: `Linux-6.18.33.1-microsoft-standard-WSL2-x86_64-with-glibc2.39`
- Compiler: `gcc (Ubuntu 13.3.0-6ubuntu2~24.04.1) 13.3.0`
- Benchmark method: host-local wall-clock milliseconds from the automated `bench_sig` driver on a 32-byte message.
- Memory method: GCC `-fstack-usage` maximum single-frame stack report plus `size bench_sig` section sizes.

| Instance | Impl | KeyGen (ms) | Sign (ms) | Verify (ms) | Max frame (bytes) | Max-frame function | .text | .data | .bss |
| --- | --- | ---: | ---: | ---: | ---: | --- | ---: | ---: | ---: |
| Kylin-128 | opt | 49.246 | 871.313 | 0.568 | 2176 | `thash_wots_chain_4x` | 65444 | 664 | 216528 |
| Kylin-128 | ref | 194.948 | 1746.791 | 1.392 | 1200 | `SPX_bpors_pk_from_sig` | 34302 | 696 | 216472 |
| Kylin-256 | opt | 98.150 | 997.808 | 1.303 | 2960 | `SPX_merkle_gen_root` | 63430 | 704 | 1329552 |
| Kylin-256 | ref | 370.071 | 2322.339 | 3.077 | 2544 | `SPX_merkle_gen_root` | 35294 | 696 | 1329512 |
| Kylin-512 | opt | 325.206 | 21804.592 | 9.078 | 7328 | `SPX_merkle_gen_root` | 66614 | 704 | 14087008 |
| Kylin-512 | ref | 2086.508 | 36862.925 | 33.531 | 6800 | `SPX_merkle_gen_root` | 36623 | 704 | 14086960 |
