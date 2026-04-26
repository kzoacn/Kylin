#ifndef KYLIN_SIGN_H
#define KYLIN_SIGN_H

#include <stdint.h>

int kylin_seed_keypair(unsigned char *pk, unsigned char *sk,
                       const unsigned char *seed);

int kylin_sign_signature(uint8_t *sig, unsigned long long *siglen,
                         const uint8_t *m, unsigned long long mlen,
                         const uint8_t *sk, const uint8_t *optrand);

int kylin_sign_verify(const uint8_t *sig, unsigned long long siglen,
                      const uint8_t *m, unsigned long long mlen,
                      const uint8_t *pk);

#endif
