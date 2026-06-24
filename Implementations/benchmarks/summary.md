# Kylin Package Metrics

- Host: `Linux-6.18.33.1-microsoft-standard-WSL2-x86_64-with-glibc2.39`
- Compiler: `gcc (Ubuntu 13.3.0-6ubuntu2~24.04.1) 13.3.0`
- Benchmark method: host-local wall-clock milliseconds from the automated `bench_sig` driver on a 32-byte message.
- Memory method: GCC `-fstack-usage` maximum single-frame stack report plus `size bench_sig` section sizes.

| Instance | Impl | KeyGen (ms) | Sign (ms) | Verify (ms) | Max frame (bytes) | Max-frame function | .text | .data | .bss |
| --- | --- | ---: | ---: | ---: | ---: | --- | ---: | ---: | ---: |
| Kylin-128 | opt | 73.057 | 486.676 | 1.928 | 2176 | `thash_wots_chain_4x` | 65976 | 664 | 438032 |
| Kylin-128 | ref | 286.336 | 1650.795 | 5.003 | 1216 | `SPX_bpors_pk_from_sig` | 34382 | 696 | 437968 |
| Kylin-256 | opt | 51.544 | 5341.378 | 3.028 | 2720 | `SPX_bpors_pk_from_sig` | 63630 | 704 | 2293872 |
| Kylin-256 | ref | 220.209 | 6940.189 | 8.057 | 2656 | `SPX_bpors_pk_from_sig` | 35423 | 704 | 2293832 |
| Kylin-512 | opt | 166.705 | 6134.908 | 22.733 | 5984 | `SPX_merkle_gen_root` | 67390 | 704 | 22632832 |
| Kylin-512 | ref | 1017.693 | 15952.799 | 89.362 | 5568 | `kylin_sign_verify` | 36975 | 704 | 22632784 |
