# Input: Message M, private key SK = (SK.seed, SK.prf, PK.seed, PK.root)
# Output: $\SPHINCSA$ signature SIG
spa_sign(M, SK){ // init
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
  tmp_md = first floor((ka +7)/ 8) bytes of digest;
  tmp_idx_tree = next floor((h - h/d +7)/ 8) bytes of digest;
  tmp_idx_leaf = next floor((h/d +7)/ 8) bytes of digest;
  md = first ka bits of tmp_md;
  idx_tree = first h - h/d bits of tmp_idx_tree;
  idx_leaf = first h/d bits of tmp_idx_leaf;
  // FORS sign
  ADRS.setLayerAddress(0);
  ADRS.setTreeAddress(idx_tree);
  ADRS.setType(FORS_TREE);
  ADRS.setKeyPairAddress(idx_leaf);
  SIG_FORS = fors_sign(md, SK.seed, PK.seed, ADRS);
  SIG = SIG || SIG_FORS;
  // get FORS public key
  PK_FORS = fors_pkFromSig(SIG_FORS, md, PK.seed, ADRS);
  // sign FORS public key with HT
  ADRS.setType(TREE);
  SIG_HT = ht_sign(PK_FORS, SK.seed, PK.seed, idx_tree, idx_leaf);
  SIG = SIG || SIG_HT;
  return SIG; 
}