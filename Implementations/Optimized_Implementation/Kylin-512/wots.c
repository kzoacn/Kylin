#include <assert.h>
#include <stdbool.h>
#include <stdint.h>
#include <string.h>

#include "utils.h"
#include "utilsx1.h"
#include "hash.h"
#include "thash.h"
#include "wots.h"
#include "wotsx1.h"
#include "address.h"
#include "params.h"

#define SPX_BIGINT_BITS (8 * SPX_N + 1)
#define SPX_BIGINT_LIMBS ((SPX_BIGINT_BITS + 63) / 64)

typedef struct {
    uint64_t limb[SPX_BIGINT_LIMBS];
} spx_bigint;

static void gen_chain(unsigned char *out, const unsigned char *in,
                      unsigned int start, unsigned int steps,
                      const spx_ctx *ctx, uint32_t addr[8])
{
    uint32_t i;

    memcpy(out, in, SPX_N);

    for (i = start; i < (start + steps) && i < SPX_WOTS_W; i++) {
        set_hash_addr(addr, i);
        thash(out, out, 1, ctx, addr);
    }
}

static void big_set_zero(spx_bigint *z)
{
    memset(z, 0, sizeof(*z));
}

static void big_set_one(spx_bigint *z)
{
    big_set_zero(z);
    z->limb[0] = 1;
}

static void big_set_limit(spx_bigint *z)
{
    unsigned int bit = 8 * SPX_N;
    big_set_zero(z);
    z->limb[bit / 64] = (uint64_t)1 << (bit % 64);
}

static bool big_less(const spx_bigint *x, const spx_bigint *y)
{
    int i;
    for (i = SPX_BIGINT_LIMBS - 1; i >= 0; i--) {
        if (x->limb[i] != y->limb[i]) {
            return x->limb[i] < y->limb[i];
        }
    }
    return false;
}

static void big_add_saturated(spx_bigint *z, const spx_bigint *x,
                              const spx_bigint *y)
{
    spx_bigint limit;
    uint64_t carry = 0;
    unsigned int i;

    big_set_zero(z);
    for (i = 0; i < SPX_BIGINT_LIMBS; i++) {
        uint64_t a = x->limb[i];
        uint64_t b = y->limb[i];
        uint64_t sum = a + b;
        uint64_t carry1 = sum < a;
        uint64_t sum2 = sum + carry;
        uint64_t carry2 = sum2 < sum;
        z->limb[i] = sum2;
        carry = carry1 | carry2;
    }

    big_set_limit(&limit);
    if (carry || !big_less(z, &limit)) {
        *z = limit;
    }
}

static void big_sub(spx_bigint *z, const spx_bigint *x, const spx_bigint *y)
{
    uint64_t borrow = 0;
    unsigned int i;

    for (i = 0; i < SPX_BIGINT_LIMBS; i++) {
        uint64_t a = x->limb[i];
        uint64_t b = y->limb[i];
        uint64_t diff = a - b;
        uint64_t borrow1 = a < b;
        uint64_t diff2 = diff - borrow;
        uint64_t borrow2 = diff < borrow;
        z->limb[i] = diff2;
        borrow = borrow1 | borrow2;
    }
}

static void big_from_bytes(spx_bigint *z, const unsigned char *msg)
{
    unsigned int i;

    big_set_zero(z);
    for (i = 0; i < SPX_N; i++) {
        unsigned int shift = (SPX_N - 1 - i) * 8;
        z->limb[shift / 64] |= (uint64_t)msg[i] << (shift % 64);
    }
}

static void encode(unsigned int *out, spx_bigint *x)
{
    static int done = 0;
    static spx_bigint dp[SPX_WOTS_LEN + 1][SPX_WOTS_SUM + 1];
    int s = SPX_WOTS_SUM;
    int i;

    if (!done) {
        big_set_one(&dp[0][0]);
        for (i = 1; i <= SPX_WOTS_LEN; i++) {
            int j;
            for (j = 0; j <= SPX_WOTS_SUM; j++) {
                int k;
                big_set_zero(&dp[i][j]);
                for (k = 0; k < SPX_WOTS_W && k <= j; k++) {
                    spx_bigint tmp;
                    big_add_saturated(&tmp, &dp[i][j], &dp[i - 1][j - k]);
                    dp[i][j] = tmp;
                }
            }
        }
        done = 1;
    }

    for (i = SPX_WOTS_LEN - 1; i >= 0; i--) {
        int j;
        int t = -1;
        for (j = 0; j < SPX_WOTS_W && j <= s; j++) {
            if (!big_less(x, &dp[i][s - j])) {
                big_sub(x, x, &dp[i][s - j]);
            } else {
                t = j;
                break;
            }
        }
        assert(t != -1);
        out[SPX_WOTS_LEN - 1 - i] = (unsigned int)t;
        s -= t;
    }
}

void chain_lengths(unsigned int *lengths, const unsigned char *msg)
{
    spx_bigint m;

    big_from_bytes(&m, msg);
    encode(lengths, &m);
}

void wots_pk_from_sig(unsigned char *pk,
                      const unsigned char *sig, const unsigned char *msg,
                      const spx_ctx *ctx, uint32_t addr[8])
{
    unsigned int lengths[SPX_WOTS_LEN];
    uint32_t i;

    chain_lengths(lengths, msg);

    for (i = 0; i < SPX_WOTS_LEN; i++) {
        set_chain_addr(addr, i);
        gen_chain(pk + i * SPX_N, sig + i * SPX_N,
                  lengths[i], SPX_WOTS_W - 1 - lengths[i], ctx, addr);
    }
}
