#include <stdint.h>
#include <stdlib.h>
#include <string.h>

#include "bpors.h"
#include "utils.h"
#include "hash.h"
#include "thash.h"
#include "address.h"
#include "auxfunc.h"

#define BPORS_MAX_CHILD_AUTH (SPX_BPORS_CH_K * SPX_BPORS_CHILD_HEIGHT)

#if SPX_BPORS_CH_K > SPX_BPORS_T
#error BPORS child subset size must not exceed the child leaf count
#endif

static uint32_t node_depth(uint32_t heap)
{
    uint32_t depth = 0;
    while (heap > 1) {
        heap >>= 1;
        depth++;
    }
    return depth;
}

static uint32_t node_index(uint32_t heap)
{
    uint32_t depth = node_depth(heap);
    return heap - (1u << depth);
}

static uint32_t child_leaf_heap(uint32_t leaf_idx)
{
    const uint32_t h = SPX_BPORS_CHILD_HEIGHT;
    const uint32_t split = SPX_BPORS_T - (1u << (h - 1));

    if (leaf_idx < 2u * split) {
        return (1u << h) + leaf_idx;
    }
    return (1u << (h - 1)) + (leaf_idx - split);
}

static void set_bpors_coord(uint32_t addr[8], uint32_t coord)
{
    ((unsigned char *)addr)[20] = (unsigned char)coord;
}

static void set_bpors_bucket(uint32_t addr[8], uint32_t bucket)
{
    ((unsigned char *)addr)[24] = (unsigned char)(bucket >> 8);
    ((unsigned char *)addr)[25] = (unsigned char)bucket;
}

static void prepare_bpors_addr(uint32_t out[8], const uint32_t in[8],
                               uint32_t type, uint32_t coord,
                               uint32_t bucket)
{
    memset(out, 0, 8 * sizeof(uint32_t));
    copy_keypair_addr(out, in);
    set_type(out, type);
    set_bpors_coord(out, coord);
    set_bpors_bucket(out, bucket);
}

static int xof_u32(uint32_t *out, const unsigned char *m, uint64_t ctr,
                   const spx_ctx *ctx, const uint32_t addr[8],
                   uint32_t domain, uint32_t coord, uint32_t item,
                   uint32_t draw)
{
    static const unsigned char tag[] = "Kylin-BPORS-H2-v1";
    unsigned char buf[sizeof(tag) - 1 + SPX_N + SPX_ADDR_BYTES +
                      SPX_BPORS_MSG_BYTES + 8 + 16];
    unsigned char rnd[4];
    unsigned char *p = buf;

    memcpy(p, tag, sizeof(tag) - 1);
    p += sizeof(tag) - 1;
    memcpy(p, ctx->pub_seed, SPX_N);
    p += SPX_N;
    memcpy(p, addr, SPX_ADDR_BYTES);
    p += SPX_ADDR_BYTES;
    memcpy(p, m, SPX_BPORS_MSG_BYTES);
    p += SPX_BPORS_MSG_BYTES;
    ull_to_bytes(p, 8, ctr);
    p += 8;
    u32_to_bytes(p, domain);
    p += 4;
    u32_to_bytes(p, coord);
    p += 4;
    u32_to_bytes(p, item);
    p += 4;
    u32_to_bytes(p, draw);
    p += 4;

    if (pseudoXOF(32, buf, (unsigned long long)(p - buf) * 8ULL, rnd) != 0) {
        return -1;
    }
    *out = (uint32_t)bytes_to_ull(rnd, 4);
    return 0;
}

static int random_bounded(uint32_t *out, uint32_t bound,
                          const unsigned char *m, uint64_t ctr,
                          const spx_ctx *ctx, const uint32_t addr[8],
                          uint32_t domain, uint32_t coord, uint32_t item)
{
    uint32_t draw = 0;
    const uint64_t range = 1ULL << 32;
    const uint64_t limit = range - (range % bound);

    if (bound == 0) {
        return -1;
    }

    for (;;) {
        uint32_t x;
        if (xof_u32(&x, m, ctr, ctx, addr, domain, coord, item, draw) != 0) {
            return -1;
        }
        if ((uint64_t)x < limit) {
            *out = x % bound;
            return 0;
        }
        draw++;
    }
}

static int contains_u32(const uint32_t *values, uint32_t len, uint32_t x)
{
    uint32_t i;
    for (i = 0; i < len; i++) {
        if (values[i] == x) {
            return 1;
        }
    }
    return 0;
}

static void sort_u32(uint32_t *values, uint32_t len)
{
    uint32_t i;
    for (i = 1; i < len; i++) {
        uint32_t x = values[i];
        uint32_t j = i;
        while (j > 0 && values[j - 1] > x) {
            values[j] = values[j - 1];
            j--;
        }
        values[j] = x;
    }
}

static int select_subset(uint32_t out[SPX_BPORS_CH_K],
                         const unsigned char *m, uint64_t ctr,
                         const spx_ctx *ctx, const uint32_t addr[8],
                         uint32_t coord)
{
    uint32_t len = 0;
    uint32_t item = 0;
    while (len < SPX_BPORS_CH_K) {
        uint32_t x;
        if (random_bounded(&x, SPX_BPORS_T, m, ctr, ctx, addr,
                           2, coord, item) != 0) {
            return -1;
        }
        item++;
        if (!contains_u32(out, len, x)) {
            out[len++] = x;
        }
    }
    sort_u32(out, SPX_BPORS_CH_K);
    return 0;
}

static int pos_less(uint32_t a, uint32_t b)
{
    uint32_t da = node_depth(a);
    uint32_t db = node_depth(b);
    if (da != db) {
        return da > db;
    }
    return node_index(a) < node_index(b);
}

static void sort_positions(uint32_t *values, uint32_t len)
{
    uint32_t i;
    for (i = 1; i < len; i++) {
        uint32_t x = values[i];
        uint32_t j = i;
        while (j > 0 && pos_less(x, values[j - 1])) {
            values[j] = values[j - 1];
            j--;
        }
        values[j] = x;
    }
}

static void add_unique(uint32_t *values, uint32_t *len, uint32_t x)
{
    if (!contains_u32(values, *len, x)) {
        values[(*len)++] = x;
    }
}

static void fill_child_exists(unsigned char *exists)
{
    uint32_t i;
    memset(exists, 0, (size_t)(1u << (SPX_BPORS_CHILD_HEIGHT + 1)));
    for (i = 0; i < SPX_BPORS_T; i++) {
        uint32_t heap = child_leaf_heap(i);
        while (heap != 0) {
            exists[heap] = 1;
            heap >>= 1;
        }
    }
}

static int oct_positions(uint32_t out[BPORS_MAX_CHILD_AUTH],
                         uint32_t *outlen,
                         const uint32_t indices[SPX_BPORS_CH_K])
{
    unsigned char exists[1u << (SPX_BPORS_CHILD_HEIGHT + 1)];
    uint32_t active[SPX_BPORS_CH_K];
    uint32_t active_len = 0;
    uint32_t auth_len = 0;
    uint32_t i;

    fill_child_exists(exists);
    for (i = 0; i < SPX_BPORS_CH_K; i++) {
        add_unique(active, &active_len, child_leaf_heap(indices[i]));
    }

    while (!(active_len == 1 && active[0] == 1)) {
        uint32_t max_depth = 0;
        uint32_t next[SPX_BPORS_CH_K];
        uint32_t next_len = 0;
        for (i = 0; i < active_len; i++) {
            uint32_t d = node_depth(active[i]);
            if (d > max_depth) {
                max_depth = d;
            }
        }
        for (i = 0; i < active_len; i++) {
            uint32_t heap = active[i];
            if (node_depth(heap) == max_depth) {
                uint32_t sibling = heap ^ 1u;
                if (exists[sibling] && !contains_u32(active, active_len, sibling)) {
                    if (auth_len >= BPORS_MAX_CHILD_AUTH) {
                        return -1;
                    }
                    add_unique(out, &auth_len, sibling);
                }
                add_unique(next, &next_len, heap >> 1);
            } else {
                add_unique(next, &next_len, heap);
            }
        }
        memcpy(active, next, next_len * sizeof(uint32_t));
        active_len = next_len;
    }

    sort_positions(out, auth_len);
    *outlen = auth_len;
    return 0;
}

static void gen_child_sk(unsigned char *sk, const spx_ctx *ctx,
                         const uint32_t base_addr[8], uint32_t coord,
                         uint32_t bucket, uint32_t leaf_idx)
{
    uint32_t addr[8];
    prepare_bpors_addr(addr, base_addr, SPX_ADDR_TYPE_BPORSCHILDPRF,
                       coord, bucket);
    set_tree_height(addr, 0);
    set_tree_index(addr, leaf_idx);
    prf_addr(sk, ctx, addr);
}

static void child_sk_to_leaf(unsigned char *leaf, const unsigned char *sk,
                             const spx_ctx *ctx,
                             const uint32_t base_addr[8], uint32_t coord,
                             uint32_t bucket, uint32_t leaf_idx)
{
    uint32_t addr[8];
    prepare_bpors_addr(addr, base_addr, SPX_ADDR_TYPE_BPORSCHILDTREE,
                       coord, bucket);
    set_tree_height(addr, 0);
    set_tree_index(addr, leaf_idx);
    thash(leaf, sk, 1, ctx, addr);
}

static int alloc_tree(unsigned char **nodes, unsigned char **have,
                      uint32_t height)
{
    size_t total = (size_t)1u << (height + 1);
    *nodes = (unsigned char *)calloc(total, SPX_N);
    *have = (unsigned char *)calloc(total, 1);
    if (*nodes == 0 || *have == 0) {
        free(*nodes);
        free(*have);
        *nodes = 0;
        *have = 0;
        return -1;
    }
    return 0;
}

static void hash_child_parent(unsigned char *out, const unsigned char *left,
                              const unsigned char *right, const spx_ctx *ctx,
                              const uint32_t base_addr[8], uint32_t coord,
                              uint32_t bucket, uint32_t height,
                              uint32_t index)
{
    unsigned char buf[2 * SPX_N];
    uint32_t addr[8];
    memcpy(buf, left, SPX_N);
    memcpy(buf + SPX_N, right, SPX_N);
    prepare_bpors_addr(addr, base_addr, SPX_ADDR_TYPE_BPORSCHILDTREE,
                       coord, bucket);
    set_tree_height(addr, height);
    set_tree_index(addr, index);
    thash(out, buf, 2, ctx, addr);
}

static int build_child_tree(unsigned char **nodes_out, unsigned char **have_out,
                            const spx_ctx *ctx, const uint32_t base_addr[8],
                            uint32_t coord, uint32_t bucket)
{
    const uint32_t h = SPX_BPORS_CHILD_HEIGHT;
    unsigned char *nodes = 0;
    unsigned char *have = 0;
    uint32_t i;

    if (alloc_tree(&nodes, &have, h) != 0) {
        return -1;
    }

    for (i = 0; i < SPX_BPORS_T; i++) {
        unsigned char sk[SPX_N];
        uint32_t heap = child_leaf_heap(i);
        gen_child_sk(sk, ctx, base_addr, coord, bucket, i);
        child_sk_to_leaf(nodes + (size_t)heap * SPX_N, sk, ctx,
                         base_addr, coord, bucket, i);
        have[heap] = 1;
    }

    for (i = h; i > 0; i--) {
        uint32_t first = 1u << i;
        uint32_t count = 1u << i;
        uint32_t j;
        for (j = 0; j < count; j += 2) {
            uint32_t left = first + j;
            uint32_t right = left + 1;
            uint32_t parent = left >> 1;
            if (have[left] && have[right] && !have[parent]) {
                hash_child_parent(nodes + (size_t)parent * SPX_N,
                                  nodes + (size_t)left * SPX_N,
                                  nodes + (size_t)right * SPX_N,
                                  ctx, base_addr, coord, bucket,
                                  h - (i - 1), j >> 1);
                have[parent] = 1;
            }
        }
    }

    *nodes_out = nodes;
    *have_out = have;
    return 0;
}

static int child_root(unsigned char *root, const spx_ctx *ctx,
                      const uint32_t base_addr[8], uint32_t coord,
                      uint32_t bucket)
{
    unsigned char *nodes = 0;
    unsigned char *have = 0;
    int ret = build_child_tree(&nodes, &have, ctx, base_addr, coord, bucket);
    if (ret == 0 && have[1]) {
        memcpy(root, nodes + SPX_N, SPX_N);
    } else {
        ret = -1;
    }
    free(nodes);
    free(have);
    return ret;
}

static int child_open(unsigned char *root, unsigned char *auth_out,
                      const spx_ctx *ctx, const uint32_t base_addr[8],
                      uint32_t coord, uint32_t bucket,
                      const uint32_t auth_pos[BPORS_MAX_CHILD_AUTH],
                      uint32_t auth_len)
{
    unsigned char *nodes = 0;
    unsigned char *have = 0;
    uint32_t i;
    int ret = build_child_tree(&nodes, &have, ctx, base_addr, coord, bucket);
    if (ret != 0 || !have[1]) {
        free(nodes);
        free(have);
        return -1;
    }
    memcpy(root, nodes + SPX_N, SPX_N);
    for (i = 0; i < auth_len; i++) {
        if (!have[auth_pos[i]]) {
            free(nodes);
            free(have);
            return -1;
        }
        memcpy(auth_out + (size_t)i * SPX_N,
               nodes + (size_t)auth_pos[i] * SPX_N, SPX_N);
    }
    free(nodes);
    free(have);
    return 0;
}

static int child_root_from_sig(unsigned char *root,
                               const unsigned char *secrets,
                               const unsigned char *auth,
                               const spx_ctx *ctx,
                               const uint32_t base_addr[8],
                               uint32_t coord, uint32_t bucket,
                               const uint32_t indices[SPX_BPORS_CH_K],
                               const uint32_t auth_pos[BPORS_MAX_CHILD_AUTH],
                               uint32_t auth_len)
{
    const uint32_t h = SPX_BPORS_CHILD_HEIGHT;
    unsigned char *nodes = 0;
    unsigned char *have = 0;
    uint32_t i;

    if (alloc_tree(&nodes, &have, h) != 0) {
        return -1;
    }

    for (i = 0; i < SPX_BPORS_CH_K; i++) {
        uint32_t heap = child_leaf_heap(indices[i]);
        if (have[heap]) {
            free(nodes);
            free(have);
            return -1;
        }
        child_sk_to_leaf(nodes + (size_t)heap * SPX_N,
                         secrets + (size_t)i * SPX_N, ctx,
                         base_addr, coord, bucket, indices[i]);
        have[heap] = 1;
    }

    for (i = 0; i < auth_len; i++) {
        uint32_t heap = auth_pos[i];
        if (have[heap]) {
            free(nodes);
            free(have);
            return -1;
        }
        memcpy(nodes + (size_t)heap * SPX_N, auth + (size_t)i * SPX_N, SPX_N);
        have[heap] = 1;
    }

    for (i = h; i > 0; i--) {
        uint32_t first = 1u << i;
        uint32_t count = 1u << i;
        uint32_t j;
        for (j = 0; j < count; j += 2) {
            uint32_t left = first + j;
            uint32_t right = left + 1;
            uint32_t parent = left >> 1;
            if (have[left] && have[right]) {
                unsigned char tmp[SPX_N];
                hash_child_parent(tmp, nodes + (size_t)left * SPX_N,
                                  nodes + (size_t)right * SPX_N,
                                  ctx, base_addr, coord, bucket,
                                  h - (i - 1), j >> 1);
                if (have[parent] && memcmp(tmp, nodes + (size_t)parent * SPX_N,
                                           SPX_N) != 0) {
                    free(nodes);
                    free(have);
                    return -1;
                }
                memcpy(nodes + (size_t)parent * SPX_N, tmp, SPX_N);
                have[parent] = 1;
            }
        }
    }

    if (!have[1]) {
        free(nodes);
        free(have);
        return -1;
    }
    memcpy(root, nodes + SPX_N, SPX_N);
    free(nodes);
    free(have);
    return 0;
}

static void hash_outer_parent(unsigned char *out, const unsigned char *left,
                              const unsigned char *right, const spx_ctx *ctx,
                              const uint32_t base_addr[8], uint32_t coord,
                              uint32_t height, uint32_t index)
{
    unsigned char buf[2 * SPX_N];
    uint32_t addr[8];
    memcpy(buf, left, SPX_N);
    memcpy(buf + SPX_N, right, SPX_N);
    prepare_bpors_addr(addr, base_addr, SPX_ADDR_TYPE_BPORSOUTER, coord, 0);
    set_tree_height(addr, height);
    set_tree_index(addr, index);
    thash(out, buf, 2, ctx, addr);
}

static int outer_open(unsigned char *root, unsigned char *auth_out,
                      const spx_ctx *ctx, const uint32_t base_addr[8],
                      uint32_t coord, uint32_t bucket)
{
    const uint32_t h = SPX_BPORS_B;
    const uint32_t leaves = 1u << SPX_BPORS_B;
    const size_t total = (size_t)1u << (SPX_BPORS_B + 1);
    unsigned char *nodes = (unsigned char *)calloc(total, SPX_N);
    uint32_t i;
    uint32_t heap;

    if (nodes == 0) {
        return -1;
    }

    for (i = 0; i < leaves; i++) {
        if (child_root(nodes + (size_t)((1u << h) + i) * SPX_N,
                       ctx, base_addr, coord, i) != 0) {
            free(nodes);
            return -1;
        }
    }

    for (i = h; i > 0; i--) {
        uint32_t first = 1u << i;
        uint32_t count = 1u << i;
        uint32_t j;
        for (j = 0; j < count; j += 2) {
            uint32_t left = first + j;
            uint32_t parent = left >> 1;
            hash_outer_parent(nodes + (size_t)parent * SPX_N,
                              nodes + (size_t)left * SPX_N,
                              nodes + (size_t)(left + 1) * SPX_N,
                              ctx, base_addr, coord, h - (i - 1), j >> 1);
        }
    }

    memcpy(root, nodes + SPX_N, SPX_N);
    heap = (1u << h) + bucket;
    for (i = 0; i < h; i++) {
        memcpy(auth_out + (size_t)i * SPX_N,
               nodes + (size_t)(heap ^ 1u) * SPX_N, SPX_N);
        heap >>= 1;
    }

    free(nodes);
    return 0;
}

static void outer_root_from_sig(unsigned char *root,
                                const unsigned char *child_pk,
                                const unsigned char *auth,
                                const spx_ctx *ctx,
                                const uint32_t base_addr[8],
                                uint32_t coord, uint32_t bucket)
{
    unsigned char cur[SPX_N];
    uint32_t heap = (1u << SPX_BPORS_B) + bucket;
    uint32_t level;
    memcpy(cur, child_pk, SPX_N);

    for (level = 0; level < SPX_BPORS_B; level++) {
        unsigned char next[SPX_N];
        uint32_t depth = SPX_BPORS_B - level;
        uint32_t idx = heap - (1u << depth);
        if ((idx & 1u) != 0) {
            hash_outer_parent(next, auth + (size_t)level * SPX_N, cur,
                              ctx, base_addr, coord, level + 1, idx >> 1);
        } else {
            hash_outer_parent(next, cur, auth + (size_t)level * SPX_N,
                              ctx, base_addr, coord, level + 1, idx >> 1);
        }
        memcpy(cur, next, SPX_N);
        heap >>= 1;
    }
    memcpy(root, cur, SPX_N);
}

static int parse_candidate(uint32_t buckets[SPX_BPORS_K],
                           uint32_t indices[SPX_BPORS_K][SPX_BPORS_CH_K],
                           uint32_t auth_pos[SPX_BPORS_K][BPORS_MAX_CHILD_AUTH],
                           uint32_t auth_len[SPX_BPORS_K],
                           uint32_t *total_auth,
                           const unsigned char *m, uint64_t ctr,
                           const spx_ctx *ctx, const uint32_t addr[8])
{
    uint32_t c;
    *total_auth = SPX_BPORS_K * SPX_BPORS_B;
    for (c = 0; c < SPX_BPORS_K; c++) {
        if (random_bounded(&buckets[c], 1u << SPX_BPORS_B, m, ctr, ctx,
                           addr, 1, c, 0) != 0) {
            return -1;
        }
        if (select_subset(indices[c], m, ctr, ctx, addr, c) != 0) {
            return -1;
        }
        if (oct_positions(auth_pos[c], &auth_len[c], indices[c]) != 0) {
            return -1;
        }
        *total_auth += auth_len[c];
    }
    return 0;
}

int bpors_sign(unsigned char *sig, unsigned char *pk,
               const unsigned char *m,
               const spx_ctx *ctx,
               const uint32_t bpors_addr[8])
{
    uint32_t buckets[SPX_BPORS_K];
    uint32_t indices[SPX_BPORS_K][SPX_BPORS_CH_K];
    uint32_t auth_pos[SPX_BPORS_K][BPORS_MAX_CHILD_AUTH];
    uint32_t auth_len[SPX_BPORS_K];
    unsigned char outer_roots[SPX_BPORS_K * SPX_N];
    uint32_t pk_addr[8];
    uint64_t ctr;
    uint32_t total_auth = 0;
    uint32_t c;
    unsigned char *secrets = sig + SPX_BPORS_CTR_BYTES;
    unsigned char *auth = secrets + SPX_BPORS_K * SPX_BPORS_CH_K * SPX_N;
    unsigned char *authp = auth;

    for (ctr = 0; ctr != UINT64_MAX; ctr++) {
        if (parse_candidate(buckets, indices, auth_pos, auth_len, &total_auth,
                            m, ctr, ctx, bpors_addr) != 0) {
            return -1;
        }
        if (total_auth <= SPX_BPORS_MMAX) {
            break;
        }
    }
    if (total_auth > SPX_BPORS_MMAX) {
        return -1;
    }

    ull_to_bytes(sig, SPX_BPORS_CTR_BYTES, ctr);

    for (c = 0; c < SPX_BPORS_K; c++) {
        uint32_t i;
        for (i = 0; i < SPX_BPORS_CH_K; i++) {
            gen_child_sk(secrets + ((size_t)c * SPX_BPORS_CH_K + i) * SPX_N,
                         ctx, bpors_addr, c, buckets[c], indices[c][i]);
        }
    }

    for (c = 0; c < SPX_BPORS_K; c++) {
        unsigned char child_pk[SPX_N];
        if (child_open(child_pk, authp, ctx, bpors_addr, c, buckets[c],
                       auth_pos[c], auth_len[c]) != 0) {
            return -1;
        }
        authp += (size_t)auth_len[c] * SPX_N;
        if (outer_open(outer_roots + (size_t)c * SPX_N, authp, ctx,
                       bpors_addr, c, buckets[c]) != 0) {
            return -1;
        }
        authp += (size_t)SPX_BPORS_B * SPX_N;
        (void)child_pk;
    }

    memset(authp, 0, (size_t)(SPX_BPORS_MMAX - total_auth) * SPX_N);

    prepare_bpors_addr(pk_addr, bpors_addr, SPX_ADDR_TYPE_BPORSPK, 0, 0);
    thash(pk, outer_roots, SPX_BPORS_K, ctx, pk_addr);
    return 0;
}

int bpors_pk_from_sig(unsigned char *pk,
                      const unsigned char *sig, const unsigned char *m,
                      const spx_ctx *ctx,
                      const uint32_t bpors_addr[8])
{
    uint32_t buckets[SPX_BPORS_K];
    uint32_t indices[SPX_BPORS_K][SPX_BPORS_CH_K];
    uint32_t auth_pos[SPX_BPORS_K][BPORS_MAX_CHILD_AUTH];
    uint32_t auth_len[SPX_BPORS_K];
    unsigned char outer_roots[SPX_BPORS_K * SPX_N];
    uint32_t pk_addr[8];
    uint64_t ctr = bytes_to_ull(sig, SPX_BPORS_CTR_BYTES);
    uint32_t total_auth = 0;
    uint32_t used_auth = 0;
    uint32_t c;
    const unsigned char *secrets = sig + SPX_BPORS_CTR_BYTES;
    const unsigned char *auth = secrets + SPX_BPORS_K * SPX_BPORS_CH_K * SPX_N;
    const unsigned char *authp = auth;

    if (parse_candidate(buckets, indices, auth_pos, auth_len, &total_auth,
                        m, ctr, ctx, bpors_addr) != 0) {
        return -1;
    }
    if (total_auth > SPX_BPORS_MMAX) {
        return -1;
    }

    for (c = 0; c < SPX_BPORS_K; c++) {
        unsigned char child_pk[SPX_N];
        if (child_root_from_sig(child_pk,
                                secrets + (size_t)c * SPX_BPORS_CH_K * SPX_N,
                                authp, ctx, bpors_addr, c, buckets[c],
                                indices[c], auth_pos[c], auth_len[c]) != 0) {
            return -1;
        }
        authp += (size_t)auth_len[c] * SPX_N;
        used_auth += auth_len[c];
        outer_root_from_sig(outer_roots + (size_t)c * SPX_N, child_pk, authp,
                            ctx, bpors_addr, c, buckets[c]);
        authp += (size_t)SPX_BPORS_B * SPX_N;
        used_auth += SPX_BPORS_B;
    }

    if (used_auth != total_auth) {
        return -1;
    }
    while (used_auth < SPX_BPORS_MMAX) {
        unsigned int i;
        for (i = 0; i < SPX_N; i++) {
            if (authp[i] != 0) {
                return -1;
            }
        }
        authp += SPX_N;
        used_auth++;
    }

    prepare_bpors_addr(pk_addr, bpors_addr, SPX_ADDR_TYPE_BPORSPK, 0, 0);
    thash(pk, outer_roots, SPX_BPORS_K, ctx, pk_addr);
    return 0;
}
