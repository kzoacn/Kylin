#include <stdint.h>
#include <stdlib.h>
#include <string.h>

#include "auxfunc.h"
#include "params.h"
#include "thash.h"

void thash(unsigned char *out, const unsigned char *in, unsigned int inblocks,
           const spx_ctx *ctx, uint32_t addr[8])
{
    static const unsigned char tag[] = "Kylin-THASH-v1";
    const unsigned long long taglen = sizeof(tag) - 1;
    const unsigned long long inlen = taglen + SPX_N + SPX_ADDR_BYTES +
                                     (unsigned long long)inblocks * SPX_N;
    unsigned char *buf = (unsigned char *)malloc((size_t)inlen);
    unsigned char *p = buf;

    if (buf == 0) {
        memset(out, 0, SPX_N);
        return;
    }

    memcpy(p, tag, (size_t)taglen);
    p += taglen;
    memcpy(p, ctx->pub_seed, SPX_N);
    p += SPX_N;
    memcpy(p, addr, SPX_ADDR_BYTES);
    p += SPX_ADDR_BYTES;
    memcpy(p, in, (size_t)inblocks * SPX_N);

    if (pseudoXOF(SPX_N * 8ULL, buf, inlen * 8ULL, out) != 0) {
        memset(out, 0, SPX_N);
    }
    free(buf);
}
