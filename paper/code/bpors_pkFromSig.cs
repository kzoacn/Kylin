# Input: BPORS+FP signature SIG_BPORS, n-byte string M, public seed PK.seed, address ADRS
# Output: BPORS+FP public key PK_BPORS, or fail
bpors_pkFromSig(SIG_BPORS, M, PK.seed, ADRS) {
  ctr = SIG_BPORS.getCounter();
  (bucket[0..K-1], I[0..K-1]) = bpors_encode(M, ctr, PK.seed, ADRS);
  A_tot = K*B;
  for (c = 0; c < K; c++) {
    AUTH_child[c] = Octopus(t, I[c]);
    A_tot = A_tot + size(AUTH_child[c]);
  }
  if (A_tot > m_max) {
    return fail;
  }

  for (c = 0; c < K; c++) {
    for (j = 0; j < k; j++) {
      sk[j] = SIG_BPORS.getSK(c, j);
      leaf[j] = F(PK.seed, childTreeADRS(ADRS, c, bucket[c], I[c][j]), sk[j]);
    }
    PK_child[c] =
        bpors_child_rootFromSig(leaf, SIG_BPORS.getChildAUTH(c), I[c], PK.seed, ADRS);
    root[c] =
        bpors_outer_rootFromSig(PK_child[c], SIG_BPORS.getOuterAUTH(c),
                                bucket[c], PK.seed, ADRS);
  }

  if (SIG_BPORS.paddingIsNonzero()) {
    return fail;
  }
  bporspkADRS = ADRS;
  bporspkADRS.setType(BPORS_ROOTS);
  PK_BPORS = T_K(PK.seed, bporspkADRS, root);
  return PK_BPORS;
}
