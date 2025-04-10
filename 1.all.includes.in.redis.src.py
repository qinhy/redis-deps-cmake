import json
import os
import re

# Directory containing Redis source files
SRC_DIR = "./src"

# Regex to capture include lines
include_pattern = re.compile(r'^\s*#\s*include\s*[<"]([^">]+)[">]')

# Store includes with file origins
includes_by_file = {}
all_includes = set()

for root, _, files in os.walk(SRC_DIR):
    for file in files:
        if file.endswith(".c") or file.endswith(".h"):
            filepath = os.path.join(root, file)
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()
                includes = []
                for line in lines:
                    match = include_pattern.match(line)
                    if match:
                        include = match.group(1)
                        includes.append(include)
                        all_includes.add(include)
                if includes:
                    includes_by_file[filepath] = includes

# Output result
print("=== Unique includes found ===")
for include in sorted(all_includes):
    print(include)

print("\n=== Includes by source file ===")
for file, headers in includes_by_file.items():
    print(f"\n{file}:")
    for header in headers:
        print(f"  {header}")


import re
from collections import defaultdict

# Provided list of all includes
all_includes = [
    "../redismodule.h", "AvailabilityMacros.h", "OS.h", "adlist.h", "ae.h", "ae_epoll.c",
    "ae_evport.c", "ae_kqueue.c", "ae_select.c", "anet.h", "arpa/inet.h", "asciilogo.h",
    "assert.h", "async.h", "atomicvar.h", "bio.h", "call_reply.h", "cli_commands.h",
    "cli_common.h", "climits", "cluster.h", "commands.def", "commands.h",
    "commands_with_reply_schema.def", "config.h", "connection.h", "connhelpers.h",
    "crc16_slottable.h", "crc64.h", "crcspeed.h", "cstdint", "cstring", "ctype.h",
    "debugmacro.h", "dict.h", "dirent.h", "dlfcn.h", "endian.h", "endianconv.h", "errno.h",
    "execinfo.h", "fcntl.h", "features.h", "float.h", "fmacros.h", "fpconv_dtoa.h",
    "functions.h", "geo.h", "geohash.h", "geohash_helper.h", "glob.h", "google/tcmalloc.h",
    "hdr_histogram.h", "hiredis.h", "hiredis_ssl.h", "intset.h", "inttypes.h",
    "jemalloc/jemalloc.h", "kernel/OS.h", "latency.h", "lauxlib.h", "libgen.h",
    "libproc.h", "limits.h", "linenoise.h", "listpack.h", "listpack_malloc.h", "locale.h",
    "lolwut.h", "lua.h", "lualib.h", "lzf.h", "lzfP.h", "mach/mach.h", "mach/mach_init.h",
    "mach/task.h", "machine/endian.h", "malloc.h", "malloc/malloc.h", "malloc_np.h",
    "math.h", "memory.h", "monotonic.h", "mt19937-64.h", "netdb.h", "netinet/in.h",
    "netinet/tcp.h", "openssl/conf.h", "openssl/decoder.h", "openssl/err.h",
    "openssl/pem.h", "openssl/rand.h", "openssl/ssl.h", "poll.h", "port.h", "pqsort.h",
    "pthread.h", "pthread_np.h", "quicklist.h", "rand.h", "rax.h", "rdb.h", "redisassert.h",
    "redismodule.h", "regex.h", "release.h", "resp_parser.h", "rio.h", "sched.h",
    "script.h", "script_lua.h", "sds.h", "sdsalloc.h", "sdscompat.h", "server.h", "sha1.h",
    "sha256.h", "signal.h", "slowlog.h", "solarisfixes.h", "sparkline.h", "stdarg.h",
    "stdatomic.h", "stddef.h", "stdint.h", "stdio.h", "stdlib.h", "stream.h", "string.h",
    "stropts.h", "sys/cpuset.h", "sys/epoll.h", "sys/event.h", "sys/feature_tests.h",
    "sys/file.h", "sys/ioctl.h", "sys/mman.h", "sys/param.h", "sys/prctl.h",
    "sys/procfs.h", "sys/resource.h", "sys/select.h", "sys/socket.h", "sys/stat.h",
    "sys/sysctl.h", "sys/time.h", "sys/types.h", "sys/uio.h", "sys/un.h", "sys/user.h",
    "sys/utsname.h", "sys/wait.h", "syscheck.h", "syslog.h", "systemd/sd-daemon.h",
    "termios.h", "testhelp.h", "time.h", "ucontext.h", "unistd.h", "util.h",
    "valgrind/helgrind.h", "version.h", "x86intrin.h", "ziplist.h", "zipmap.h", "zmalloc.h"
]

# Regex pattern for system headers (heuristic: starts with known prefixes or ends with .h)
linux_specific_keywords = [
    "sys/", "netinet/", "arpa/", "unistd.h", "fcntl.h", "poll.h", "signal.h", "dlfcn.h",
    "pthread.h", "execinfo.h", "stropts.h", "dirent.h", "ucontext.h", "syslog.h",
    "termios.h", "sched.h", "netdb.h", "mach/", "libproc.h", "prctl.h", "mman.h",
    "sysctl.h", "procfs.h", "cpuset.h", "utsname.h"
]

# Classify headers
linux_specific = []
non_linux_system = []
third_party = []
project_local = []

for header in all_includes:
    if any(header.startswith(prefix) or prefix in header for prefix in linux_specific_keywords):
        linux_specific.append(header)
    elif re.match(r'^[a-zA-Z0-9_/]+\.(h|hpp)$', header) and "/" not in header:
        non_linux_system.append(header)
    elif header.startswith("openssl/") or "jemalloc" in header or "hiredis" in header or "tcmalloc" in header:
        third_party.append(header)
    elif header.startswith("redismodule.h") or header.startswith("../") or header.endswith(".def") or "." not in header:
        project_local.append(header)
    else:
        project_local.append(header)

print(json.dumps({
    "Linux-specific": sorted(linux_specific),
    "Non-Linux system": sorted(non_linux_system),
    "3rd-party": sorted(third_party),
    "Project-local": sorted(project_local),
},indent=2))