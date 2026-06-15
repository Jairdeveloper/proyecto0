#include "hash_table.h"

#include <stdlib.h>
#include <string.h>

#define HT_MIN_CAPACITY 16
#define HT_LOAD_FACTOR  0.75

static unsigned long hash_djb2(const char *str) {
    unsigned long h = 5381;
    int c;
    while ((c = *str++))
        h = ((h << 5) + h) + (unsigned long)c;
    return h;
}

static int ht_probe(HashTable *ht, const char *key) {
    unsigned long h = hash_djb2(key);
    int cap = ht->capacity;
    int idx = (int)(h % (unsigned long)cap);

    for (int i = 0; i < cap; i++) {
        int candidate = (idx + i) % cap;
        if (!ht->entries[candidate].active)
            return candidate;
        if (ht->entries[candidate].key &&
            strcmp(ht->entries[candidate].key, key) == 0)
            return candidate;
    }
    return -1;
}

static int ht_grow(HashTable *ht) {
    int old_cap = ht->capacity;
    HTEntry *old_entries = ht->entries;

    int new_cap = old_cap * 2;
    HTEntry *new_entries = calloc((size_t)new_cap, sizeof(*new_entries));
    if (!new_entries) return -1;

    ht->entries = new_entries;
    ht->capacity = new_cap;
    ht->count = 0;

    for (int i = 0; i < old_cap; i++) {
        if (old_entries[i].active && old_entries[i].key) {
            ht_insert(ht, old_entries[i].key, old_entries[i].value);
            free(old_entries[i].key);
        }
    }
    free(old_entries);
    return 0;
}

HashTable *ht_create(int capacity) {
    HashTable *ht = calloc(1, sizeof(*ht));
    if (!ht) return NULL;
    if (capacity < HT_MIN_CAPACITY)
        capacity = HT_MIN_CAPACITY;
    ht->entries = calloc((size_t)capacity, sizeof(*ht->entries));
    if (!ht->entries) {
        free(ht);
        return NULL;
    }
    ht->capacity = capacity;
    ht->count = 0;
    return ht;
}

void ht_free(HashTable *ht) {
    if (!ht) return;
    for (int i = 0; i < ht->capacity; i++) {
        if (ht->entries[i].active)
            free(ht->entries[i].key);
    }
    free(ht->entries);
    free(ht);
}

void ht_insert(HashTable *ht, const char *key, void *value) {
    if (!ht || !key) return;

    if ((double)ht->count >= (double)ht->capacity * HT_LOAD_FACTOR) {
        if (ht_grow(ht) != 0) return;
    }

    int idx = ht_probe(ht, key);
    if (idx < 0) return;

    if (!ht->entries[idx].active) {
        ht->entries[idx].key = strdup(key);
        if (!ht->entries[idx].key) return;
        ht->entries[idx].active = 1;
        ht->count++;
    }
    ht->entries[idx].value = value;
}

void *ht_lookup(HashTable *ht, const char *key) {
    if (!ht || !key) return NULL;
    int idx = ht_probe(ht, key);
    if (idx < 0 || !ht->entries[idx].active)
        return NULL;
    return ht->entries[idx].value;
}

int ht_contains(HashTable *ht, const char *key) {
    if (!ht || !key) return 0;
    int idx = ht_probe(ht, key);
    return (idx >= 0 && ht->entries[idx].active) ? 1 : 0;
}

void ht_delete(HashTable *ht, const char *key) {
    if (!ht || !key) return;
    int idx = ht_probe(ht, key);
    if (idx < 0 || !ht->entries[idx].active)
        return;
    free(ht->entries[idx].key);
    ht->entries[idx].key = NULL;
    ht->entries[idx].value = NULL;
    ht->entries[idx].active = 0;
    ht->count--;
}

void **ht_values(HashTable *ht, int *out_count) {
    if (!ht || !out_count) return NULL;
    void **values = malloc((size_t)ht->count * sizeof(*values));
    if (!values) return NULL;
    int idx = 0;
    for (int i = 0; i < ht->capacity; i++) {
        if (ht->entries[i].active)
            values[idx++] = ht->entries[i].value;
    }
    *out_count = idx;
    return values;
}
