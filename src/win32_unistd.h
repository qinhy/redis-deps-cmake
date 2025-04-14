#ifndef WIN32_UNISTD_H
#define WIN32_UNISTD_H

#ifdef _WIN32
#include <stdlib.h>
#include <io.h>
#include <process.h>
#include <direct.h>

// Map POSIX names to Windows equivalents
#define R_OK    4       /* Test for read permission    */
#define W_OK    2       /* Test for write permission   */
#define F_OK    0       /* Test for existence          */
#define X_OK    1       /* Test for execute permission */

#define access _access
#define getcwd _getcwd
#define chdir _chdir
#define unlink _unlink
#define rmdir _rmdir
#define sleep(x) Sleep((x)*1000)

#endif /* _WIN32 */

#endif /* WIN32_UNISTD_H */ 