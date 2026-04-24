# Input: (none)
# Output: $\SPHINCSA$ key pair (SK,PK)
spa_keygen( ){
  SK.seed = sec_rand(n);
  SK.prf = sec_rand(n);
  PK.seed = sec_rand(n);
  PK.root = ht_PKgen(SK.seed, PK.seed);
  return ( (SK.seed, SK.prf, PK.seed, PK.root), (PK.seed, PK.root) );
}