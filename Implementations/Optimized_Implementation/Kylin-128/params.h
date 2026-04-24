#ifndef SPX_PARAMS_H
#define SPX_PARAMS_H

#define SPX_NAMESPACE(s) SPX_##s

#define SPX_N 16
#define SPX_FULL_HEIGHT 70
#define SPX_D 10
#define SPX_FORS_HEIGHT 14
#define SPX_FORS_TREES 31
#define SPX_WOTS_W 64
#define SPX_WOTS_LEN 23

#define SPX_ADDR_BYTES 32

#define SPX_WOTS_BYTES (SPX_WOTS_LEN * SPX_N)
#define SPX_WOTS_PK_BYTES SPX_WOTS_BYTES
#define SPX_WOTS_SUM (SPX_WOTS_LEN * (SPX_WOTS_W - 1) / 2)

#define SPX_TREE_HEIGHT (SPX_FULL_HEIGHT / SPX_D)

#if SPX_TREE_HEIGHT * SPX_D != SPX_FULL_HEIGHT
#error SPX_D should always divide SPX_FULL_HEIGHT
#endif

#define SPX_FORS_MSG_BYTES ((SPX_FORS_HEIGHT * SPX_FORS_TREES + 7) / 8)
#define SPX_FORS_BYTES ((SPX_FORS_HEIGHT + 1) * SPX_FORS_TREES * SPX_N)
#define SPX_FORS_PK_BYTES SPX_N

#define SPX_BYTES (SPX_N + SPX_FORS_BYTES + SPX_D * SPX_WOTS_BYTES + \
                   SPX_FULL_HEIGHT * SPX_N)
#define SPX_PK_BYTES (2 * SPX_N)
#define SPX_SK_BYTES (4 * SPX_N)
#define SPX_SEED_BYTES (3 * SPX_N)

#include "shake_offsets.h"

#endif
