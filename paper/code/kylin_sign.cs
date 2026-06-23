# Input: Message M, private key SK = (SK.seed, SK.prf, PK.seed, PK.root)
# Output: $\SPHINCSA$ signature SIG
kylin_sign(M, SK){ // init
ADRS = toByte(0, 32);
  // generate randomizer
  opt = PK.seed;
  if(RANDOMIZE){
    opt = rand(n);
  }
  R = PRF_msg(SK.prf, opt, M);
  SIG = SIG || R;
  // compute message digest and index
  digest = H_msg(R, PK.seed, PK.root, M);
  md = first n bytes of digest;
  tmp_idx_tree = next floor((h - h_0 +7)/ 8) bytes of digest;
  tmp_idx_leaf = next floor((h_0 +7)/ 8) bytes of digest;
  idx_tree = first h - h_0 bits of tmp_idx_tree;
  idx_leaf = first h_0 bits of tmp_idx_leaf;
  // BPORS+FP sign
  ADRS.setLayerAddress(0);
  ADRS.setTreeAddress(idx_tree);
  ADRS.setType(BPORS_CHILD_TREE);
  ADRS.setKeyPairAddress(idx_leaf);
  (SIG_BPORS, PK_BPORS) = bpors_sign(md, SK.seed, PK.seed, ADRS);
  SIG = SIG || SIG_BPORS;
  // sign BPORS+FP public key with HT
  ADRS.setType(TREE);
  SIG_HT = ht_sign(PK_BPORS, SK.seed, PK.seed, idx_tree, idx_leaf);
  SIG = SIG || SIG_HT;
  return SIG; 
}
