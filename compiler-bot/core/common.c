#include "common.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

int read_stdin(char *buf, size_t size) {
    if (!buf || size == 0) return -1;

    size_t i = 0;
    int c;
    while ((c = getchar()) != EOF && i < size - 1)
        buf[i++] = (char)c;
    buf[i] = '\0';
    return (int)i;
}

const char *parse_flag(char **argv, const char *flag) {
    if (!argv || !flag) return NULL;
    int flen = (int)strlen(flag);
    for (int i = 1; argv[i]; i++) {
        if (strncmp(argv[i], flag, (size_t)flen) == 0 &&
            argv[i][flen] == '=') {
            return argv[i] + flen + 1;
        }
    }
    return NULL;
}

int parse_int_flag(char **argv, const char *flag, int default_val) {
    const char *val = parse_flag(argv, flag);
    if (!val) return default_val;
    char *end = NULL;
    long result = strtol(val, &end, 10);
    if (end == val || *end != '\0')
        return default_val;
    return (int)result;
}

void log_info(const char *msg) {
    fprintf(stdout, "[INFO] %s\n", msg);
}

void log_error(const char *msg) {
    fprintf(stderr, "[ERROR] %s\n", msg);
}

void log_warn(const char *msg) {
    fprintf(stdout, "[WARN] %s\n", msg);
}
