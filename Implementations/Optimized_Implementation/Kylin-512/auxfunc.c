/*
The software is provided by the Institute of Commercial Cryptography Standards
(ICCS), and is used for algorithm submissions in the Next-generation Commercial
Cryptographic Algorithms Program (NGCC).

ICCS doesn't represent or warrant that the operation of the software will be
uninterrupted or error-free in all cases. ICCS will take no responsibility for
the use of the software or the results thereof, if the software is used for any
other purposes.
*/

#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include "auxfunc.h"

#define L1 512
#define L2 256
#define HASH_SUCCESS 0
#define XOF_SUCCESS 0
#define MEMORY_ALLOCATION_FAILED -2
#define HASH_FAILED -3
#define INVALID_DIGESTBITLEN -4

#define FF1(x, y, z) ((x) ^ (y) ^ (z))
#define FF2(x, y, z) (((x) & (y)) | ((x) & (z)) | ((y) & (z)))
#define GG1(x, y, z) ((x) ^ (y) ^ (z))
#define GG2(x, y, z) ((((y) ^ (z)) & (x)) ^ (z))
#define L_SHIFT(a, n) ((a) << (n) | ((a) & 0xFFFFFFFF) >> (32 - (n)))
#define P0(x) ((x) ^ L_SHIFT((x), 9) ^ L_SHIFT((x), 17))
#define P1(x) ((x) ^ L_SHIFT((x), 15) ^ L_SHIFT((x), 23))
#define PUT32(a, b) ((a)[0] = (unsigned char)((b) >> 24), \
					 (a)[1] = (unsigned char)((b) >> 16), \
					 (a)[2] = (unsigned char)((b) >> 8),  \
					 (a)[3] = (unsigned char)(b))

#if defined(__x86_64__) || defined(__i386__) || defined(_M_X64) || defined(_M_IX86)
#define SM3_HAS_X86_DISPATCH 1
#include <immintrin.h>
#else
#define SM3_HAS_X86_DISPATCH 0
#endif

static inline unsigned int load_u32_be(const unsigned char *in)
{
	return ((unsigned int)in[0] << 24) |
	       ((unsigned int)in[1] << 16) |
	       ((unsigned int)in[2] << 8) |
	       ((unsigned int)in[3]);
}

static const unsigned int sm3_tj_rot[64] = {
	0x79CC4519U, 0xF3988A32U, 0xE7311465U, 0xCE6228CBU,
	0x9CC45197U, 0x3988A32FU, 0x7311465EU, 0xE6228CBCU,
	0xCC451979U, 0x988A32F3U, 0x311465E7U, 0x6228CBCEU,
	0xC451979CU, 0x88A32F39U, 0x11465E73U, 0x228CBCE6U,
	0x9D8A7A87U, 0x3B14F50FU, 0x7629EA1EU, 0xEC53D43CU,
	0xD8A7A879U, 0xB14F50F3U, 0x629EA1E7U, 0xC53D43CEU,
	0x8A7A879DU, 0x14F50F3BU, 0x29EA1E76U, 0x53D43CECU,
	0xA7A879D8U, 0x4F50F3B1U, 0x9EA1E762U, 0x3D43CEC5U,
	0x7A879D8AU, 0xF50F3B14U, 0xEA1E7629U, 0xD43CEC53U,
	0xA879D8A7U, 0x50F3B14FU, 0xA1E7629EU, 0x43CEC53DU,
	0x879D8A7AU, 0x0F3B14F5U, 0x1E7629EAU, 0x3CEC53D4U,
	0x79D8A7A8U, 0xF3B14F50U, 0xE7629EA1U, 0xCEC53D43U,
	0x9D8A7A87U, 0x3B14F50FU, 0x7629EA1EU, 0xEC53D43CU,
	0xD8A7A879U, 0xB14F50F3U, 0x629EA1E7U, 0xC53D43CEU,
	0x8A7A879DU, 0x14F50F3BU, 0x29EA1E76U, 0x53D43CECU,
	0xA7A879D8U, 0x4F50F3B1U, 0x9EA1E762U, 0x3D43CEC5U
};

// GB/T 32905-2016
static void sm3_bit_init(unsigned int *init_digest)
{
	init_digest[0] = 0x7380166F;
	init_digest[1] = 0x4914B2B9;
	init_digest[2] = 0x172442D7;
	init_digest[3] = 0xDA8A0600;
	init_digest[4] = 0xA96F30BC;
	init_digest[5] = 0x163138AA;
	init_digest[6] = 0xE38DEE4D;
	init_digest[7] = 0xB0FB0E4E;
}

/* Macro-based fully unrolled SM3 round */
#define SM3_R_FF1(r) do { \
	Wj = W[r] ^ W[r + 4]; \
	SS1 = L_SHIFT(L_SHIFT(A, 12) + E + sm3_tj_rot[r], 7); \
	SS2 = SS1 ^ L_SHIFT(A, 12); \
	TT1 = FF1(A, B, C) + D + SS2 + Wj; \
	TT2 = GG1(E, F, G) + H + SS1 + W[r]; \
	D = C; C = L_SHIFT(B, 9); B = A; A = TT1; \
	H = G; G = L_SHIFT(F, 19); F = E; E = P0(TT2); \
} while (0)

#define SM3_R_FF2(r) do { \
	Wj = W[r] ^ W[r + 4]; \
	SS1 = L_SHIFT(L_SHIFT(A, 12) + E + sm3_tj_rot[r], 7); \
	SS2 = SS1 ^ L_SHIFT(A, 12); \
	TT1 = FF2(A, B, C) + D + SS2 + Wj; \
	TT2 = GG2(E, F, G) + H + SS1 + W[r]; \
	D = C; C = L_SHIFT(B, 9); B = A; A = TT1; \
	H = G; G = L_SHIFT(F, 19); F = E; E = P0(TT2); \
} while (0)

static void sm3_bit_compress_core(unsigned int dgst[8], const unsigned char *msg, unsigned long long blocks, int use_simd_loader)
{
	unsigned int A, B, C, D, E, F, G, H;
	unsigned int W[68];
	unsigned int SS1, SS2, TT1, TT2;
	unsigned int Wj;
	unsigned int i;

	while (blocks--)
	{
		if (use_simd_loader)
		{
			#if SM3_HAS_X86_DISPATCH
			{
				const __m128i shuffle = _mm_setr_epi8(3, 2, 1, 0, 7, 6, 5, 4,
				                                      11, 10, 9, 8, 15, 14, 13, 12);
				__m128i m0 = _mm_loadu_si128((const __m128i *)(msg + 0));
				__m128i m1 = _mm_loadu_si128((const __m128i *)(msg + 16));
				__m128i m2 = _mm_loadu_si128((const __m128i *)(msg + 32));
				__m128i m3 = _mm_loadu_si128((const __m128i *)(msg + 48));
				_mm_storeu_si128((__m128i *)&W[0], _mm_shuffle_epi8(m0, shuffle));
				_mm_storeu_si128((__m128i *)&W[4], _mm_shuffle_epi8(m1, shuffle));
				_mm_storeu_si128((__m128i *)&W[8], _mm_shuffle_epi8(m2, shuffle));
				_mm_storeu_si128((__m128i *)&W[12], _mm_shuffle_epi8(m3, shuffle));
			}
			#else
			for (i = 0; i < 16; i++) { W[i] = load_u32_be(msg + i * 4); }
			#endif
		}
		else
		{
			for (i = 0; i < 16; i++) { W[i] = load_u32_be(msg + i * 4); }
		}

		for (i = 16; i < 68; i++) {
			W[i] = P1(W[i - 16] ^ W[i - 9] ^ L_SHIFT(W[i - 3], 15)) ^
			       L_SHIFT(W[i - 13], 7) ^ W[i - 6];
		}

		A = dgst[0]; B = dgst[1]; C = dgst[2]; D = dgst[3];
		E = dgst[4]; F = dgst[5]; G = dgst[6]; H = dgst[7];

		SM3_R_FF1(0);  SM3_R_FF1(1);  SM3_R_FF1(2);  SM3_R_FF1(3);
		SM3_R_FF1(4);  SM3_R_FF1(5);  SM3_R_FF1(6);  SM3_R_FF1(7);
		SM3_R_FF1(8);  SM3_R_FF1(9);  SM3_R_FF1(10); SM3_R_FF1(11);
		SM3_R_FF1(12); SM3_R_FF1(13); SM3_R_FF1(14); SM3_R_FF1(15);
		SM3_R_FF2(16); SM3_R_FF2(17); SM3_R_FF2(18); SM3_R_FF2(19);
		SM3_R_FF2(20); SM3_R_FF2(21); SM3_R_FF2(22); SM3_R_FF2(23);
		SM3_R_FF2(24); SM3_R_FF2(25); SM3_R_FF2(26); SM3_R_FF2(27);
		SM3_R_FF2(28); SM3_R_FF2(29); SM3_R_FF2(30); SM3_R_FF2(31);
		SM3_R_FF2(32); SM3_R_FF2(33); SM3_R_FF2(34); SM3_R_FF2(35);
		SM3_R_FF2(36); SM3_R_FF2(37); SM3_R_FF2(38); SM3_R_FF2(39);
		SM3_R_FF2(40); SM3_R_FF2(41); SM3_R_FF2(42); SM3_R_FF2(43);
		SM3_R_FF2(44); SM3_R_FF2(45); SM3_R_FF2(46); SM3_R_FF2(47);
		SM3_R_FF2(48); SM3_R_FF2(49); SM3_R_FF2(50); SM3_R_FF2(51);
		SM3_R_FF2(52); SM3_R_FF2(53); SM3_R_FF2(54); SM3_R_FF2(55);
		SM3_R_FF2(56); SM3_R_FF2(57); SM3_R_FF2(58); SM3_R_FF2(59);
		SM3_R_FF2(60); SM3_R_FF2(61); SM3_R_FF2(62); SM3_R_FF2(63);

		dgst[0] ^= A; dgst[1] ^= B; dgst[2] ^= C; dgst[3] ^= D;
		dgst[4] ^= E; dgst[5] ^= F; dgst[6] ^= G; dgst[7] ^= H;
		msg += 64;
	}
}

#undef SM3_R_FF1
#undef SM3_R_FF2

static void sm3_bit_compress_scalar(unsigned int dgst[8], const unsigned char *msg, unsigned long long blocks)
{
	sm3_bit_compress_core(dgst, msg, blocks, 0);
}

#if SM3_HAS_X86_DISPATCH
__attribute__((target("avx2,bmi2,ssse3")))
static void sm3_bit_compress_avx2(unsigned int dgst[8], const unsigned char *msg, unsigned long long blocks)
{
	sm3_bit_compress_core(dgst, msg, blocks, 1);
}
#endif

typedef void (*sm3_compress_fn)(unsigned int dgst[8], const unsigned char *msg, unsigned long long blocks);

static sm3_compress_fn sm3_select_compress(void)
{
#if SM3_HAS_X86_DISPATCH
	__builtin_cpu_init();
	if (__builtin_cpu_supports("avx2") && __builtin_cpu_supports("bmi2")) {
		return sm3_bit_compress_avx2;
	}
#endif
	return sm3_bit_compress_scalar;
}

static sm3_compress_fn sm3_get_compress_impl(void)
{
	static sm3_compress_fn compress_impl = NULL;
	if (compress_impl == NULL) {
		compress_impl = sm3_select_compress();
	}
	return compress_impl;
}

static void sm3_hash_bytes_plus_u32_be(const unsigned char *msg, unsigned long long msg_len_bytes,
                                       unsigned int suffix_be, unsigned char *dgst)
{
	sm3_compress_fn compress_impl = sm3_get_compress_impl();
	unsigned long long block_num = msg_len_bytes / 64ULL;
	unsigned long long remain = msg_len_bytes % 64ULL;
	unsigned int digest[8];
	unsigned char tail[128];
	unsigned long long tail_len = remain + 4ULL;
	unsigned long long total_bits = (msg_len_bytes + 4ULL) * 8ULL;
	unsigned long long rem_mod;
	unsigned long long pad_zeros;

	sm3_bit_init(digest);
	if (block_num != 0ULL) {
		compress_impl(digest, msg, block_num);
	}

	if (remain != 0ULL) {
		memcpy(tail, msg + block_num * 64ULL, (size_t)remain);
	}
	tail[remain + 0ULL] = (unsigned char)(suffix_be >> 24);
	tail[remain + 1ULL] = (unsigned char)(suffix_be >> 16);
	tail[remain + 2ULL] = (unsigned char)(suffix_be >> 8);
	tail[remain + 3ULL] = (unsigned char)(suffix_be);
	tail[tail_len++] = 0x80;

	rem_mod = tail_len & 63ULL;
	if (rem_mod <= 56ULL) {
		pad_zeros = 56ULL - rem_mod;
	} else {
		pad_zeros = 64ULL + 56ULL - rem_mod;
	}
	memset(tail + tail_len, 0, (size_t)pad_zeros);
	tail_len += pad_zeros;

	PUT32(tail + tail_len + 0ULL, (unsigned int)(total_bits >> 32));
	PUT32(tail + tail_len + 4ULL, (unsigned int)(total_bits & 0xFFFFFFFFU));
	tail_len += 8ULL;

	compress_impl(digest, tail, tail_len / 64ULL);

	for (int i = 0; i < 8; i++) {
		PUT32(dgst + i * 4, digest[i]);
	}
}

static void sm3_bit(const unsigned char *msg, unsigned long long msg_bitlen, unsigned char *dgst)
{
	unsigned long long block_num;
	unsigned long long remain;
	sm3_compress_fn compress_impl = sm3_get_compress_impl();
	block_num = msg_bitlen / 512;
	remain = msg_bitlen & 0x1FF;
	/*********************Initializing value********************/
	unsigned int digest[8];
	sm3_bit_init(digest);
	/******************Round function**************************/
	if (block_num != 0)
	{
		compress_impl(digest, msg, block_num);
	}
	unsigned char block[64];
	memset(block, 0, 64);
	memcpy(block, msg + block_num * 64, (remain + 7) >> 3);
	block[remain >> 3] &= ((0xFF00 >> (remain & 0x7)) & 0xFF);
	block[remain >> 3] |= (1 << (7 - (remain & 0x7)));
	/*************************Padding**************************/
	if (remain <= 512 - 65)
	{
		memset(block + (remain >> 3) + 1, 0, (512 - remain - 65) >> 3);
	}
	else
	{
		memset(block + (remain >> 3) + 1, 0, (512 - remain - 1) >> 3);
		compress_impl(digest, block, 1);
		memset(block, 0, 64 - 8);
	}
	PUT32(block + 56, block_num >> 32 << 9);
	PUT32(block + 60, (block_num << 9) + (remain));
	/**********************Round function************************/
	compress_impl(digest, block, 1);
	/*********************Output hash value**********************/
	for (int i = 0; i < 8; i++)
	{
		PUT32(dgst + i * 4, digest[i]);
	}
}

// key = SM3(UTF-8("3.14159265358979")) || SM3(UTF-8("2.71828182845904"))
static const unsigned char key[] = {
	0x53, 0x07, 0xf6, 0xd5, 0xeb, 0x6a, 0x3c, 0xed,
	0x3d, 0x24, 0xc5, 0x3c, 0xc9, 0xc8, 0x2c, 0xce,
	0x2f, 0x89, 0x36, 0x39, 0x70, 0x23, 0xf0, 0x69,
	0x5c, 0x26, 0xc8, 0x0c, 0x1a, 0xb1, 0x82, 0xa7,
	0x1d, 0xb0, 0x2b, 0xa9, 0x2f, 0x54, 0x40, 0x18,
	0x11, 0x5a, 0x96, 0xe7, 0x19, 0x66, 0x2c, 0xa3,
	0x2b, 0x7c, 0x7e, 0xfc, 0x0a, 0x6d, 0x24, 0x82,
	0x15, 0x07, 0x66, 0xba, 0x6f, 0x65, 0x5b, 0x8e};

static unsigned long long key_len_bits = (sizeof(key) / sizeof(key[0])) * 8;

static void normalize(unsigned char *input, unsigned long long total_bits)
{
	unsigned long long full_bytes = total_bits / 8;
	unsigned long long remaining_bits = total_bits % 8;
	if (remaining_bits > 0)
	{
		input[full_bytes] = input[full_bytes] & ~((1 << (8 - remaining_bits)) - 1);
	}
}

// GB/T 15852.2-2024 Section 7
static int hmac(const unsigned char *msg, unsigned long long msg_len_bits, const unsigned char *key, unsigned long long key_len_bits, unsigned char *mac)
{
	// key expansion
	unsigned char K[L1 / 8] = {0};
	memcpy(K, key, key_len_bits / 8);
	unsigned char K1[L1 / 8], K2[L1 / 8];
	unsigned char IPAD[L1 / 8], OPAD[L1 / 8];
	memset(IPAD, 0x36, sizeof(IPAD));
	memset(OPAD, 0x5C, sizeof(OPAD));
	for (unsigned long long i = 0; i < L1 / 8; i++)
	{
		K1[i] = K[i] ^ IPAD[i];
		K2[i] = K[i] ^ OPAD[i];
	}
	// hash operation
	unsigned char H1[L2 / 8], H2[L2 / 8];
	unsigned char *temp1;
	temp1 = (unsigned char *)malloc(L1 / 8 + (msg_len_bits + 7) / 8);
	if (temp1 == NULL)
	{
		fprintf(stderr, "ERROR: Memory allocation failed at %s, line %d. \n", __FILE__, __LINE__);
		return MEMORY_ALLOCATION_FAILED;
	}
	memcpy(temp1, K1, L1 / 8);
	memcpy(temp1 + L1 / 8, msg, (msg_len_bits + 7) / 8);
	sm3_bit(temp1, L1 + msg_len_bits, H1);
	// output transformation
	unsigned char temp2[L1 / 8 + L2 / 8];
	memcpy(temp2, K2, L1 / 8);
	memcpy(temp2 + L1 / 8, H1, L2 / 8);
	sm3_bit(temp2, L1 + L2, H2);
	// truncation operation
	memcpy(mac, H2, L2 / 8);
	free(temp1);
	return HASH_SUCCESS;
}

static int pseudohash_512(const unsigned char *msg, unsigned long long msg_len_bits, unsigned char *hash512)
{
	// k1
	unsigned char k1[32];
	unsigned char *cascade_0200_msg;
	cascade_0200_msg = (unsigned char *)malloc((msg_len_bits + 7) / 8 + 2);
	if (cascade_0200_msg == NULL)
	{
		fprintf(stderr, "ERROR: Memory allocation failed at %s, line %d. \n", __FILE__, __LINE__);
		return MEMORY_ALLOCATION_FAILED;
	}
	cascade_0200_msg[0] = 0x02;
	cascade_0200_msg[1] = 0x00;
	memcpy(cascade_0200_msg + 2, msg, (msg_len_bits + 7) / 8);
	if (hmac(cascade_0200_msg, 16 + msg_len_bits, key, key_len_bits, k1) != 0)
	{
		fprintf(stderr, "ERROR: HMAC failed at %s, line %d. \n", __FILE__, __LINE__);
		return HASH_FAILED;
	}
	// h1
	unsigned char h1[32];
	unsigned char *cascade_msg_0200;
	cascade_msg_0200 = (unsigned char *)malloc((msg_len_bits + 7) / 8 + 2);
	if (cascade_msg_0200 == NULL)
	{
		fprintf(stderr, "ERROR: Memory allocation failed at %s, line %d. \n", __FILE__, __LINE__);
		return MEMORY_ALLOCATION_FAILED;
	}
	memcpy(cascade_msg_0200, msg, (msg_len_bits + 7) / 8);
	if (msg_len_bits % 8 == 0)
	{
		cascade_msg_0200[(msg_len_bits + 7) / 8] = 0x02;
		cascade_msg_0200[(msg_len_bits + 7) / 8 + 1] = 0x00;
	}
	else
	{
		normalize(cascade_msg_0200, msg_len_bits);
		cascade_msg_0200[(msg_len_bits + 7) / 8 - 1] = cascade_msg_0200[(msg_len_bits + 7) / 8 - 1] ^ (0x02 >> (msg_len_bits % 8));
		cascade_msg_0200[(msg_len_bits + 7) / 8] = (0x02 << (8 - msg_len_bits % 8)) & 0xff;
		cascade_msg_0200[(msg_len_bits + 7) / 8 + 1] = 0x00;
	}
	sm3_bit(cascade_msg_0200, 16 + msg_len_bits, h1);
	// h2
	unsigned char h2[32];
	unsigned char k1_cascade_h1[64];
	memcpy(k1_cascade_h1, k1, 32);
	memcpy(k1_cascade_h1 + 32, h1, 32);
	sm3_bit(k1_cascade_h1, (sizeof(k1_cascade_h1) / sizeof(k1_cascade_h1[0])) * 8, h2);
	// final result
	memcpy(hash512, h1, 32);
	memcpy(hash512 + 32, h2, 32);
	// free
	free(cascade_0200_msg);
	free(cascade_msg_0200);
	return HASH_SUCCESS;
}

static int pseudohash_768(const unsigned char *msg, unsigned long long msg_len_bits, unsigned char *hash768)
{
	// k1
	unsigned char k1[32];
	unsigned char *cascade_0300_msg;
	cascade_0300_msg = (unsigned char *)malloc((msg_len_bits + 7) / 8 + 2);
	if (cascade_0300_msg == NULL)
	{
		fprintf(stderr, "ERROR: Memory allocation failed at %s, line %d. \n", __FILE__, __LINE__);
		return MEMORY_ALLOCATION_FAILED;
	}
	cascade_0300_msg[0] = 0x03;
	cascade_0300_msg[1] = 0x00;
	memcpy(cascade_0300_msg + 2, msg, (msg_len_bits + 7) / 8);
	if (hmac(cascade_0300_msg, 16 + msg_len_bits, key, key_len_bits, k1) != 0)
	{
		fprintf(stderr, "ERROR: HMAC failed at %s, line %d. \n", __FILE__, __LINE__);
		return HASH_FAILED;
	}
	// h1
	unsigned char h1[32];
	unsigned char *cascade_msg_0300;
	cascade_msg_0300 = (unsigned char *)malloc((msg_len_bits + 7) / 8 + 2);
	if (cascade_msg_0300 == NULL)
	{
		fprintf(stderr, "ERROR: Memory allocation failed at %s, line %d. \n", __FILE__, __LINE__);
		return MEMORY_ALLOCATION_FAILED;
	}
	memcpy(cascade_msg_0300, msg, (msg_len_bits + 7) / 8);

	if (msg_len_bits % 8 == 0)
	{
		cascade_msg_0300[(msg_len_bits + 7) / 8] = 0x03;
		cascade_msg_0300[(msg_len_bits + 7) / 8 + 1] = 0x00;
	}
	else
	{
		normalize(cascade_msg_0300, msg_len_bits);
		cascade_msg_0300[(msg_len_bits + 7) / 8 - 1] = cascade_msg_0300[(msg_len_bits + 7) / 8 - 1] ^ (0x03 >> (msg_len_bits % 8));
		cascade_msg_0300[(msg_len_bits + 7) / 8] = (0x03 << (8 - msg_len_bits % 8)) & 0xff;
		cascade_msg_0300[(msg_len_bits + 7) / 8 + 1] = 0x00;
	}
	sm3_bit(cascade_msg_0300, 16 + msg_len_bits, h1);
	// k2
	unsigned char k2[32];
	if (hmac(h1, (sizeof(h1) / sizeof(h1[0])) * 8, key, key_len_bits, k2) != 0)
	{
		fprintf(stderr, "ERROR: HMAC failed at %s, line %d. \n", __FILE__, __LINE__);
		return HASH_FAILED;
	}
	// h2
	unsigned char h2[32];
	unsigned char k1_cascade_h1[64];
	memcpy(k1_cascade_h1, k1, 32);
	memcpy(k1_cascade_h1 + 32, h1, 32);
	sm3_bit(k1_cascade_h1, (sizeof(k1_cascade_h1) / sizeof(k1_cascade_h1[0])) * 8, h2);
	// h3
	unsigned char h3[32];
	unsigned char h2_cascade_k2[64];
	memcpy(h2_cascade_k2, h2, 32);
	memcpy(h2_cascade_k2 + 32, k2, 32);
	sm3_bit(h2_cascade_k2, (sizeof(h2_cascade_k2) / sizeof(h2_cascade_k2[0])) * 8, h3);
	// final result
	memcpy(hash768, h1, 32);
	memcpy(hash768 + 32, h2, 32);
	memcpy(hash768 + 64, h3, 32);
	// free
	free(cascade_0300_msg);
	free(cascade_msg_0300);
	return HASH_SUCCESS;
}

static int pseudohash_1024(const unsigned char *msg, unsigned long long msg_len_bits, unsigned char *hash1024)
{
	// k1
	unsigned char k1[32];
	unsigned char *cascade_0400_msg;
	cascade_0400_msg = (unsigned char *)malloc((msg_len_bits + 7) / 8 + 2);
	if (cascade_0400_msg == NULL)
	{
		fprintf(stderr, "ERROR: Memory allocation failed at %s, line %d. \n", __FILE__, __LINE__);
		return MEMORY_ALLOCATION_FAILED;
	}
	cascade_0400_msg[0] = 0x04;
	cascade_0400_msg[1] = 0x00;
	memcpy(cascade_0400_msg + 2, msg, (msg_len_bits + 7) / 8);
	if (hmac(cascade_0400_msg, 16 + msg_len_bits, key, key_len_bits, k1) != 0)
	{
		fprintf(stderr, "ERROR: HMAC failed at %s, line %d. \n", __FILE__, __LINE__);
		return HASH_FAILED;
	}
	// h1
	unsigned char h1[32];
	unsigned char *cascade_msg_0400;
	cascade_msg_0400 = (unsigned char *)malloc((msg_len_bits + 7) / 8 + 2);
	if (cascade_msg_0400 == NULL)
	{
		fprintf(stderr, "ERROR: Memory allocation failed at %s, line %d. \n", __FILE__, __LINE__);
		return MEMORY_ALLOCATION_FAILED;
	}
	memcpy(cascade_msg_0400, msg, (msg_len_bits + 7) / 8);
	normalize(cascade_msg_0400, msg_len_bits);
	if (msg_len_bits % 8 == 0)
	{
		cascade_msg_0400[(msg_len_bits + 7) / 8] = 0x04;
		cascade_msg_0400[(msg_len_bits + 7) / 8 + 1] = 0x00;
	}
	else
	{
		cascade_msg_0400[(msg_len_bits + 7) / 8 - 1] = cascade_msg_0400[(msg_len_bits + 7) / 8 - 1] ^ (0x04 >> (msg_len_bits % 8));
		cascade_msg_0400[(msg_len_bits + 7) / 8] = (0x04 << (8 - msg_len_bits % 8)) & 0xff;
		cascade_msg_0400[(msg_len_bits + 7) / 8 + 1] = 0x00;
	}
	sm3_bit(cascade_msg_0400, 16 + msg_len_bits, h1);
	// k2
	unsigned char k2[32];
	if (hmac(h1, (sizeof(h1) / sizeof(h1[0])) * 8, key, key_len_bits, k2) != 0)
	{
		fprintf(stderr, "ERROR: HMAC failed at %s, line %d. \n", __FILE__, __LINE__);
		return HASH_FAILED;
	}
	// h2
	unsigned char h2[32];
	unsigned char k1_cascade_h1[64];
	memcpy(k1_cascade_h1, k1, 32);
	memcpy(k1_cascade_h1 + 32, h1, 32);
	sm3_bit(k1_cascade_h1, (sizeof(k1_cascade_h1) / sizeof(k1_cascade_h1[0])) * 8, h2);
	// k3
	unsigned char k3[32];
	if (hmac(h2, (sizeof(h2) / sizeof(h2[0])) * 8, key, key_len_bits, k3) != 0)
	{
		fprintf(stderr, "ERROR: HMAC failed at %s, line %d. \n", __FILE__, __LINE__);
		return HASH_FAILED;
	}
	// h3
	unsigned char h3[32];
	unsigned char h2_cascade_k2[64];
	memcpy(h2_cascade_k2, h2, 32);
	memcpy(h2_cascade_k2 + 32, k2, 32);
	sm3_bit(h2_cascade_k2, (sizeof(h2_cascade_k2) / sizeof(h2_cascade_k2[0])) * 8, h3);
	// k4
	unsigned char k4[32];
	if (hmac(h3, (sizeof(h3) / sizeof(h3[0])) * 8, key, key_len_bits, k4) != 0)
	{
		fprintf(stderr, "ERROR: HMAC failed at %s, line %d. \n", __FILE__, __LINE__);
		return HASH_FAILED;
	}
	// h4
	unsigned char h4[32];
	unsigned char k3_cascade_h3_k4[96];
	memcpy(k3_cascade_h3_k4, k3, 32);
	memcpy(k3_cascade_h3_k4 + 32, h3, 32);
	memcpy(k3_cascade_h3_k4 + 64, k4, 32);
	sm3_bit(k3_cascade_h3_k4, (sizeof(k3_cascade_h3_k4) / sizeof(k3_cascade_h3_k4[0])) * 8, h4);
	// final result
	memcpy(hash1024, h1, 32);
	memcpy(hash1024 + 32, h2, 32);
	memcpy(hash1024 + 64, h3, 32);
	memcpy(hash1024 + 96, h4, 32);
	// free
	free(cascade_0400_msg);
	free(cascade_msg_0400);
	return HASH_SUCCESS;
}

int sm3hash(int digest_len_bits, const unsigned char *msg, unsigned long long msg_len_bits, unsigned char *digest)
{
	if (digest_len_bits == 256)
	{
		sm3_bit(msg, msg_len_bits, digest);
		return HASH_SUCCESS;
	}
	else
	{
		fprintf(stderr, "ERROR: Digestbitlen not in the limitation. \n");
		return INVALID_DIGESTBITLEN;
	}
}

int pseudohash(int digest_len_bits, const unsigned char *msg, unsigned long long msg_len_bits, unsigned char *digest)
{
	if (digest_len_bits == 512)
	{
		return pseudohash_512(msg, msg_len_bits, digest);
	}
	else if (digest_len_bits == 768)
	{
		return pseudohash_768(msg, msg_len_bits, digest);
	}
	else if (digest_len_bits == 1024)
	{
		return pseudohash_1024(msg, msg_len_bits, digest);
	}
	else
	{
		fprintf(stderr, "ERROR: Digestbitlen not in the limitation. \n");
		return INVALID_DIGESTBITLEN;
	}
}

// GB/T 32918.4-2016 Section 5.4.3
int pseudoXOF(unsigned long long output_len_bits, const unsigned char *msg, unsigned long long msg_len_bits, unsigned char *output)
{
	unsigned int ct = 1;
	const unsigned long long blocks = (output_len_bits + 255) / 256;
	const unsigned long long msg_len_bytes = (msg_len_bits + 7) / 8;
	const unsigned long long out_len_bytes = (output_len_bits + 7) / 8;
	unsigned long long produced = 0;
	unsigned char block[32];
	unsigned char stack_buf[512];
	unsigned char *cascade_msg_ct = stack_buf;

	if (blocks == 0) {
		return XOF_SUCCESS;
	}

	if ((msg_len_bits & 7ULL) == 0ULL) {
		/*
		 * Fast path for byte-aligned input (the dominant SPHINCS+ call pattern).
		 * Hash msg || ct directly without copying msg into a temporary buffer.
		 */
		for (unsigned long long i = 0; i < blocks; i++) {
			sm3_hash_bytes_plus_u32_be(msg, msg_len_bytes, ct, block);

			{
				const unsigned long long take = (out_len_bytes - produced > sizeof(block)) ?
					(unsigned long long)sizeof(block) : (out_len_bytes - produced);
				memcpy(output + produced, block, (size_t)take);
				produced += take;
			}
			ct++;
		}
	} else {
		if (msg_len_bytes + 4 > (unsigned long long)sizeof(stack_buf)) {
			cascade_msg_ct = (unsigned char *)malloc((size_t)(msg_len_bytes + 4));
			if (cascade_msg_ct == NULL) {
				fprintf(stderr, "ERROR: Memory allocation failed at %s, line %d. \n", __FILE__, __LINE__);
				return MEMORY_ALLOCATION_FAILED;
			}
		}
		for (unsigned long long i = 0; i < blocks; i++) {
			memcpy(cascade_msg_ct, msg, (size_t)msg_len_bytes);
			normalize(cascade_msg_ct, msg_len_bits);
			cascade_msg_ct[msg_len_bytes - 1] ^= (unsigned char)(ct >> (32U - (8U - (msg_len_bits % 8U))));
			cascade_msg_ct[msg_len_bytes + 0] = (unsigned char)(((ct << (8U - (msg_len_bits % 8U))) & 0xffffffffU) >> 24);
			cascade_msg_ct[msg_len_bytes + 1] = (unsigned char)(((ct << (16U - (msg_len_bits % 8U))) & 0xffffffffU) >> 24);
			cascade_msg_ct[msg_len_bytes + 2] = (unsigned char)(((ct << (24U - (msg_len_bits % 8U))) & 0xffffffffU) >> 24);
			cascade_msg_ct[msg_len_bytes + 3] = (unsigned char)(((ct << (32U - (msg_len_bits % 8U))) & 0xffffffffU) >> 24);
			sm3_bit(cascade_msg_ct, msg_len_bits + 32ULL, block);

			{
				const unsigned long long take = (out_len_bytes - produced > sizeof(block)) ?
					(unsigned long long)sizeof(block) : (out_len_bytes - produced);
				memcpy(output + produced, block, (size_t)take);
				produced += take;
			}
			ct++;
		}
		if (cascade_msg_ct != stack_buf) {
			free(cascade_msg_ct);
		}
	}
	if (output_len_bits % 8 != 0ULL) {
		normalize(output, output_len_bits);
	}
	return XOF_SUCCESS;
}

/* SSE2 CPUID check — shared by wotsx1.c and wots.c */
#if defined(__x86_64__) || defined(__i386__) || defined(_M_X64) || defined(_M_IX86)
int have_sse2(void)
{
	__builtin_cpu_init();
	return __builtin_cpu_supports("sse2");
}
#else
int have_sse2(void) { return 0; }
#endif

/* =========================================================================
 * 4-way SSE2 WOTS chain step for n=64
 * ========================================================================= */

#if SM3_HAS_X86_DISPATCH

#include <emmintrin.h>

static inline __m128i mm_rotl32(__m128i x, int n)
{
	return _mm_or_si128(_mm_slli_epi32(x, n), _mm_srli_epi32(x, 32 - n));
}

static inline __m128i mm_p0(__m128i x)
{
	__m128i t = _mm_xor_si128(mm_rotl32(x, 9), mm_rotl32(x, 17));
	return _mm_xor_si128(x, t);
}

static inline __m128i mm_p1(__m128i x)
{
	__m128i t = _mm_xor_si128(mm_rotl32(x, 15), mm_rotl32(x, 23));
	return _mm_xor_si128(x, t);
}

static void sm3_4x_rounds(__m128i dgst[8], const __m128i W[68])
{
	__m128i A = dgst[0], B = dgst[1], C = dgst[2], D = dgst[3];
	__m128i E = dgst[4], F = dgst[5], G = dgst[6], H = dgst[7];
	__m128i SS1, SS2, TT1, TT2, Wj, tj_r;
	int r;

	for (r = 0; r < 16; r++) {
		tj_r = _mm_set1_epi32((int)sm3_tj_rot[r]);
		Wj = _mm_xor_si128(W[r], W[r + 4]);
		SS1 = mm_rotl32(_mm_add_epi32(_mm_add_epi32(mm_rotl32(A, 12), E), tj_r), 7);
		SS2 = _mm_xor_si128(SS1, mm_rotl32(A, 12));
		TT1 = _mm_add_epi32(_mm_add_epi32(_mm_add_epi32(
			_mm_xor_si128(_mm_xor_si128(A, B), C), D), SS2), Wj);
		TT2 = _mm_add_epi32(_mm_add_epi32(_mm_add_epi32(
			_mm_xor_si128(_mm_xor_si128(E, F), G), H), SS1), W[r]);
		D = C; C = mm_rotl32(B, 9); B = A; A = TT1;
		H = G; G = mm_rotl32(F, 19); F = E; E = mm_p0(TT2);
	}

	for (r = 16; r < 64; r++) {
		tj_r = _mm_set1_epi32((int)sm3_tj_rot[r]);
		Wj = _mm_xor_si128(W[r], W[r + 4]);
		SS1 = mm_rotl32(_mm_add_epi32(_mm_add_epi32(mm_rotl32(A, 12), E), tj_r), 7);
		SS2 = _mm_xor_si128(SS1, mm_rotl32(A, 12));
		TT1 = _mm_add_epi32(_mm_add_epi32(_mm_add_epi32(
			_mm_or_si128(_mm_or_si128(_mm_and_si128(A, B), _mm_and_si128(A, C)),
				_mm_and_si128(B, C)), D), SS2), Wj);
		TT2 = _mm_add_epi32(_mm_add_epi32(_mm_add_epi32(
			_mm_xor_si128(_mm_and_si128(_mm_xor_si128(F, G), E), G), H), SS1), W[r]);
		D = C; C = mm_rotl32(B, 9); B = A; A = TT1;
		H = G; G = mm_rotl32(F, 19); F = E; E = mm_p0(TT2);
	}

	dgst[0] = _mm_xor_si128(dgst[0], A); dgst[1] = _mm_xor_si128(dgst[1], B);
	dgst[2] = _mm_xor_si128(dgst[2], C); dgst[3] = _mm_xor_si128(dgst[3], D);
	dgst[4] = _mm_xor_si128(dgst[4], E); dgst[5] = _mm_xor_si128(dgst[5], F);
	dgst[6] = _mm_xor_si128(dgst[6], G); dgst[7] = _mm_xor_si128(dgst[7], H);
}

static void sm3_4x_expand(__m128i W[68])
{
	int j;
	for (j = 16; j < 68; j++) {
		W[j] = _mm_xor_si128(
			_mm_xor_si128(
				mm_p1(_mm_xor_si128(_mm_xor_si128(W[j - 16], W[j - 9]),
					mm_rotl32(W[j - 3], 15))),
				mm_rotl32(W[j - 13], 7)),
			W[j - 6]);
	}
}

/*
 * thash_wots_chain_4x for n=64 — process 4 WOTS chains in parallel.
 *
 * Message layout for n=64 (thash with inblocks=1):
 *   tag(14) || pub_seed(64) || addr(32) || in(64) = 174 bytes
 * pseudoXOF(512, ...) calls SM3 twice with ct=1 and ct=2:
 *
 *   Block 0 (shared):  tag[0..13] || pub_seed[0..49]
 *   Block 1 (per-lane): pub_seed[50..63] || addr[0..31] || in[0..17]
 *   Block 2 (per-lane): in[18..63] || ct || padding
 *
 * Blocks 0 and 1 are identical for ct=1 and ct=2 — only Block 2 differs.
 * We save state after Block 1 and replay Block 2 with ct=2.
 */
void thash_wots_chain_4x(unsigned char *out, const unsigned char *in,
                         const unsigned char *pub_seed,
                         const uint32_t addrs[4][8])
{
	static const unsigned char tag[] = "Kylin-THASH-v1";
	__m128i dgst[8], dgst_saved[8], W[68];
	unsigned char block0[64];
	unsigned char block1[4][64];
	unsigned char block2_ct1[4][64];
	unsigned char block2_ct2[4][64];
	const unsigned long long total_bits = (174ULL + 4ULL) * 8ULL;  /* 1424 */
	int j, lane;

	/* Build shared Block 0: tag(14) || pub_seed[0..49](50) */
	memcpy(block0, tag, 14);
	memcpy(block0 + 14, pub_seed, 50);

	/* Build per-lane Block 1: pub_seed[50..63](14) || addr[0..31](32) || in[0..17](18) */
	for (lane = 0; lane < 4; lane++) {
		unsigned char *b = block1[lane];
		memcpy(b, pub_seed + 50, 14);
		memcpy(b + 14, addrs[lane], 32);
		memcpy(b + 46, in + lane * 64, 18);
	}

	/* Build per-lane Block 2 for ct=1 and ct=2 */
	for (lane = 0; lane < 4; lane++) {
		unsigned char *b1 = block2_ct1[lane];
		unsigned char *b2 = block2_ct2[lane];
		/* in[18..63] = 46 bytes */
		memcpy(b1, in + lane * 64 + 18, 46);
		memcpy(b2, in + lane * 64 + 18, 46);
		/* ct */
		b1[46] = 0x00; b1[47] = 0x00; b1[48] = 0x00; b1[49] = 0x01;
		b2[46] = 0x00; b2[47] = 0x00; b2[48] = 0x00; b2[49] = 0x02;
		/* SM3 padding */
		b1[50] = 0x80; b2[50] = 0x80;
		memset(b1 + 51, 0, 64 - 51 - 8);
		memset(b2 + 51, 0, 64 - 51 - 8);
		PUT32(b1 + 56, (unsigned int)(total_bits >> 32));
		PUT32(b1 + 60, (unsigned int)total_bits);
		PUT32(b2 + 56, (unsigned int)(total_bits >> 32));
		PUT32(b2 + 60, (unsigned int)total_bits);
	}

	/* SM3 IV */
	dgst[0] = _mm_set1_epi32(0x7380166F); dgst[1] = _mm_set1_epi32(0x4914B2B9);
	dgst[2] = _mm_set1_epi32(0x172442D7); dgst[3] = _mm_set1_epi32(0xDA8A0600);
	dgst[4] = _mm_set1_epi32(0xA96F30BC); dgst[5] = _mm_set1_epi32(0x163138AA);
	dgst[6] = _mm_set1_epi32(0xE38DEE4D); dgst[7] = _mm_set1_epi32(0xB0FB0E4E);

	/* ---- Block 0 (shared) ---- */
	for (j = 0; j < 16; j++) {
		unsigned int w = load_u32_be(block0 + j * 4);
		W[j] = _mm_set1_epi32((int)w);
	}
	sm3_4x_expand(W);
	sm3_4x_rounds(dgst, W);

	/* ---- Block 1 (per-lane) ---- */
	for (j = 0; j < 16; j++) {
		W[j] = _mm_setr_epi32(
			(int)load_u32_be(block1[0] + j * 4),
			(int)load_u32_be(block1[1] + j * 4),
			(int)load_u32_be(block1[2] + j * 4),
			(int)load_u32_be(block1[3] + j * 4));
	}
	sm3_4x_expand(W);
	sm3_4x_rounds(dgst, W);

	/* Save state after Block 1 (reused for ct=2) */
	for (j = 0; j < 8; j++) dgst_saved[j] = dgst[j];

	/* ---- Block 2 with ct=1 ---- */
	for (j = 0; j < 16; j++) {
		W[j] = _mm_setr_epi32(
			(int)load_u32_be(block2_ct1[0] + j * 4),
			(int)load_u32_be(block2_ct1[1] + j * 4),
			(int)load_u32_be(block2_ct1[2] + j * 4),
			(int)load_u32_be(block2_ct1[3] + j * 4));
	}
	sm3_4x_expand(W);
	sm3_4x_rounds(dgst, W);

	/* Extract ct=1 output: first 32 bytes per lane */
	{
		unsigned int all[8][4];
		for (j = 0; j < 8; j++)
			_mm_storeu_si128((__m128i *)all[j], dgst[j]);
		for (lane = 0; lane < 4; lane++) {
			for (j = 0; j < 8; j++) {
				PUT32(out + lane * 64 + j * 4, all[j][lane]);
			}
		}
	}

	/* Restore state after Block 1 for ct=2 */
	for (j = 0; j < 8; j++) dgst[j] = dgst_saved[j];

	/* ---- Block 2 with ct=2 ---- */
	for (j = 0; j < 16; j++) {
		W[j] = _mm_setr_epi32(
			(int)load_u32_be(block2_ct2[0] + j * 4),
			(int)load_u32_be(block2_ct2[1] + j * 4),
			(int)load_u32_be(block2_ct2[2] + j * 4),
			(int)load_u32_be(block2_ct2[3] + j * 4));
	}
	sm3_4x_expand(W);
	sm3_4x_rounds(dgst, W);

	/* Extract ct=2 output: next 32 bytes per lane */
	{
		unsigned int all[8][4];
		for (j = 0; j < 8; j++)
			_mm_storeu_si128((__m128i *)all[j], dgst[j]);
		for (lane = 0; lane < 4; lane++) {
			for (j = 0; j < 8; j++) {
				PUT32(out + lane * 64 + 32 + j * 4, all[j][lane]);
			}
		}
	}
}

#endif /* SM3_HAS_X86_DISPATCH */
