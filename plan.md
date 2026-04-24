# Kylin NGCC Migration Plan

## Current Repository Knowledge

This project is intended to migrate `SPHINCS-ALPHA-NIST`, a stateless hash-based post-quantum digital signature scheme, into an NGCC-compatible submission package.

Important repository areas:

- `SPHINCS-ALPHA-NIST/`: original NIST submission documentation and code. It must remain read-only.
- `docs/`: NGCC requirements, evaluation criteria, feedback documents, and the ICCS API templates under `docs/API_PKC/`.
- `main.tex` and `paper/`: current English submission document and supporting data/scripts.
- The NGCC implementation package is under `Implementations/`, with reference and optimized first-stage Kylin SIG instances for `Kylin-128`, `Kylin-256`, and `Kylin-512`.

The NGCC documents require, for a digital signature submission:

- key generation, signing, and verification algorithms;
- support for messages up to `2^63` bits;
- at least `2^64` different messages per key pair;
- one reference implementation without platform-specific instructions;
- one optimized implementation for mainstream 64-bit PC processors;
- automated build scripts;
- KAT vectors generated using the ICCS auxiliary program/data;
- source code using the ICCS programming interface from `API_PKC.zip`;
- hash/XOF calls through ICCS auxiliary functions, not through the original SHAKE/SHA2 implementation directly.

The relevant NGCC SIG API is:

- `sig_get_pk_len_bytes()`
- `sig_get_sk_len_bytes()`
- `sig_get_sn_len_bytes()`
- `sig_keygen(...)`
- `sig_sign(...)`
- `sig_verify(...)`

The NGCC helper/template files `KAT_SIG.c`, `auxfunc.*`, and `drng.*` should be copied into each instance directory and then left unmodified.

## Decisions Already Made

The first migration stage targets only three NGCC instances:

- `Kylin-128`
- `Kylin-256`
- `Kylin-512`

The new project/algorithm name should be used now in code-level artifacts, not postponed. Directory names, `ALGORITHM_INSTANCE` macros, and KAT filenames should therefore use `Kylin-*`.

The first-stage parameters come from `paper/data/para_ngcc.csv`. Parameter optimization is explicitly deferred to a later task. The current table incorporates the `Kylin-128` decision to use `n=16` for the 128-bit classical / 80-bit quantum target.

Current parameter table status:

| Instance | NGCC classical/quantum | n | h | d | a | k | w | len | subtree | pk | sk | sig |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `Kylin-128` | 128/80 | 16 | 70 | 10 | 14 | 31 | 64 | 23 | 7 | 32 | 64 | 12256 |
| `Kylin-256` | 256/128 | 32 | 70 | 10 | 14 | 42 | 64 | 45 | 7 | 64 | 128 | 36832 |
| `Kylin-512` | 512/256 | 64 | 70 | 10 | 14 | 65 | 64 | 87 | 7 | 128 | 256 | 122624 |

The parameter script `paper/code/search_ngcc_params.py` currently reproduces the implementation table:

```text
Selected first-stage implementation shape (h, d, a, w): (70, 10, 14, 64)
Kylin-128: n=16, h=70, d=10, a=14, k=31, w=64, len=23, classical=128.0, ngcc_quantum=80, formula_quantum=64.0, pk=32, sk=64, sig=12256, hashcalls=2901248
Kylin-256: n=32, h=70, d=10, a=14, k=42, w=64, len=45, classical=256.0, ngcc_quantum=128, formula_quantum=128.0, pk=64, sk=128, sig=36832, hashcalls=5063936
Kylin-512: n=64, h=70, d=10, a=14, k=65, w=64, len=87, classical=512.0, ngcc_quantum=256, formula_quantum=256.0, pk=128, sk=256, sig=122624, hashcalls=9258240
```

Note: the `Kylin-128` row records the NGCC 80-bit quantum target while the draft's simple `classical/2` formula gives 64 bits for `n=16`. The final security explanation for this row is part of the later parameter discussion.

## Implementation Status

Completed first-stage migration items:

- Created `Implementations/Reference_Implementation/Kylin-128`, `Kylin-256`, and `Kylin-512`.
- Created `Implementations/Optimized_Implementation/Kylin-128`, `Kylin-256`, and `Kylin-512`.
- Added NGCC SIG wrappers `SIG_AlgorithmInstance.h/c` for all six instance directories.
- Kept copied ICCS `KAT_SIG.c`, `auxfunc.*`, and `drng.*` unchanged.
- Replaced SHAKE/SHA2 dependencies with ICCS `pseudoXOF` through `hash_iccs.c` and `thash_iccs.c`.
- Replaced randomness with NGCC `drng_algorithm` / `get_random_number`.
- Generalized WOTSCS encoding with a saturating multi-precision helper that supports `n=16`, `n=32`, and `n=64`.
- Added Makefiles, self-tests, top-level implementation README, and generated reference KAT files in `Test_Vectors/`.

## Implementation Plan

### 1. Create NGCC Package Layout

Create the following repository-local submission package directories:

```text
Implementations/
  Reference_Implementation/
    Kylin-128/
    Kylin-256/
    Kylin-512/
  Optimized_Implementation/
    Kylin-128/
    Kylin-256/
    Kylin-512/
  README
Test_Vectors/
  KAT_SIG_Kylin-128.txt
  KAT_SIG_Kylin-256.txt
  KAT_SIG_Kylin-512.txt
```

For each instance directory, copy the NGCC SIG template/support files from:

```text
docs/API_PKC/Implementations/Reference_Implementation/AlgorithmInstance/
```

Required copied files:

- `SIG_AlgorithmInstance.h`
- `SIG_AlgorithmInstance.c`
- `KAT_SIG.c`
- `auxfunc.h`
- `auxfunc.c`
- `drng.h`
- `drng.c`
- a local `README.txt`

After copying, modify only `SIG_AlgorithmInstance.h`, `SIG_AlgorithmInstance.c`, local SPHINCS/Kylin implementation files, build scripts, and README files. Keep `KAT_SIG.c`, `auxfunc.*`, and `drng.*` unchanged.

### 2. Port the SPHINCS-alpha Core

Use the original reference implementation as source material, especially one of the `Reference_Implementation/sphincs-a-shake-*` trees. Do not edit the original tree.

Bring over the core files needed for the stateless signature:

- address handling;
- context;
- FORS;
- hypertree/Merkle utilities;
- WOTSCS;
- signing and verification flow;
- parameter headers.

Remove or replace dependencies on:

- `/dev/urandom` based `randombytes.c`;
- original `fips202.*`;
- original `sha2.*`;
- OpenSSL KAT machinery;
- NIST `api.h` as the public API surface.

The public interface for NGCC should be the SIG API, not the NIST PQC API.

### 3. Implement Kylin Parameters

For each instance, provide a local `params.h` or equivalent configuration with fixed constants:

- `SPX_N`
- `SPX_FULL_HEIGHT`
- `SPX_D`
- `SPX_FORS_HEIGHT`
- `SPX_FORS_TREES`
- `SPX_WOTS_W`
- `SPX_WOTS_LEN`
- derived byte lengths

The first-stage implementation uses a common shape for all three instances:

- `SPX_FULL_HEIGHT = 70`
- `SPX_D = 10`
- `SPX_FORS_HEIGHT = 14`
- `SPX_WOTS_W = 64`
- subtree height `7`

This common-shape assumption can be revisited during the later parameter-optimization task.

The instance-specific values are:

- `Kylin-128`: `SPX_N=16`, `SPX_FORS_TREES=31`, `SPX_WOTS_LEN=23`
- `Kylin-256`: `SPX_N=32`, `SPX_FORS_TREES=42`, `SPX_WOTS_LEN=45`
- `Kylin-512`: `SPX_N=64`, `SPX_FORS_TREES=65`, `SPX_WOTS_LEN=87`

Set in `SIG_AlgorithmInstance.h`:

- `OUTPUT_BLANK_TEST_VECTORS 0`
- `ALGORITHM_INSTANCE "Kylin-128"` or corresponding instance name

### 4. Replace Hash/XOF Instantiation

NGCC requires the cryptographic hash algorithm and XOF in implementations to use ICCS auxiliary functions.

Use `pseudoXOF` as the common primitive for:

- `prf_addr`
- `gen_message_random`
- `hash_message`
- `thash`

Use explicit domain separation tags for each logical function. The domain tags should be stable byte prefixes, for example:

- `KYLN_PRF_ADDR`
- `KYLN_PRF_MSG`
- `KYLN_H_MSG`
- `KYLN_THASH`

The exact byte layout should be documented in comments and kept identical across reference and optimized implementations.

Recommended layouts:

- `prf_addr`: `tag || pk_seed || ADRS || sk_seed`
- `gen_message_random`: `tag || sk_prf || optrand || message`
- `hash_message`: `tag || R || pk || message`
- `thash`: `tag || pk_seed || ADRS || input_blocks`

For `hash_message`, request exactly:

```text
SPX_FORS_MSG_BYTES + SPX_TREE_BYTES + SPX_LEAF_BYTES
```

bytes from `pseudoXOF`, then parse digest, tree index, and leaf index as in the original code.

### 5. Replace Randomness

In NGCC KAT generation, `KAT_SIG.c` initializes the global:

```c
extern DRNG_ctx drng_algorithm;
```

Implement all signing randomness through:

```c
get_random_number(&drng_algorithm, out, out_len_bits)
```

Use it for:

- key generation seed material;
- per-signature `optrand`.

Do not use `/dev/urandom` or the original `randombytes.c` in the NGCC package.

### 6. Implement SIG API Wrapper

`sig_get_pk_len_bytes`, `sig_get_sk_len_bytes`, and `sig_get_sn_len_bytes` should return the fixed derived sizes for each instance.

`sig_keygen` should:

- validate non-null output pointers;
- draw `3 * SPX_N` seed bytes from `drng_algorithm`;
- call the internal seeded keypair routine;
- write exact key lengths;
- return `0` on success and a negative NGCC-style error code on failure.

`sig_sign` should:

- validate `sk_len_bytes == SPX_SK_BYTES`;
- validate output pointers;
- sign the message using the detached signature format;
- write `SPX_BYTES` to `sn_len_bytes`;
- return `0` on success.

`sig_verify` should:

- validate `pk_len_bytes == SPX_PK_BYTES`;
- validate `sn_len_bytes == SPX_BYTES`;
- return `0` for valid signatures;
- return `-1` for invalid signatures;
- return another negative value only for API/internal errors.

### 7. Generalize WOTSCS Encoding

The original `wots.c` stored the message as `uint256_t`, so it could not correctly support `Kylin-512` with `n=64`. The Kylin port replaces this with a fixed-width saturating multi-precision helper sized from `SPX_N`.

Replace this with a generic fixed-width multi-precision helper whose limb count derives from `SPX_N`:

```text
SPX_MSG_LIMBS = ceil(SPX_N / 8)
```

Required operations:

- zero;
- load big-endian or original-compatible byte order from message digest;
- compare;
- subtract;
- saturated add for DP values.

The DP table values for WOTSCS encoding only need to distinguish whether a count is greater than the maximum encodable message value. To avoid enormous arbitrary precision arithmetic, saturate all DP values at:

```text
2^(8 * SPX_N)
```

or a representation of "larger than any message". This is enough for the encoding decision procedure.

Verify this carefully for all three instances, especially `Kylin-512`.

### 8. Build Scripts

Each instance directory should include a `Makefile` with targets:

- default KAT generator build;
- `test`;
- `kat`;
- `clean`.

Reference implementation flags:

```text
-std=c99 -Wall -Wextra -Wpedantic -O2
```

Optimized implementation flags:

```text
-std=c99 -Wall -Wextra -Wpedantic -O3 -march=native
```

The first optimized implementation can share the same portable C source with stronger compiler flags. Deeper AVX2/vector optimization is deferred to the later optimization task.

### 9. Generate KAT Files

For each reference instance:

1. Build the KAT executable from `KAT_SIG.c`, `SIG_AlgorithmInstance.c`, `auxfunc.c`, `drng.c`, and Kylin core files.
2. Run it.
3. Copy or place the generated output file into root `Test_Vectors/`.
4. Confirm filenames exactly match:
   - `KAT_SIG_Kylin-128.txt`
   - `KAT_SIG_Kylin-256.txt`
   - `KAT_SIG_Kylin-512.txt`

The generated KAT files must be non-empty and contain actual values, not blank templates.

### 10. Update English Documentation

Update `main.tex` and `paper/tex/*` as needed:

- title should refer to Kylin and NGCC;
- basic information table should use Kylin;
- parameter table should display `Kylin-128/256/512`;
- implementation checklist should reflect completed NGCC API package and KAT generation;
- keep remaining external deliverables as TODOs:
  - signed submitter forms;
  - IP statements;
  - optional 32-bit/hardware results;
  - final parameter optimization;
  - Chinese document.

Do not attempt the full Chinese document in this first stage.

## Verification Plan

Run these checks after implementation:

```text
python3 paper/code/search_ngcc_params.py
```

Expected: implementation shape `(70, 10, 14, 64)` and the three current `Kylin-*` parameter rows, with `Kylin-128` using `n=16`.

For each reference instance:

```text
make clean
make
make test
make kat
```

For each optimized instance:

```text
make clean
make
make test
```

Functional checks:

- generated keypair signs and verifies a test message;
- modified message fails verification;
- modified signature fails verification;
- wrong public key fails verification;
- `sig_*_len_bytes` values match the parameter table;
- generated KAT files are deterministic across repeated runs.

Documentation checks:

- LaTeX build succeeds;
- cross references for parameter and submission tables resolve;
- no stale statement says the NGCC implementation package is merely a placeholder once it has been created.

## Deferred Work

These items are intentionally outside the first implementation stage:

- new parameter search/optimization methodology;
- deeper code optimization beyond a first 64-bit `-O3` package;
- full project-wide polish of the Kylin name in every historical discussion;
- signed submission forms and IP declarations;
- Chinese version of the full document;
- optional embedded/hardware implementations and benchmarks.

## Progress Log

### 2026-04-24 - Task 1: Submission Narrative Refresh

- Updated `main.tex` title/author placeholders to use the Kylin submission name.
- Rewrote `paper/tex/abstract.tex` from a research-paper abstract into a submission-package abstract that reflects the current NGCC deliverables.
- Updated `paper/tex/submission_overview.tex` so the basic-information table, message-length statement, correctness statement, and external-deliverable status match the repository's current Kylin package state.
- Removed a stale statement in `paper/tex/sphincsp.tex` that still claimed the repository lacked NGCC implementations and test vectors.

### 2026-04-24 - Task 2: Submission Evidence and Scope Statements

- Added explicit first-stage scope statements for message length, correctness, side-channel scope, single-key vs. multi-key claims, and repeated-key usage in `paper/tex/submission_overview.tex`, `paper/tex/sphincsp.tex`, and `paper/tex/submission_checklist.tex`.
- Added repository-local package benchmark and memory tables to `paper/tex/sphincsp.tex`, backed by generated CSV inputs `paper/data/package_bench.csv` and `paper/data/package_memory.csv`.
- Added a shared benchmark driver at `Implementations/tools/bench_sig.c` and an automated metrics collector at `Implementations/tools/collect_metrics.py`, then generated `Implementations/benchmarks/summary.md`.
- Documented the NGCC message-length bound directly in all six `SIG_AlgorithmInstance.c` wrappers.

### 2026-04-24 - Task 3: Build Automation and Artifact Cleanup

- Added per-instance `bench` and `stack_usage` Makefile targets, and extended `clean` so build/KAT/metrics artifacts are removable in one pass.
- Added a repository-root `Makefile` with `params`, `build`, `test`, `kat`, `metrics`, `clean`, and `verify` targets for package-level automation.
- Updated `Implementations/README` to describe the new top-level workflow and generated metrics outputs.
- Added a root `.gitignore` covering implementation binaries, KAT output directories, stack-usage directories, and LaTeX temporary files.
