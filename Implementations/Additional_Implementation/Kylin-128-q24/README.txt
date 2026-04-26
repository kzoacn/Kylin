Kylin NGCC SIG implementation instance

This directory contains one Kylin digital-signature instance using the NGCC SIG
API from `SIG_AlgorithmInstance.h`.

Build and test:

    make
    make test

Generate the NGCC KAT file for this instance:

    make kat

`make kat` runs the unmodified ICCS `KAT_SIG.c` driver and copies the resulting
`KAT_SIG_Kylin-*.txt` file to the repository-level `Test_Vectors/` directory.

The ICCS files `KAT_SIG.c`, `auxfunc.c`, `auxfunc.h`, `drng.c`, and `drng.h`
are copied from `docs/API_PKC/Implementations/Reference_Implementation/
AlgorithmInstance/` and kept unchanged.

The implementation uses `pseudoXOF` from `auxfunc.c` for the SPHINCS-alpha hash
and XOF calls, and obtains key-generation and signing randomness from the NGCC
`drng_algorithm` context.
