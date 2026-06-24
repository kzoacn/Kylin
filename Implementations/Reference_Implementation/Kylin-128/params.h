#ifndef SPX_PARAMS_H
#define SPX_PARAMS_H

#include <stdint.h>

#define SPX_NAMESPACE(s) SPX_##s

#define SPX_N 16
#define SPX_FULL_HEIGHT 65
#define SPX_D 9
#define SPX_BPORS_K 5
#define SPX_BPORS_B 6
#define SPX_BPORS_T 132
#define SPX_BPORS_CHILD_HEIGHT 8
#define SPX_BPORS_CH_K 4
#define SPX_BPORS_MMAX 120
#define SPX_BPORS_CTR_BYTES 8
#define SPX_WOTS_W 73
#define SPX_WOTS_LEN 22

#define SPX_ADDR_BYTES 32

#define SPX_WOTS_BYTES (SPX_WOTS_LEN * SPX_N)
#define SPX_WOTS_PK_BYTES SPX_WOTS_BYTES
#define SPX_WOTS_SUM (SPX_WOTS_LEN * (SPX_WOTS_W - 1) / 2)

#if SPX_D != 9
#error This implementation currently requires explicit per-layer heights for SPX_D == 9
#endif

#define SPX_TREE_HEIGHT_0 7
#define SPX_TREE_HEIGHT_1 7
#define SPX_TREE_HEIGHT_2 7
#define SPX_TREE_HEIGHT_3 7
#define SPX_TREE_HEIGHT_4 7
#define SPX_TREE_HEIGHT_5 7
#define SPX_TREE_HEIGHT_6 7
#define SPX_TREE_HEIGHT_7 8
#define SPX_TREE_HEIGHT_8 8

#define SPX_BOTTOM_TREE_HEIGHT SPX_TREE_HEIGHT_0
#define SPX_TOP_TREE_HEIGHT SPX_TREE_HEIGHT_8

#define SPX_LAYER_HEIGHT_SUM \
    (SPX_TREE_HEIGHT_0 + \
     SPX_TREE_HEIGHT_1 + \
     SPX_TREE_HEIGHT_2 + \
     SPX_TREE_HEIGHT_3 + \
     SPX_TREE_HEIGHT_4 + \
     SPX_TREE_HEIGHT_5 + \
     SPX_TREE_HEIGHT_6 + \
     SPX_TREE_HEIGHT_7 + \
     SPX_TREE_HEIGHT_8)

#if SPX_LAYER_HEIGHT_SUM != SPX_FULL_HEIGHT
#error Sum of per-layer heights must equal SPX_FULL_HEIGHT
#endif

#define SPX_MAX_TREE_HEIGHT SPX_TOP_TREE_HEIGHT

#if SPX_MAX_TREE_HEIGHT > 32
#error Each XMSS layer height must be at most 32 bits
#endif

#define SPX_TREE_BITS (SPX_FULL_HEIGHT - SPX_BOTTOM_TREE_HEIGHT)
#define SPX_TREE_BYTES ((SPX_TREE_BITS + 7) / 8)
#define SPX_LEAF_BITS SPX_BOTTOM_TREE_HEIGHT
#define SPX_LEAF_BYTES ((SPX_LEAF_BITS + 7) / 8)

#define SPX_BPORS_MSG_BYTES SPX_N
#define SPX_BPORS_BYTES \
    (SPX_BPORS_CTR_BYTES + \
     (SPX_BPORS_K * SPX_BPORS_CH_K + SPX_BPORS_MMAX) * SPX_N)
#define SPX_BPORS_PK_BYTES SPX_N
#define SPX_DGST_BYTES (SPX_BPORS_MSG_BYTES + SPX_TREE_BYTES + SPX_LEAF_BYTES)

#define SPX_BYTES (SPX_N + SPX_BPORS_BYTES + SPX_D * SPX_WOTS_BYTES + \
                   SPX_FULL_HEIGHT * SPX_N)
#define SPX_PK_BYTES (2 * SPX_N)
#define SPX_SK_BYTES (4 * SPX_N)
#define SPX_SEED_BYTES (3 * SPX_N)

static inline uint32_t spx_tree_height(uint32_t layer)
{
    static const uint8_t heights[SPX_D] = {
        SPX_TREE_HEIGHT_0, SPX_TREE_HEIGHT_1, SPX_TREE_HEIGHT_2, SPX_TREE_HEIGHT_3, SPX_TREE_HEIGHT_4, SPX_TREE_HEIGHT_5, SPX_TREE_HEIGHT_6, SPX_TREE_HEIGHT_7, SPX_TREE_HEIGHT_8
    };

    return heights[layer];
}

#include "shake_offsets.h"

#endif
