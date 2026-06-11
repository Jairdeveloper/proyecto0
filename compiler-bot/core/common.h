#ifndef COMMON_H
#define COMMON_H

#include <stddef.h>

/**
 * Read all of stdin into buf, null-terminated.
 * @param size  Max bytes to read (including null terminator).
 * @return      Number of bytes read, or -1 on error.
 */
int read_stdin(char *buf, size_t size);

/**
 * Parse --flag=value from argv. Returns pointer to value part, or NULL.
 */
const char *parse_flag(char **argv, const char *flag);

/**
 * Like parse_flag but returns an int. Returns default_val if flag absent
 * or value is not a valid integer.
 */
int parse_int_flag(char **argv, const char *flag, int default_val);

void log_info(const char *msg);
void log_error(const char *msg);
void log_warn(const char *msg);

#endif
