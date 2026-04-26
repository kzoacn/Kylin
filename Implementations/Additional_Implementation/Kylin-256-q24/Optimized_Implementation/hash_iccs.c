#include <limits.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>

#include "address.h"
#include "auxfunc.h"
#include "hash.h"
#include "params.h"
#include "utils.h"

static int xof_with_tag(unsigned char *out, unsigned long long outlen,
                        const unsigned char *tag, unsigned long long taglen,
                        const unsigned char *a, unsigned long long alen,
                        const unsigned char *b, unsigned long long blen,
                        const unsigned char *c, unsigned long long clen,
                        const unsigned char *d, unsigned long long dlen)
{
    unsigned long long inlen = taglen + alen + blen + clen + dlen;
    unsigned char *buf;
    unsigned char *p;
    int ret;

    if (outlen > ULLONG_MAX / 8 || inlen > ULLONG_MAX / 8) {
        return -1;
    }

    buf = (unsigned char *)malloc((size_t)inlen);
    if (buf == 0) {
        return -1;
    }

    p = buf;
    memcpy(p, tag, (size_t)taglen);
    p += taglen;
    if (alen != 0) {
        memcpy(p, a, (size_t)alen);
        p += alen;
    }
    if (blen != 0) {
        memcpy(p, b, (size_t)blen);
        p += blen;
    }
    if (clen != 0) {
        memcpy(p, c, (size_t)clen);
        p += clen;
    }
    if (dlen != 0) {
        memcpy(p, d, (size_t)dlen);
    }

    ret = pseudoXOF(outlen * 8ULL, buf, inlen * 8ULL, out);
    free(buf);
    return ret;
}

void initialize_hash_function(spx_ctx *ctx)
{
    (void)ctx;
}

void prf_addr(unsigned char *out, const spx_ctx *ctx,
              const uint32_t addr[8])
{
    static const unsigned char tag[] = "Kylin-PRF-ADDR-v1";
    if (xof_with_tag(out, SPX_N, tag, sizeof(tag) - 1,
                     ctx->pub_seed, SPX_N,
                     (const unsigned char *)addr, SPX_ADDR_BYTES,
                     ctx->sk_seed, SPX_N,
                     0, 0) != 0) {
        memset(out, 0, SPX_N);
    }
}

void gen_message_random(unsigned char *R, const unsigned char *sk_prf,
                        const unsigned char *optrand,
                        const unsigned char *m, unsigned long long mlen,
                        const spx_ctx *ctx)
{
    static const unsigned char tag[] = "Kylin-PRF-MSG-v1";
    (void)ctx;
    if (xof_with_tag(R, SPX_N, tag, sizeof(tag) - 1,
                     sk_prf, SPX_N,
                     optrand, SPX_N,
                     m, mlen,
                     0, 0) != 0) {
        memset(R, 0, SPX_N);
    }
}

void hash_message(unsigned char *digest, uint64_t *tree, uint32_t *leaf_idx,
                  const unsigned char *R, const unsigned char *pk,
                  const unsigned char *m, unsigned long long mlen,
                  const spx_ctx *ctx)
{
    static const unsigned char tag[] = "Kylin-H-MSG-v1";
    unsigned char buf[SPX_DGST_BYTES];
    unsigned char *bufp = buf;

    (void)ctx;
    if (xof_with_tag(buf, SPX_DGST_BYTES, tag, sizeof(tag) - 1,
                     R, SPX_N,
                     pk, SPX_PK_BYTES,
                     m, mlen,
                     0, 0) != 0) {
        memset(buf, 0, sizeof(buf));
    }

    memcpy(digest, bufp, SPX_FORS_MSG_BYTES);
    bufp += SPX_FORS_MSG_BYTES;

#if SPX_TREE_BITS > 64
#error Subtree addressing is limited to at most 64 bits
#endif

    *tree = bytes_to_ull(bufp, SPX_TREE_BYTES);
    if (SPX_TREE_BITS == 0) {
        *tree = 0;
    } else if (SPX_TREE_BITS < 64) {
        *tree &= (~(uint64_t)0) >> (64 - SPX_TREE_BITS);
    }
    bufp += SPX_TREE_BYTES;

    *leaf_idx = (uint32_t)bytes_to_ull(bufp, SPX_LEAF_BYTES);
    if (SPX_LEAF_BITS == 0) {
        *leaf_idx = 0;
    } else if (SPX_LEAF_BITS < 32) {
        *leaf_idx &= (~(uint32_t)0) >> (32 - SPX_LEAF_BITS);
    }
}
