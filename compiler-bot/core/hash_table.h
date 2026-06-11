#ifndef HASH_TABLE_H
#define HASH_TABLE_H

#include <stddef.h>

typedef struct {
    char *key;
    void *value;
    int   active;
} HTEntry;

typedef struct {
    HTEntry *entries;
    int      capacity;
    int      count;
} HashTable;

/**
 * Create a hash table with at least `capacity` buckets.
 * The caller owns the table and must call ht_free().
 */
HashTable *ht_create(int capacity);

/** Free all memory used by the hash table. */
void ht_free(HashTable *ht);

/** Insert key->value pair. Replaces existing value if key exists. */
void ht_insert(HashTable *ht, const char *key, void *value);

/** Lookup value by key. Returns NULL if not found. */
void *ht_lookup(HashTable *ht, const char *key);

/** Returns 1 if key exists, 0 otherwise. */
int ht_contains(HashTable *ht, const char *key);

/** Remove key from table. No-op if key doesn't exist. */
void ht_delete(HashTable *ht, const char *key);

/**
 * Collect all values into a malloc'd array.
 * Caller must free() the returned array.
 */
void **ht_values(HashTable *ht, int *out_count);

#endif
