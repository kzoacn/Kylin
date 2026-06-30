#include <stdint.h>
#include <string.h>

#include "params.h"
#include "wots.h"
#include "bpors.h"
#include "hash.h"
#include "thash.h"
#include "address.h"
#include "utils.h"
#include "merkle.h"
#include "kylin_sign.h"

static uint32_t get_low_bits(uint64_t value, uint32_t bits)
{
    if (bits == 0) {
        return 0;
    }
    if (bits >= 32) {
        return (uint32_t)value;
    }
    return (uint32_t)(value & ((1ULL << bits) - 1ULL));
}

static uint64_t shift_right_bits(uint64_t value, uint32_t bits)
{
    if (bits >= 64) {
        return 0;
    }
    return value >> bits;
}

int kylin_seed_keypair(unsigned char *pk, unsigned char *sk,
                       const unsigned char *seed)
{
    spx_ctx ctx;

    memcpy(sk, seed, SPX_SEED_BYTES);
    memcpy(pk, sk + 2 * SPX_N, SPX_N);

    memcpy(ctx.pub_seed, pk, SPX_N);
    memcpy(ctx.sk_seed, sk, SPX_N);

    initialize_hash_function(&ctx);
    if (merkle_gen_root(sk + 3 * SPX_N, &ctx) != 0) {
        return -1;
    }

    memcpy(pk + SPX_N, sk + 3 * SPX_N, SPX_N);
    return 0;
}

int kylin_sign_signature(uint8_t *sig, unsigned long long *siglen,
                         const uint8_t *m, unsigned long long mlen,
                         const uint8_t *sk, const uint8_t *optrand)
{
    spx_ctx ctx;
    const unsigned char *sk_prf = sk + SPX_N;
    const unsigned char *pk = sk + 2 * SPX_N;
    unsigned char mhash[SPX_BPORS_MSG_BYTES];
    unsigned char root[SPX_N];
    uint64_t tree;
    uint32_t idx_leaf;
    uint32_t wots_addr[8] = {0};
    uint32_t tree_addr[8] = {0};
    unsigned int i;
    uint32_t tree_height;

    memcpy(ctx.sk_seed, sk, SPX_N);
    memcpy(ctx.pub_seed, pk, SPX_N);
    initialize_hash_function(&ctx);

    set_type(wots_addr, SPX_ADDR_TYPE_WOTS);
    set_type(tree_addr, SPX_ADDR_TYPE_HASHTREE);

    gen_message_random(sig, sk_prf, optrand, m, mlen, &ctx);
    hash_message(mhash, &tree, &idx_leaf, sig, pk, m, mlen, &ctx);
    sig += SPX_N;

    set_tree_addr(wots_addr, tree);
    set_keypair_addr(wots_addr, idx_leaf);

    if (bpors_sign(sig, root, mhash, &ctx, wots_addr) != 0) {
        return -1;
    }
    sig += SPX_BPORS_BYTES;

    for (i = 0; i < SPX_D; i++) {
        tree_height = spx_tree_height(i);
        set_layer_addr(tree_addr, i);
        set_tree_addr(tree_addr, tree);

        copy_subtree_addr(wots_addr, tree_addr);
        set_keypair_addr(wots_addr, idx_leaf);

        if (merkle_sign(sig, root, &ctx, wots_addr, tree_addr,
                        idx_leaf, tree_height) != 0) {
            return -1;
        }
        sig += SPX_WOTS_BYTES + tree_height * SPX_N;

        if (i + 1 < SPX_D) {
            uint32_t next_tree_height = spx_tree_height(i + 1);
            idx_leaf = get_low_bits(tree, next_tree_height);
            tree = shift_right_bits(tree, next_tree_height);
        }
    }

    *siglen = SPX_BYTES;
    return 0;
}

int kylin_sign_verify(const uint8_t *sig, unsigned long long siglen,
                      const uint8_t *m, unsigned long long mlen,
                      const uint8_t *pk)
{
    spx_ctx ctx;
    const unsigned char *pub_root = pk + SPX_N;
    unsigned char mhash[SPX_BPORS_MSG_BYTES];
    unsigned char wots_pk[SPX_WOTS_BYTES];
    unsigned char root[SPX_N];
    unsigned char leaf[SPX_N];
    uint64_t tree;
    uint32_t idx_leaf;
    uint32_t wots_addr[8] = {0};
    uint32_t tree_addr[8] = {0};
    uint32_t wots_pk_addr[8] = {0};
    unsigned int i;
    uint32_t tree_height;

    if (siglen != SPX_BYTES) {
        return -1;
    }

    memcpy(ctx.pub_seed, pk, SPX_N);
    initialize_hash_function(&ctx);

    set_type(wots_addr, SPX_ADDR_TYPE_WOTS);
    set_type(tree_addr, SPX_ADDR_TYPE_HASHTREE);
    set_type(wots_pk_addr, SPX_ADDR_TYPE_WOTSPK);

    hash_message(mhash, &tree, &idx_leaf, sig, pk, m, mlen, &ctx);
    sig += SPX_N;

    set_tree_addr(wots_addr, tree);
    set_keypair_addr(wots_addr, idx_leaf);

    if (bpors_pk_from_sig(root, sig, mhash, &ctx, wots_addr) != 0) {
        return -1;
    }
    sig += SPX_BPORS_BYTES;

    for (i = 0; i < SPX_D; i++) {
        tree_height = spx_tree_height(i);
        set_layer_addr(tree_addr, i);
        set_tree_addr(tree_addr, tree);

        copy_subtree_addr(wots_addr, tree_addr);
        set_keypair_addr(wots_addr, idx_leaf);

        copy_keypair_addr(wots_pk_addr, wots_addr);

        if (wots_pk_from_sig(wots_pk, sig, root, &ctx, wots_addr) != 0) {
            return -1;
        }
        sig += SPX_WOTS_BYTES;

        thash(leaf, wots_pk, SPX_WOTS_LEN, &ctx, wots_pk_addr);

        compute_root(root, leaf, idx_leaf, 0, sig, tree_height,
                     &ctx, tree_addr);
        sig += tree_height * SPX_N;

        if (i + 1 < SPX_D) {
            uint32_t next_tree_height = spx_tree_height(i + 1);
            idx_leaf = get_low_bits(tree, next_tree_height);
            tree = shift_right_bits(tree, next_tree_height);
        }
    }

    if (memcmp(root, pub_root, SPX_N) != 0) {
        return -1;
    }

    return 0;
}
