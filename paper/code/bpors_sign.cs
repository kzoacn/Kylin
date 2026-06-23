# Input: n-byte string M, secret seed SK.seed, address ADRS, public seed PK.seed
# Output: BPORS+FP signature SIG_BPORS and public key PK_BPORS
bpors_sign(M, SK.seed, PK.seed, ADRS) {
  ctr = 0;
  do {
    (bucket[0..K-1], I[0..K-1]) = bpors_encode(M, ctr, PK.seed, ADRS);
    A_tot = K*B;
    for (c = 0; c < K; c++) {
      AUTH_child[c] = Octopus(t, I[c]);
      A_tot = A_tot + size(AUTH_child[c]);
    }
    ctr = ctr + 1;
  } while (A_tot > m_max);

  SIG_BPORS = SIG_BPORS || toByte(ctr - 1, c_ctr);
  for (c = 0; c < K; c++) {
    for (j = 0; j < k; j++) {
      SIG_BPORS = SIG_BPORS || bpors_SKgen(SK.seed, ADRS, c, bucket[c], I[c][j]);
    }
  }

  for (c = 0; c < K; c++) {
    (PK_child[c], AUTH_values) =
        bpors_child_open(SK.seed, PK.seed, ADRS, c, bucket[c], I[c]);
    SIG_BPORS = SIG_BPORS || AUTH_values;
    (root[c], AUTH_outer) =
        bpors_outer_open(SK.seed, PK.seed, ADRS, c, bucket[c]);
    SIG_BPORS = SIG_BPORS || AUTH_outer;
  }

  SIG_BPORS = SIG_BPORS || zero padding to m_max authentication nodes;
  bporspkADRS = ADRS;
  bporspkADRS.setType(BPORS_ROOTS);
  PK_BPORS = T_K(PK.seed, bporspkADRS, root);
  return (SIG_BPORS, PK_BPORS);
}
