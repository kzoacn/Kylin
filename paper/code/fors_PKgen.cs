# Input: Secret seed SK.seed, public seed PK.seed, address ADRS
# Output: FORS public key PK
fors_PKgen(SK.seed, PK.seed, ADRS) {
  forspkADRS = ADRS; // copy address to create FTS public key address
  for(i = 0; i < k; i++){
    root[i] = fors_treehash(SK.seed, i*t, a, PK.seed, ADRS);
  }
  forspkADRS.setType(FORS_ROOTS);
  forspkADRS.setKeyPairAddress(ADRS.getKeyPairAddress());
  pk = T_k(PK.seed, forspkADRS, root);
  return pk; 
}