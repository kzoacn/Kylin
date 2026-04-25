#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "SIG_AlgorithmInstance.h"
#include "drng.h"

DRNG_ctx drng_algorithm;

static int fail(const char *what)
{
    fprintf(stderr, "%s\n", what);
    return 1;
}

int main(void)
{
    unsigned char seed[64];
    unsigned char msg[] = "Kylin NGCC signature self-test";
    unsigned char *pk;
    unsigned char *sk;
    unsigned char *sig;
    unsigned long long pk_len = sig_get_pk_len_bytes();
    unsigned long long sk_len = sig_get_sk_len_bytes();
    unsigned long long sig_len = sig_get_sn_len_bytes();
    unsigned long long out_pk_len = 0;
    unsigned long long out_sk_len = 0;
    unsigned long long out_sig_len = 0;
    int ret;

    memset(seed, 0x4b, sizeof(seed));
    if (init_random_number(&drng_algorithm, seed, sizeof(seed)) != 0) {
        return fail("DRNG initialization failed");
    }

    pk = (unsigned char *)calloc((size_t)pk_len, 1);
    sk = (unsigned char *)calloc((size_t)sk_len, 1);
    sig = (unsigned char *)calloc((size_t)sig_len, 1);
    if (pk == 0 || sk == 0 || sig == 0) {
        return fail("allocation failed");
    }

    ret = sig_keygen(pk, &out_pk_len, sk, &out_sk_len);
    if (ret != 0 || out_pk_len != pk_len || out_sk_len != sk_len) {
        return fail("sig_keygen failed");
    }

    ret = sig_sign(sk, sk_len, msg, sizeof(msg) - 1, sig, &out_sig_len);
    if (ret != 0 || out_sig_len != sig_len) {
        return fail("sig_sign failed");
    }

    if (sig_verify(pk, pk_len, sig, sig_len, msg, sizeof(msg) - 1) != 0) {
        return fail("valid signature rejected");
    }

    msg[0] ^= 1;
    if (sig_verify(pk, pk_len, sig, sig_len, msg, sizeof(msg) - 1) == 0) {
        return fail("modified message accepted");
    }
    msg[0] ^= 1;

    sig[0] ^= 1;
    if (sig_verify(pk, pk_len, sig, sig_len, msg, sizeof(msg) - 1) == 0) {
        return fail("modified signature accepted");
    }

    free(sig);
    free(sk);
    free(pk);
    return 0;
}
