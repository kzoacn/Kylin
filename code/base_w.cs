# Input: len_X-byte string X, int w, output length out_len
# Output: out_len int array basew

base_w(X, w, out_len) {
    int in = 0;
    int out = 0;
    unsigned int total = 0;
    int bits = 0;
    int consumed;
    for ( consumed = 0; consumed < out_len; consumed++ ) {
        if ( bits == 0 ) {
            total = X[in];
            in++;
            bits += 8;
    }
    bits -= lg(w);
          basew[out] = (total >> bits) AND (w - 1);
          out++;
    }
      return basew;
}