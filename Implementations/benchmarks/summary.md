# Kylin Package Metrics

- Host: `Linux-6.6.87.2-microsoft-standard-WSL2-x86_64-with-glibc2.39`
- Compiler: `gcc (Ubuntu 13.3.0-6ubuntu2~24.04.1) 13.3.0`
- Benchmark method: host-local wall-clock milliseconds from the automated `bench_sig` driver on a 32-byte message.
- Memory method: GCC `-fstack-usage` maximum single-frame stack report plus `size bench_sig` section sizes.

| Instance | Impl | KeyGen (ms) | Sign (ms) | Verify (ms) | Max frame (bytes) | Max-frame function | .text | .data | .bss |
| --- | --- | ---: | ---: | ---: | ---: | --- | ---: | ---: | ---: |
| Kylin-128 | opt | 129.112 | 2293.660 | 5.256 | 896 | `sm3_bit` | 35152 | 688 | 417832 |
| Kylin-128 | ref | 140.777 | 2405.816 | 5.430 | 880 | `SPX_fors_sign` | 27725 | 688 | 417832 |
| Kylin-256 | opt | 260.554 | 4074.893 | 10.320 | 2144 | `SPX_merkle_gen_root` | 35240 | 688 | 2609352 |
| Kylin-256 | ref | 294.203 | 4369.066 | 10.777 | 1904 | `kylin_sign_verify` | 28157 | 688 | 2609352 |
| Kylin-512 | opt | 1430.341 | 20188.727 | 55.029 | 6656 | `SPX_merkle_gen_root` | 36056 | 688 | 17367208 |
| Kylin-512 | ref | 1603.432 | 20940.655 | 59.571 | 6208 | `kylin_sign_verify` | 29189 | 688 | 17367208 |
