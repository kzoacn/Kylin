/*
The software is provided by the Institute of Commercial Cryptography Standards
(ICCS), and is used for algorithm submissions in the Next-generation Commercial
Cryptographic Algorithms Program (NGCC).

ICCS doesn't represent or warrant that the operation of the software will be
uninterrupted or error-free in all cases. ICCS will take no responsibility for
the use of the software or the results thereof, if the software is used for any
other purposes.
*/

#ifndef AUXFUNC_H
#define AUXFUNC_H

#include <stdint.h>

#ifdef __cplusplus
extern "C"
{
#endif

    /// @brief The SM3 hash function
    /// @param[in] digest_len_bits Total bits (only 256) of output digest
    /// @param[in] msg Base address of input message byte array
    /// @param[in] msg_len_bits Total bits of input message
    /// @param[out] digest Base address of output message digest byte array
    /// @return 0 for success, others for error
    int sm3hash(int digest_len_bits, const unsigned char *msg, unsigned long long msg_len_bits, unsigned char *digest);

    /// @brief A pseudo-hash function constructed using SM3 and HMAC-SM3 to generate a 512/768/1024-bit hash value
    ///        It is only used for correctness verification of implementations, and does not guarantee security
    /// @param[in] digest_len_bits Total bits (only 512/768/1024) of output digest
    /// @param[in] msg Base address of input message byte array
    /// @param[in] msg_len_bits Total bits of input message
    /// @param[out] digest Base address of output message digest byte array
    /// @return 0 for success, others for error
    int pseudohash(int digest_len_bits, const unsigned char *msg, unsigned long long msg_len_bits, unsigned char *digest);

    /// @brief An eXtensible Output Function (XOF) constructed using KDF-SM3 to generate an output of specified length
    ///        It is only used for correctness verification of implementations, and does not guarantee security
    /// @param[in] output_len_bits Total bits (less than (2^40-2^8)) of output
    /// @param[in] msg Base address of input message byte array
    /// @param[in] msg_len_bits Total bits of input message
    /// @param[out] output Base address of output byte array
    /// @return 0 for success, others for error
    int pseudoXOF(unsigned long long output_len_bits, const unsigned char *msg, unsigned long long msg_len_bits, unsigned char *output);

    /// @brief 4-way SSE2 WOTS chain step — processes 4 chains in parallel
    /// @param[out] out 4*32 = 128 bytes output (contiguous per chain)
    /// @param[in]  in  4*32 = 128 bytes input (contiguous per chain)
    /// @param[in]  pub_seed 32 bytes public seed
    /// @param[in]  addrs 4 address arrays (addrs[0..3][0..7])
    void thash_wots_chain_4x(unsigned char *out, const unsigned char *in,
                             const unsigned char *pub_seed,
                             const uint32_t addrs[4][8]);

#ifdef __cplusplus
}
#endif

#endif
