# Kylin Package Metrics

- Host: `Linux-6.6.87.2-microsoft-standard-WSL2-x86_64-with-glibc2.39`
- Compiler: `gcc (Ubuntu 13.3.0-6ubuntu2~24.04.1) 13.3.0`
- Benchmark method: host-local wall-clock milliseconds from the automated `bench_sig` driver on a 32-byte message.
- Memory method: GCC `-fstack-usage` maximum single-frame stack report plus `size bench_sig` section sizes.

| Instance | Impl | KeyGen (ms) | Sign (ms) | Verify (ms) | Max frame (bytes) | Max-frame function | .text | .data | .bss |
| --- | --- | ---: | ---: | ---: | ---: | --- | ---: | ---: | ---: |
| Kylin-128 | opt | 127.112 | 2273.504 | 5.298 | 896 | `sm3_bit` | 35152 | 688 | 417832 |
| Kylin-128 | ref | 137.808 | 2323.175 | 5.435 | 880 | `SPX_fors_sign` | 27725 | 688 | 417832 |
| Kylin-256 | opt | 259.104 | 4073.319 | 10.274 | 2144 | `SPX_merkle_gen_root` | 35240 | 688 | 2609352 |
| Kylin-256 | ref | 290.938 | 4181.810 | 10.888 | 1904 | `kylin_sign_verify` | 28157 | 688 | 2609352 |
| Kylin-512 | opt | 1435.642 | 20879.731 | 57.382 | 6656 | `SPX_merkle_gen_root` | 36056 | 688 | 17367208 |
| Kylin-512 | ref | 1584.024 | 21347.615 | 58.648 | 6208 | `kylin_sign_verify` | 29189 | 688 | 17367208 |
