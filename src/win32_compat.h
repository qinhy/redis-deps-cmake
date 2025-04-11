#ifndef WIN32_COMPAT_H
#define WIN32_COMPAT_H

#ifdef _WIN32
struct iovec {
    void  *iov_base;    /* Starting address */
    size_t iov_len;     /* Number of bytes to transfer */
};
#else
#include <sys/uio.h>
#endif

#endif /* WIN32_COMPAT_H */