#Input: secret seed SK.seed, address ADRS, secret key index idx = it+j
#Output: FORS private key sk
fors_SKgen(SK.seed, ADRS, idx) {
  skADRS = ADRS; // copy address to create key generation address 
  skADRS.setType(FORS_PRF); 
  skADRS.setKeyPairAddress(ADRS.getKeyPairAddress());

  skADRS.setTreeHeight(0);
  skADRS.setTreeIndex(idx);
  sk = PRF(SK.seed, skADRS);
  return sk; 
}