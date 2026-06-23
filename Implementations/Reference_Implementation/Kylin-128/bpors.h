#ifndef SPX_BPORS_H
#define SPX_BPORS_H

#include <stdint.h>

#include "params.h"
#include "context.h"

#define bpors_sign SPX_NAMESPACE(bpors_sign)
int bpors_sign(unsigned char *sig, unsigned char *pk,
               const unsigned char *m,
               const spx_ctx *ctx,
               const uint32_t bpors_addr[8]);

#define bpors_pk_from_sig SPX_NAMESPACE(bpors_pk_from_sig)
int bpors_pk_from_sig(unsigned char *pk,
                      const unsigned char *sig, const unsigned char *m,
                      const spx_ctx *ctx,
                      const uint32_t bpors_addr[8]);

#endif
