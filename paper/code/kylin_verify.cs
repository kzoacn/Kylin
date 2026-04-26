# Input: Message M, signature SIG, public key PK
# Output: Boolean
kylin_verify(M, SIG, PK){ // init
  ADRS = toByte(0, 32);
  R = SIG.getR();
  SIG_FORS = SIG.getSIG_FORS();
  SIG_HT = SIG.getSIG_HT();
  // compute message digest and index
  digest = H_msg(R, PK.seed, PK.root, M);
  tmp_md = first floor((ka +7)/ 8) bytes of digest;
  tmp_idx_tree = next floor((h - h_0 +7)/ 8) bytes of digest;
  tmp_idx_leaf = next floor((h_0 +7)/ 8) bytes of digest;
  md = first ka bits of tmp_md;
  idx_tree = first h - h_0 bits of tmp_idx_tree;
  idx_leaf = first h_0 bits of tmp_idx_leaf;
  // compute FORS public key
  ADRS.setLayerAddress(0);
  ADRS.setTreeAddress(idx_tree);
  ADRS.setType(FORS_TREE);
  ADRS.setKeyPairAddress(idx_leaf);
  PK_FORS = fors_pkFromSig(SIG_FORS, md, PK.seed, ADRS);
  // verify HT signature
  ADRS.setType(TREE);
  return ht_verify(PK_FORS, SIG_HT, PK.seed, idx_tree, idx_leaf, PK.root);
}
