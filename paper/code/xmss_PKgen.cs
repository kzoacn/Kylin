# Input: Secret seed SK.seed, public seed PK.seed, address ADRS
# Output: XMSS public key PK
xmss_PKgen(SK.seed, PK.seed, ADRS) {
  pk = treehash(SK.seed, 0, |\texttt{h\_XMSS}|, PK.seed, ADRS)
  return pk; 
}
