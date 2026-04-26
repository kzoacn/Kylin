#include <stdint.h>
#include <string.h>

#include "utils.h"
#include "hash.h"
#include "thash.h"
#include "wots.h"
#include "wotsx1.h"
#include "address.h"
#include "params.h"
#include "auxfunc.h"

#define CHAIN_GROUP 4

#if defined(__x86_64__) || defined(__i386__) || defined(_M_X64) || defined(_M_IX86)
static int have_sse2(void)
{
	__builtin_cpu_init();
	return __builtin_cpu_supports("sse2");
}
#else
static int have_sse2(void) { return 0; }
#endif

/*
 * Generates a WOTS public key using 4-way SSE2 when available.
 */
void wots_gen_leafx1(unsigned char *dest,
                   const spx_ctx *ctx,
                   uint32_t leaf_idx, void *v_info)
{
	struct leaf_info_x1 *info = v_info;
	uint32_t *leaf_addr = info->leaf_addr;
	uint32_t *pk_addr = info->pk_addr;
	unsigned int i, k;
	unsigned char pk_buffer[SPX_WOTS_BYTES];
	unsigned char *buffer;
	uint32_t wots_k_mask;

	if (leaf_idx == info->wots_sign_leaf) {
		wots_k_mask = 0;
	} else {
		wots_k_mask = (uint32_t)~0;
	}

	set_keypair_addr(leaf_addr, leaf_idx);
	set_keypair_addr(pk_addr, leaf_idx);

	if (have_sse2()) {
		/* ---- 4-way SSE2 path ---- */
		unsigned char group_bufs[CHAIN_GROUP * SPX_N];
		uint32_t group_addrs[CHAIN_GROUP][8];
		uint32_t group_wots_k[CHAIN_GROUP];
		unsigned char *group_sig[CHAIN_GROUP];
		const unsigned int full_groups = SPX_WOTS_LEN / CHAIN_GROUP;
		const unsigned char *pub_seed = ctx->pub_seed;
		unsigned int g, c;

		for (g = 0; g < full_groups; g++) {
			unsigned int base = g * CHAIN_GROUP;

			/* PRF for each chain */
			for (c = 0; c < CHAIN_GROUP; c++) {
				unsigned int chain_idx = base + c;
				unsigned char *buf = group_bufs + c * SPX_N;
				uint32_t *addr = group_addrs[c];
				unsigned char *a = (unsigned char *)addr;

				memcpy(addr, leaf_addr, 32);
				/* Use byte-level offsets matching the address format */
				a[SPX_OFFSET_CHAIN_ADDR] = (unsigned char)chain_idx;
				a[SPX_OFFSET_HASH_ADDR]  = 0;
				a[SPX_OFFSET_TYPE]       = SPX_ADDR_TYPE_WOTSPRF;
				prf_addr(buf, ctx, addr);

				group_wots_k[c] = info->wots_steps[chain_idx] | wots_k_mask;
				group_sig[c] = info->wots_sig + chain_idx * SPX_N;

				if (0 == group_wots_k[c]) {
					memcpy(group_sig[c], buf, SPX_N);
				}
			}

			/* Set WOTS type for all 4 addresses */
			for (c = 0; c < CHAIN_GROUP; c++) {
				((unsigned char *)group_addrs[c])[SPX_OFFSET_TYPE] = SPX_ADDR_TYPE_WOTS;
			}

			/* 72 chain steps using 4-way SSE2 */
			for (k = 0; k < SPX_WOTS_W - 1; k++) {
				for (c = 0; c < CHAIN_GROUP; c++) {
					((unsigned char *)group_addrs[c])[SPX_OFFSET_HASH_ADDR] = (unsigned char)k;
				}
				thash_wots_chain_4x(group_bufs, group_bufs, pub_seed, (const uint32_t (*)[8])group_addrs);

				for (c = 0; c < CHAIN_GROUP; c++) {
					if (k + 1 == group_wots_k[c]) {
						memcpy(group_sig[c], group_bufs + c * SPX_N, SPX_N);
					}
				}
			}

			/* Copy results to pk_buffer */
			for (c = 0; c < CHAIN_GROUP; c++) {
				memcpy(pk_buffer + (base + c) * SPX_N,
				       group_bufs + c * SPX_N, SPX_N);
			}
		}

		/* Remaining chains with scalar path */
		for (i = full_groups * CHAIN_GROUP; i < SPX_WOTS_LEN; i++) {
			uint32_t wots_k = info->wots_steps[i] | wots_k_mask;

			set_chain_addr(leaf_addr, i);
			set_hash_addr(leaf_addr, 0);
			set_type(leaf_addr, SPX_ADDR_TYPE_WOTSPRF);
			prf_addr(pk_buffer + i * SPX_N, ctx, leaf_addr);

			set_type(leaf_addr, SPX_ADDR_TYPE_WOTS);

			if (0 == wots_k) {
				memcpy(info->wots_sig + i * SPX_N,
				       pk_buffer + i * SPX_N, SPX_N);
			}

			for (k = 0; k < SPX_WOTS_W - 1; k++) {
				set_hash_addr(leaf_addr, k);
				thash(pk_buffer + i * SPX_N, pk_buffer + i * SPX_N,
				      1, ctx, leaf_addr);

				if (k + 1 == wots_k) {
					memcpy(info->wots_sig + i * SPX_N,
					       pk_buffer + i * SPX_N, SPX_N);
				}
			}
		}
	} else {
		/* ---- Scalar fallback ---- */
		for (i = 0, buffer = pk_buffer; i < SPX_WOTS_LEN;
		     i++, buffer += SPX_N) {
			uint32_t wots_k = info->wots_steps[i] | wots_k_mask;

			set_chain_addr(leaf_addr, i);
			set_hash_addr(leaf_addr, 0);
			set_type(leaf_addr, SPX_ADDR_TYPE_WOTSPRF);
			prf_addr(buffer, ctx, leaf_addr);

			set_type(leaf_addr, SPX_ADDR_TYPE_WOTS);

			for (k = 0;; k++) {
				if (k == wots_k) {
					memcpy(info->wots_sig + i * SPX_N,
					       buffer, SPX_N);
				}
				if (k == SPX_WOTS_W - 1) break;
				set_hash_addr(leaf_addr, k);
				thash(buffer, buffer, 1, ctx, leaf_addr);
			}
		}
	}

	/* Final thash to generate WOTS public key */
	thash(dest, pk_buffer, SPX_WOTS_LEN, ctx, pk_addr);
}
