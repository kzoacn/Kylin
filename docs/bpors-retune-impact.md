# BPORS+FP Retune Impact Notes

This note records repository areas that changed, or must be checked, when the
bottom few-time layer is BPORS+FP and the six packaged profiles are retuned.

## Parameter Source

- Frozen source of truth: `paper/data/para_kylin_final_6profiles.csv`.
- Reproduction script: `paper/code/search_bpors_kylin_params.py`.
- Independent checker: `paper/code/check_bpors_profiles.py`.
- Historical FORS baseline used for sign/verify hash-call caps:
  `paper/data/para_fors_baseline_6profiles.csv`.

The checker recomputes signature size, BPORS cover bit security,
forced-pruning acceptance probability, child-tree height, and the 105% old-FORS
sign/verify hash-call caps.  The q24 companion rows use a higher practical
forced-pruning floor than the primary rows so that KAT generation does not
spend tens of millions of trials on the counter loop.

## Implementation Files

- `params.h` in all primary and q24 implementation directories must match the
  final CSV.
- q24 `Makefile` KAT targets must copy to repository-root `Test_Vectors/`.
- `Implementations/tools/collect_metrics.py` must discover both nested
  q24 reference and optimized directories.
- `Implementations/README` must list the same six frozen tuples.

## Paper Files

- English source remains authoritative.
- Mirrored Chinese files must be updated for every changed table, address
  description, section heading, caption, and proof/concrete-security row.
- Active construction text should describe BPORS+FP addresses and signatures;
  old FORS algorithm sections should not be active in `paper/tex/kylin.tex` or
  `paper/tex-zh/kylin.tex`.
- Parameter tables, concrete-security tables, and performance hash-call tables
  should be refreshed from the final CSV/checker output.
- Benchmark timing tables should be refreshed after rerunning the implementation
  benchmark driver; until then, old timing rows should not be interpreted as
  measurements for the retuned parameter set.

## Validation

- Run `python3 paper/code/check_bpors_profiles.py`.
- Run `make test` for all primary and q24 reference/optimized instances.
- Regenerate root `Test_Vectors/KAT_SIG_*.txt` from the retuned code.
- Compare reference and optimized KAT outputs for matching instances.
- Rebuild English and Chinese PDFs after document edits.
