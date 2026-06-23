# Input: Message M, signature SIG, public key PK
# Output: Boolean
kylin_verify(M, SIG, PK){ // init
  ADRS = toByte(0, 32);
  R = SIG.getR();
  SIG_BPORS = SIG.getSIG_BPORS();
  SIG_HT = SIG.getSIG_HT();
  // compute message digest and index
  digest = H_msg(R, PK.seed, PK.root, M);
  md = first n bytes of digest;
  tmp_idx_tree = next floor((h - h_0 +7)/ 8) bytes of digest;
  tmp_idx_leaf = next floor((h_0 +7)/ 8) bytes of digest;
  idx_tree = first h - h_0 bits of tmp_idx_tree;
  idx_leaf = first h_0 bits of tmp_idx_leaf;
  // compute BPORS+FP public key
  ADRS.setLayerAddress(0);
  ADRS.setTreeAddress(idx_tree);
  ADRS.setType(BPORS_CHILD_TREE);
  ADRS.setKeyPairAddress(idx_leaf);
  PK_BPORS = bpors_pkFromSig(SIG_BPORS, md, PK.seed, ADRS);
  // verify HT signature
  ADRS.setType(TREE);
  return ht_verify(PK_BPORS, SIG_HT, PK.seed, idx_tree, idx_leaf, PK.root);
}
