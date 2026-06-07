#include "json_builder.h"
#include <stdlib.h>
#include <string.h>
#include <stdio.h>

#define JB_GROW_FACTOR 2

JSONBuilder *jb_create(size_t initial_cap) {
    JSONBuilder *jb = calloc(1, sizeof(JSONBuilder));
    if (!jb) return NULL;
    if (initial_cap < 256) initial_cap = 256;
    jb->buf = malloc(initial_cap);
    jb->cap = initial_cap;
    jb->len = 0;
    jb->buf[0] = '\0';
    return jb;
}

void jb_free(JSONBuilder *jb) {
    if (jb) { free(jb->buf); free(jb); }
}

void jb_clear(JSONBuilder *jb) {
    jb->len = 0;
    jb->depth = 0;
    jb->need_comma = 0;
    if (jb->buf) jb->buf[0] = '\0';
}

const char *jb_string(JSONBuilder *jb) {
    return jb->buf;
}

static void jb_grow(JSONBuilder *jb, size_t needed) {
    if (jb->len + needed + 1 <= jb->cap) return;
    size_t new_cap = jb->cap * JB_GROW_FACTOR;
    while (jb->len + needed + 1 > new_cap)
        new_cap *= JB_GROW_FACTOR;
    jb->buf = realloc(jb->buf, new_cap);
    jb->cap = new_cap;
}

static void jb_emit(JSONBuilder *jb, const char *s, size_t n) {
    jb_grow(jb, n);
    memcpy(jb->buf + jb->len, s, n);
    jb->len += n;
    jb->buf[jb->len] = '\0';
}

static void jb_comma_newline(JSONBuilder *jb) {
    if (jb->need_comma) {
        jb_emit(jb, ",\n", 2);
    } else {
        jb_emit(jb, "\n", 1);
        jb->need_comma = 1;
    }
    for (int i = 0; i < jb->depth; i++)
        jb_emit(jb, "  ", 2);
}

void jb_begin_object(JSONBuilder *jb) {
    jb_comma_newline(jb);
    jb_emit(jb, "{", 1);
    jb->depth++;
    jb->need_comma = 0;
}

void jb_end_object(JSONBuilder *jb) {
    jb->depth--;
    jb->need_comma = 1;
    jb_emit(jb, "\n", 1);
    for (int i = 0; i < jb->depth; i++)
        jb_emit(jb, "  ", 2);
    jb_emit(jb, "}", 1);
}

void jb_begin_array(JSONBuilder *jb) {
    jb_comma_newline(jb);
    jb_emit(jb, "[", 1);
    jb->depth++;
    jb->need_comma = 0;
}

void jb_end_array(JSONBuilder *jb) {
    jb->depth--;
    jb->need_comma = 1;
    jb_emit(jb, "\n", 1);
    for (int i = 0; i < jb->depth; i++)
        jb_emit(jb, "  ", 2);
    jb_emit(jb, "]", 1);
}

void jb_key(JSONBuilder *jb, const char *key) {
    jb_comma_newline(jb);
    size_t klen = strlen(key);
    jb_grow(jb, klen + 4);
    jb->buf[jb->len++] = '"';
    memcpy(jb->buf + jb->len, key, klen);
    jb->len += klen;
    jb_emit(jb, "\": ", 3);
    jb->need_comma = 0;
}

static void jb_escape_string(JSONBuilder *jb, const char *val) {
    jb->buf[jb->len++] = '"';
    while (*val) {
        switch (*val) {
            case '"':  jb_emit(jb, "\\\"", 2); break;
            case '\\': jb_emit(jb, "\\\\", 2); break;
            case '\n': jb_emit(jb, "\\n", 2); break;
            case '\t': jb_emit(jb, "\\t", 2); break;
            case '\r': jb_emit(jb, "\\r", 2); break;
            default:   jb_grow(jb, 1);
                       jb->buf[jb->len++] = *val; break;
        }
        val++;
    }
    jb->buf[jb->len++] = '"';
    jb->buf[jb->len] = '\0';
}

void jb_string_value(JSONBuilder *jb, const char *val) {
    if (!val) { jb_null_value(jb); return; }
    jb_grow(jb, strlen(val) * 2 + 2);  /* worst-case escaping */
    jb_escape_string(jb, val);
}

void jb_int_value(JSONBuilder *jb, int val) {
    char tmp[32];
    int n = snprintf(tmp, sizeof(tmp), "%d", val);
    jb_emit(jb, tmp, (size_t)n);
}

void jb_bool_value(JSONBuilder *jb, int val) {
    jb_emit(jb, val ? "true" : "false", val ? 4 : 5);
}

void jb_null_value(JSONBuilder *jb) {
    jb_emit(jb, "null", 4);
}

void jb_raw(JSONBuilder *jb, const char *raw) {
    jb_emit(jb, raw, strlen(raw));
}
