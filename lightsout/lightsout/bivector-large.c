#include <stdbool.h>
#include <stdlib.h>
#include <string.h>
#include "lib/bitvector.h"
#include "lib/contracts.h"
#include "lib/xalloc.h"
#include <limits.h>

static size_t chars_needed() {
    return (BITVECTOR_LIMIT + CHAR_BIT - 1) / CHAR_BIT;  
}

bitvector bitvector_new() {
    size_t size = chars_needed();
    char* bits = xcalloc(size, sizeof(char));  
    return (bitvector)bits;
}

bitvector bitvector_copy(bitvector b) {
    REQUIRES(b != NULL);
    
    size_t size = chars_needed();
    char* bits = xmalloc(size * sizeof(char));
    memcpy(bits, (char*)b, size);
    return (bitvector)bits;
}


bool bitvector_get(bitvector b, index_t i) {
    REQUIRES(b != NULL);
    REQUIRES(i < BITVECTOR_LIMIT);
    
    char* bits = (char*)b;
    size_t char_index = i / CHAR_BIT;
    size_t bit_index = i % CHAR_BIT;
    char mask = 1 << bit_index;
    return (bits[char_index] & mask) != 0;
}


bitvector bitvector_flip(bitvector b, index_t i) {
    REQUIRES(b != NULL);
    REQUIRES(i < BITVECTOR_LIMIT);
    bitvector result = bitvector_copy(b);
    char* bits = (char*)result;
    size_t char_index = i / CHAR_BIT;
    size_t bit_index = i % CHAR_BIT;
    
    // Create mask and flip the bit
    char mask = 1 << bit_index;
    bits[char_index] ^= mask;
    
    return result;
}

/* Compare two bitvectors for equality. */
bool bitvector_equal(bitvector b1, bitvector b2) {
    REQUIRES(b1 != NULL);
    REQUIRES(b2 != NULL);
    
    size_t size = chars_needed();
    char* bits1 = (char*)b1;
    char* bits2 = (char*)b2;
    
    // Compare all chars except possibly the last one
    size_t full_chars = BITVECTOR_LIMIT / CHAR_BIT;
    
    // Compare full chars
    for (size_t i = 0; i < full_chars; i++) {
        if (bits1[i] != bits2[i]) {
            return false;
        }
    }
    
    // Handle remaining bits in the last char (if any)
    size_t remaining_bits = BITVECTOR_LIMIT % CHAR_BIT;
    if (remaining_bits > 0) {
        // Create mask for only the bits we care about
        char mask = (1 << remaining_bits) - 1;
        if ((bits1[full_chars] & mask) != (bits2[full_chars] & mask)) {
            return false;
        }
    }
    
    return true;
}

void bitvector_free(bitvector b) {
    if (b != NULL) {
        free((char*)b);
    }
}