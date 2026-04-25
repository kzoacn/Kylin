#ifndef SPX_PARAMS_H
#define SPX_PARAMS_H

#include <stdint.h>

#define SPX_NAMESPACE(s) SPX_##s

#define SPX_N 64
#define SPX_FULL_HEIGHT 70
#define SPX_D 4
#define SPX_FORS_HEIGHT 20
#define SPX_FORS_TREES 27
#define SPX_WOTS_W 64
#define SPX_WOTS_LEN 87

#define SPX_ADDR_BYTES 32

#define SPX_WOTS_BYTES (SPX_WOTS_LEN * SPX_N)
#define SPX_WOTS_PK_BYTES SPX_WOTS_BYTES
#define SPX_WOTS_SUM (SPX_WOTS_LEN * (SPX_WOTS_W - 1) / 2)

#if SPX_D != 4
#error This implementation currently requires explicit per-layer heights for SPX_D == 4
#endif

#define SPX_TREE_HEIGHT_0 17
#define SPX_TREE_HEIGHT_1 17
#define SPX_TREE_HEIGHT_2 18
#define SPX_TREE_HEIGHT_3 18

#define SPX_BOTTOM_TREE_HEIGHT SPX_TREE_HEIGHT_0
#define SPX_TOP_TREE_HEIGHT SPX_TREE_HEIGHT_3

#define SPX_LAYER_HEIGHT_SUM \
    (SPX_TREE_HEIGHT_0 + SPX_TREE_HEIGHT_1 + SPX_TREE_HEIGHT_2 + SPX_TREE_HEIGHT_3)

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

#define SPX_FORS_MSG_BYTES ((SPX_FORS_HEIGHT * SPX_FORS_TREES + 7) / 8)
#define SPX_FORS_BYTES ((SPX_FORS_HEIGHT + 1) * SPX_FORS_TREES * SPX_N)
#define SPX_FORS_PK_BYTES SPX_N
#define SPX_DGST_BYTES (SPX_FORS_MSG_BYTES + SPX_TREE_BYTES + SPX_LEAF_BYTES)

#define SPX_BYTES (SPX_N + SPX_FORS_BYTES + SPX_D * SPX_WOTS_BYTES + \
                   SPX_FULL_HEIGHT * SPX_N)
#define SPX_PK_BYTES (2 * SPX_N)
#define SPX_SK_BYTES (4 * SPX_N)
#define SPX_SEED_BYTES (3 * SPX_N)

static inline uint32_t spx_tree_height(uint32_t layer)
{
    static const uint8_t heights[SPX_D] = {
        SPX_TREE_HEIGHT_0, SPX_TREE_HEIGHT_1, SPX_TREE_HEIGHT_2, SPX_TREE_HEIGHT_3
    };

    return heights[layer];
}

#include "shake_offsets.h"

#endif
