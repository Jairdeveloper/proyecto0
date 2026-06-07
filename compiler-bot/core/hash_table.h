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

HashTable *ht_create(int capacity);
void       ht_free(HashTable *ht);
void       ht_insert(HashTable *ht, const char *key, void *value);
void      *ht_lookup(HashTable *ht, const char *key);
int        ht_contains(HashTable *ht, const char *key);
void       ht_delete(HashTable *ht, const char *key);
void      **ht_values(HashTable *ht, int *out_count);

#endif
