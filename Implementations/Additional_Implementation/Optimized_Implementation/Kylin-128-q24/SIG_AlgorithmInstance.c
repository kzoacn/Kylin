#include <limits.h>
#include <stdint.h>
#include <string.h>

#include "SIG_AlgorithmInstance.h"
#include "params.h"
#include "kylin_sign.h"
#include "drng.h"

extern DRNG_ctx drng_algorithm;

#define SIG_OK 0
#define SIG_INVALID_SIGNATURE (-1)
#define SIG_API_ERROR (-2)
#define SIG_RNG_ERROR (-3)

static int valid_message_length(unsigned long long m_len_bytes)
{
    /* 2^63 bits equals 2^60 bytes, matching the NGCC submission bound. */
    return m_len_bytes <= (1ULL << 60);
}

unsigned long long sig_get_pk_len_bytes()
{
    return SPX_PK_BYTES;
}

unsigned long long sig_get_sk_len_bytes()
{
    return SPX_SK_BYTES;
}

unsigned long long sig_get_sn_len_bytes()
{
    return SPX_BYTES;
}

int sig_keygen(
    unsigned char *pk, unsigned long long *pk_len_bytes,
    unsigned char *sk, unsigned long long *sk_len_bytes)
{
    unsigned char seed[SPX_SEED_BYTES];

    if (pk == 0 || pk_len_bytes == 0 || sk == 0 || sk_len_bytes == 0) {
        return SIG_API_ERROR;
    }

    if (get_random_number(&drng_algorithm, seed, SPX_SEED_BYTES * 8ULL) != 0) {
        memset(seed, 0, sizeof(seed));
        return SIG_RNG_ERROR;
    }

    kylin_seed_keypair(pk, sk, seed);
    memset(seed, 0, sizeof(seed));

    *pk_len_bytes = SPX_PK_BYTES;
    *sk_len_bytes = SPX_SK_BYTES;
    return SIG_OK;
}

int sig_sign(
    unsigned char *sk, unsigned long long sk_len_bytes,
    unsigned char *m, unsigned long long m_len_bytes,
    unsigned char *sn, unsigned long long *sn_len_bytes)
{
    unsigned char optrand[SPX_N];

    if (sk == 0 || sn == 0 || sn_len_bytes == 0) {
        return SIG_API_ERROR;
    }
    if (m_len_bytes != 0 && m == 0) {
        return SIG_API_ERROR;
    }
    if (sk_len_bytes != SPX_SK_BYTES || !valid_message_length(m_len_bytes)) {
        return SIG_API_ERROR;
    }

    if (get_random_number(&drng_algorithm, optrand, SPX_N * 8ULL) != 0) {
        memset(optrand, 0, sizeof(optrand));
        return SIG_RNG_ERROR;
    }

    kylin_sign_signature(sn, sn_len_bytes, m, m_len_bytes, sk, optrand);
    memset(optrand, 0, sizeof(optrand));
    return SIG_OK;
}

int sig_verify(
    unsigned char *pk, unsigned long long pk_len_bytes,
    unsigned char *sn, unsigned long long sn_len_bytes,
    unsigned char *m, unsigned long long m_len_bytes)
{
    if (pk == 0 || sn == 0) {
        return SIG_API_ERROR;
    }
    if (m_len_bytes != 0 && m == 0) {
        return SIG_API_ERROR;
    }
    if (pk_len_bytes != SPX_PK_BYTES || sn_len_bytes != SPX_BYTES ||
        !valid_message_length(m_len_bytes)) {
        return SIG_API_ERROR;
    }

    if (kylin_sign_verify(sn, sn_len_bytes, m, m_len_bytes, pk) != 0) {
        return SIG_INVALID_SIGNATURE;
    }

    return SIG_OK;
}
