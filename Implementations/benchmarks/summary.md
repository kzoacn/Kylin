# Kylin Package Metrics

- Host: `Linux-6.6.87.2-microsoft-standard-WSL2-x86_64-with-glibc2.39`
- Compiler: `gcc (Ubuntu 13.3.0-6ubuntu2~24.04.1) 13.3.0`
- Benchmark method: host-local wall-clock milliseconds from the automated `bench_sig` driver on a 32-byte message.
- Memory method: GCC `-fstack-usage` maximum single-frame stack report plus `size bench_sig` section sizes.

| Instance | Impl | KeyGen (ms) | Sign (ms) | Verify (ms) | Max frame (bytes) | Max-frame function | .text | .data | .bss |
| --- | --- | ---: | ---: | ---: | ---: | --- | ---: | ---: | ---: |
| Kylin-128 | opt | 131.420 | 2308.762 | 5.329 | 896 | `sm3_bit` | 35152 | 688 | 417832 |
| Kylin-128 | ref | 140.072 | 2425.882 | 5.425 | 880 | `SPX_fors_sign` | 27725 | 688 | 417832 |
| Kylin-256 | opt | 270.257 | 4166.231 | 10.348 | 2144 | `SPX_merkle_gen_root` | 35240 | 688 | 2609352 |
| Kylin-256 | ref | 294.484 | 4305.607 | 11.075 | 1904 | `kylin_sign_verify` | 28157 | 688 | 2609352 |
| Kylin-512 | opt | 1089.656 | 13421.444 | 83.670 | 6048 | `SPX_merkle_gen_root` | 36120 | 688 | 21847912 |
| Kylin-512 | ref | 1301.560 | 13865.691 | 87.474 | 5648 | `kylin_sign_verify` | 29405 | 688 | 21847912 |
