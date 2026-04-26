# Kylin Package Metrics

- Host: `Linux-6.6.87.2-microsoft-standard-WSL2-x86_64-with-glibc2.39`
- Compiler: `gcc (Ubuntu 13.3.0-6ubuntu2~24.04.1) 13.3.0`
- Benchmark method: host-local wall-clock milliseconds from the automated `bench_sig` driver on a 32-byte message.
- Memory method: GCC `-fstack-usage` maximum single-frame stack report plus `size bench_sig` section sizes.

| Instance | Impl | KeyGen (ms) | Sign (ms) | Verify (ms) | Max frame (bytes) | Max-frame function | .text | .data | .bss |
| --- | --- | ---: | ---: | ---: | ---: | --- | ---: | ---: | ---: |
| Kylin-128 | opt | 74.794 | 589.819 | 4.662 | 2176 | `auxfunc.c:774:6:thash_wots_chain_4x` | 52801 | 648 | 438032 |
| Kylin-128 | ref | 291.231 | 1809.888 | 5.184 | 704 | `auxfunc.c:50:13:sm3_bit_compress` | 28557 | 688 | 437968 |
| Kylin-256 | opt | 52.559 | 873.686 | 8.034 | 2176 | `merkle.c:46:6:SPX_merkle_gen_root` | 56252 | 688 | 2293872 |
| Kylin-256 | ref | 224.785 | 2498.940 | 9.173 | 1904 | `kylin_sign.c:106:5:kylin_sign_verify` | 28981 | 688 | 2293832 |
| Kylin-512 | opt | 171.275 | 4377.480 | 79.168 | 6048 | `merkle.c:46:6:SPX_merkle_gen_root` | 59836 | 688 | 21847952 |
| Kylin-512 | ref | 1003.814 | 13993.516 | 87.607 | 5648 | `kylin_sign.c:106:5:kylin_sign_verify` | 30021 | 688 | 21847912 |
