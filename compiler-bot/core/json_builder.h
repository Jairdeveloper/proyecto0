#ifndef JSON_BUILDER_H
#define JSON_BUILDER_H

#include <stddef.h>

typedef struct {
    char *buf;
    size_t cap;
    size_t len;
    int    depth;
    int    need_comma;
} JSONBuilder;

JSONBuilder *jb_create(size_t initial_cap);
void         jb_free(JSONBuilder *jb);
void         jb_clear(JSONBuilder *jb);
const char  *jb_string(JSONBuilder *jb);

void jb_begin_object(JSONBuilder *jb);
void jb_end_object(JSONBuilder *jb);
void jb_begin_array(JSONBuilder *jb);
void jb_end_array(JSONBuilder *jb);
void jb_key(JSONBuilder *jb, const char *key);
void jb_string_value(JSONBuilder *jb, const char *val);
void jb_int_value(JSONBuilder *jb, int val);
void jb_bool_value(JSONBuilder *jb, int val);
void jb_null_value(JSONBuilder *jb);
void jb_raw(JSONBuilder *jb, const char *raw);

#endif
