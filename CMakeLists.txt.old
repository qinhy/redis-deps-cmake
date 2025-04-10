cmake_minimum_required(VERSION 3.12)
project(redis C)

# ------------------------------------------------------------------------------------
# Options (analogous to the Makefile variables)
# ------------------------------------------------------------------------------------

option(USE_JEMALLOC "Use Jemalloc" OFF)
option(USE_TCMALLOC "Use TCMalloc" OFF)
option(USE_TCMALLOC_MINIMAL "Use TCMalloc minimal" OFF)
option(USE_SYSTEMD "Use systemd" OFF)
option(USE_BACKTRACE "Use backtrace" OFF)
option(BUILD_TLS "Build with TLS support ('no', 'yes', or 'module')" OFF)
option(OPTIMIZE_FOR_DEBUG "Disable optimizations (similar to 'noopt')" OFF)
option(SANITIZER_ADDRESS "Enable Address Sanitizer" OFF)
option(SANITIZER_UNDEFINED "Enable Undefined Behavior Sanitizer" OFF)
option(SANITIZER_THREAD "Enable Thread Sanitizer" OFF)

# ------------------------------------------------------------------------------------
# Detect compiler / platform specifics (rough analog to Makefile logic)
# ------------------------------------------------------------------------------------
include(CheckCSourceCompiles)
include(CheckSymbolExists)

# 1. Set default flags for compilers:
set(DEFAULT_C_FLAGS "-Wall -W -Wno-missing-field-initializers -Werror=deprecated-declarations -Wstrict-prototypes")

# 2. Check if we can use <stdatomic.h> and set C standard:
file(WRITE "${CMAKE_BINARY_DIR}/check_atomic.c" "#include <stdatomic.h>\nint main(){return 0;}\n")
try_compile(HAVE_C11_ATOMIC
  "${CMAKE_BINARY_DIR}"
  "${CMAKE_BINARY_DIR}/check_atomic.c"
  CMAKE_FLAGS "-DCMAKE_C_STANDARD=11"
)
if(HAVE_C11_ATOMIC)
  set(STD_FLAG "-std=gnu11")
else()
  # fallback
  set(STD_FLAG "-std=c99")
endif()

# 3. Clang vs. GCC detection
#    (We don’t use the Makefile’s exact approach, but we can replicate the essence)
if(CMAKE_C_COMPILER_ID MATCHES "Clang")
  set(IS_CLANG TRUE)
else()
  set(IS_CLANG FALSE)
endif()

# 4. Operating system specifics
if(CMAKE_SYSTEM_NAME STREQUAL "Linux")
  set(OS_LINUX TRUE)
elseif(CMAKE_SYSTEM_NAME STREQUAL "Darwin")
  set(OS_DARWIN TRUE)
elseif(CMAKE_SYSTEM_NAME STREQUAL "FreeBSD")
  set(OS_FREEBSD TRUE)
elseif(CMAKE_SYSTEM_NAME STREQUAL "OpenBSD")
  set(OS_OPENBSD TRUE)
elseif(CMAKE_SYSTEM_NAME STREQUAL "NetBSD")
  set(OS_NETBSD TRUE)
elseif(CMAKE_SYSTEM_NAME STREQUAL "DragonFly")
  set(OS_DRAGONFLY TRUE)
elseif(CMAKE_SYSTEM_NAME STREQUAL "SunOS")
  set(OS_SUN TRUE)
elseif(CMAKE_SYSTEM_NAME STREQUAL "AIX")
  set(OS_AIX TRUE)
elseif(CMAKE_SYSTEM_NAME STREQUAL "Haiku")
  set(OS_HAIKU TRUE)
endif()

# ------------------------------------------------------------------------------------
# Decide on an allocator (similar to MALLOC= in the Makefile)
# ------------------------------------------------------------------------------------
# By default on Linux we pick jemalloc if available, otherwise fallback to libc.
# We do a simple approach: if the user sets USE_JEMALLOC or USE_TCMALLOC, that wins.
set(MALLOC_LIB "")
if(USE_TCMALLOC)
  add_compile_definitions(USE_TCMALLOC)
  set(MALLOC_LIB "tcmalloc")
elseif(USE_TCMALLOC_MINIMAL)
  add_compile_definitions(USE_TCMALLOC)
  set(MALLOC_LIB "tcmalloc_minimal")
elseif(USE_JEMALLOC)
  add_compile_definitions(USE_JEMALLOC)
  # We'll assume that you either have jemalloc as a subproject in ../deps/jemalloc
  # or installed on your system.  The Makefile includes a local static library from deps.
  #
  # Example of linking to local static library:
  #   set(MALLOC_LIB "${CMAKE_CURRENT_SOURCE_DIR}/../deps/jemalloc/lib/libjemalloc.a")
  # If you want to search system wide:
  #   find_library(JEMALLOC_LIB jemalloc)
  #   set(MALLOC_LIB "${JEMALLOC_LIB}")
  #
  # For demonstration, assume we link to the local static library in ../deps.
  set(MALLOC_LIB "${CMAKE_CURRENT_SOURCE_DIR}/../deps/jemalloc/lib/libjemalloc.a")
else()
  # default to libc
endif()

# ------------------------------------------------------------------------------------
# Handle sanitizer options
# ------------------------------------------------------------------------------------
set(SANITIZER_FLAGS "")
if(SANITIZER_ADDRESS)
  set(SANITIZER_FLAGS "${SANITIZER_FLAGS} -fsanitize=address -fno-sanitize-recover=all -fno-omit-frame-pointer")
elseif(SANITIZER_UNDEFINED)
  set(SANITIZER_FLAGS "${SANITIZER_FLAGS} -fsanitize=undefined -fno-sanitize-recover=all -fno-omit-frame-pointer")
elseif(SANITIZER_THREAD)
  set(SANITIZER_FLAGS "${SANITIZER_FLAGS} -fsanitize=thread -fno-sanitize-recover=all -fno-omit-frame-pointer")
endif()

# ------------------------------------------------------------------------------------
# Optimization flags
# ------------------------------------------------------------------------------------
if(OPTIMIZE_FOR_DEBUG)
  # Like "noopt"
  set(OPT_FLAGS "-O0")
else()
  # Like the Makefile’s default -O3 + LTO
  set(OPT_FLAGS "-O3")
  if(IS_CLANG)
    set(OPT_FLAGS "${OPT_FLAGS} -flto")
  else()
    set(OPT_FLAGS "${OPT_FLAGS} -flto=auto")
  endif()
  # The Makefile adds -fno-omit-frame-pointer unless O0
  set(OPT_FLAGS "${OPT_FLAGS} -fno-omit-frame-pointer")
endif()

# ------------------------------------------------------------------------------------
# Summarize final compile/link flags
# ------------------------------------------------------------------------------------
# By default, let’s include debug info
set(DEBUG_FLAGS "-g -ggdb")

# CMake sets CMAKE_C_FLAGS_<CONFIG> for us. We can unify them into one for a single-config build:
set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} ${DEFAULT_C_FLAGS} ${STD_FLAG} ${DEBUG_FLAGS} ${OPT_FLAGS} ${SANITIZER_FLAGS}")

# Additional platform-specific link libraries
set(PLATFORM_LIBS "")
if(OS_LINUX OR OS_DRAGONFLY OR OS_FREEBSD OR OS_NETBSD OR OS_OPENBSD OR OS_HAIKU)
  list(APPEND PLATFORM_LIBS "dl" "m" "pthread")
  if(OS_LINUX)
    list(APPEND PLATFORM_LIBS "rt")
  endif()
elseif(OS_DARWIN)
  list(APPEND PLATFORM_LIBS "dl" "m")
elseif(OS_SUN)
  list(APPEND PLATFORM_LIBS "dl" "nsl" "socket" "resolv" "pthread" "rt")
  add_compile_definitions(__EXTENSIONS__ _XPG6)
elseif(OS_AIX)
  list(APPEND PLATFORM_LIBS "dl" "pthread" "crypt" "bsd")
elseif(WIN32)
  message(FATAL_ERROR "Windows is not officially handled by this Makefile. You'd need adjustments.")
else()
  # fallback
  list(APPEND PLATFORM_LIBS "dl" "m" "pthread")
endif()

if(USE_BACKTRACE)
  # The Makefile uses -DUSE_BACKTRACE, plus linking with -lexecinfo if on BSD, etc.
  add_compile_definitions(USE_BACKTRACE)
  # For demonstration, just assume you have execinfo if you’re on a *BSD
  if(OS_FREEBSD OR OS_NETBSD OR OS_OPENBSD OR OS_DRAGONFLY)
    list(APPEND PLATFORM_LIBS "execinfo")
  endif()
endif()

# On certain ARM builds, the Makefile adds -funwind-tables
if(CMAKE_SYSTEM_PROCESSOR MATCHES "^(arm|aarch64)")
  set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} -funwind-tables")
endif()

# systemd
if(USE_SYSTEMD)
  add_compile_definitions(HAVE_LIBSYSTEMD)
  # Typically discovered via pkg-config:
  #   pkg_check_modules(SYSTEMD libsystemd)
  # if found, do e.g.:
  #   list(APPEND PLATFORM_LIBS "${SYSTEMD_LIBRARIES}")
  #
  # Or if we can’t pkg-config, just do the fallback:
  list(APPEND PLATFORM_LIBS "systemd")
endif()

# Gather final link flags.  For demonstration, we apply them globally.
# If you need them only for certain targets, set them individually.
set(CMAKE_EXE_LINKER_FLAGS "${CMAKE_EXE_LINKER_FLAGS} ${OPT_FLAGS} ${SANITIZER_FLAGS}")

# ------------------------------------------------------------------------------------
# TLS / OpenSSL
# ------------------------------------------------------------------------------------
set(OPENSSL_LIBS "")
if(BUILD_TLS)
  # The Makefile has multiple states: "no", "yes", "module"
  # We’ll represent "yes" or "module" by toggling.  If BUILD_TLS is "module", we set a definition.
  if(BUILD_TLS STREQUAL "module")
    add_compile_definitions(USE_OPENSSL=2 BUILD_TLS_MODULE=2)
  else()
    add_compile_definitions(USE_OPENSSL=1 BUILD_TLS_MODULE=0)
  endif()

  # Typically discover with find_package(OpenSSL REQUIRED), for example:
  find_package(OpenSSL REQUIRED)
  if(OpenSSL_FOUND)
    set(OPENSSL_LIBS "${OpenSSL_LIBRARIES}")
    include_directories(${OpenSSL_INCLUDE_DIR})
  else()
    message(WARNING "OpenSSL not found. TLS build may fail.")
    list(APPEND OPENSSL_LIBS "ssl" "crypto")
  endif()
endif()

# ------------------------------------------------------------------------------------
# Additional libraries (libatomic, etc.)
# ------------------------------------------------------------------------------------
# The Makefile links -latomic on Linux ARM
if(CMAKE_SYSTEM_PROCESSOR MATCHES "^(arm|aarch64)" AND OS_LINUX)
  list(APPEND PLATFORM_LIBS "atomic")
endif()

# The Makefile always links with -lm
if(NOT OS_AIX)  # AIX may link m differently
  list(APPEND PLATFORM_LIBS "m")
endif()

# ------------------------------------------------------------------------------------
# If building with a static Jemalloc library from deps, link that first.
if(USE_JEMALLOC AND EXISTS "${MALLOC_LIB}")
  list(INSERT PLATFORM_LIBS 0 "${MALLOC_LIB}")
elseif(USE_TCMALLOC OR USE_TCMALLOC_MINIMAL)
  # TCMalloc is usually system installed; just link it
  if(USE_TCMALLOC)
    list(INSERT PLATFORM_LIBS 0 "tcmalloc")
  else()
    list(INSERT PLATFORM_LIBS 0 "tcmalloc_minimal")
  endif()
endif()

# ------------------------------------------------------------------------------------
# Source files (mirroring the Makefile’s object lists)
# ------------------------------------------------------------------------------------
set(REDIS_SERVER_SRCS
  threads_mngr.c
  adlist.c
  quicklist.c
  ae.c
  anet.c
  dict.c
  ebuckets.c
  mstr.c
  kvstore.c
  server.c
  sds.c
  zmalloc.c
  lzf_c.c
  lzf_d.c
  pqsort.c
  zipmap.c
  sha1.c
  ziplist.c
  release.c
  networking.c
  util.c
  object.c
  db.c
  replication.c
  rdb.c
  t_string.c
  t_list.c
  t_set.c
  t_zset.c
  t_hash.c
  config.c
  aof.c
  pubsub.c
  multi.c
  debug.c
  sort.c
  intset.c
  syncio.c
  cluster.c
  cluster_legacy.c
  crc16.c
  endianconv.c
  slowlog.c
  eval.c
  bio.c
  rio.c
  rand.c
  memtest.c
  syscheck.c
  crcspeed.c
  crc64.c
  bitops.c
  sentinel.c
  notify.c
  setproctitle.c
  blocked.c
  hyperloglog.c
  latency.c
  sparkline.c
  redis-check-rdb.c
  redis-check-aof.c
  geo.c
  lazyfree.c
  module.c
  evict.c
  expire.c
  geohash.c
  geohash_helper.c
  childinfo.c
  defrag.c
  siphash.c
  rax.c
  t_stream.c
  listpack.c
  localtime.c
  lolwut.c
  lolwut5.c
  lolwut6.c
  acl.c
  tracking.c
  socket.c
  tls.c
  sha256.c
  timeout.c
  setcpuaffinity.c
  monotonic.c
  mt19937-64.c
  resp_parser.c
  call_reply.c
  script_lua.c
  script.c
  functions.c
  function_lua.c
  commands.c
  strl.c
  connection.c
  unix.c
  logreqres.c
)

set(REDIS_CLI_SRCS
  anet.c
  adlist.c
  dict.c
  redis-cli.c
  zmalloc.c
  release.c
  ae.c
  redisassert.c
  crcspeed.c
  crc64.c
  siphash.c
  crc16.c
  monotonic.c
  cli_common.c
  mt19937-64.c
  strl.c
  cli_commands.c
)

set(REDIS_BENCHMARK_SRCS
  ae.c
  anet.c
  redis-benchmark.c
  adlist.c
  dict.c
  zmalloc.c
  redisassert.c
  release.c
  crcspeed.c
  crc64.c
  siphash.c
  crc16.c
  monotonic.c
  cli_common.c
  mt19937-64.c
  strl.c
)

# ------------------------------------------------------------------------------------
# Include paths for local dependencies (mirroring -I../deps/...)
# (You can also do add_subdirectory calls to build those.)
# ------------------------------------------------------------------------------------
include_directories(
  "${CMAKE_CURRENT_SOURCE_DIR}/../deps/hiredis"
  "${CMAKE_CURRENT_SOURCE_DIR}/../deps/linenoise"
  "${CMAKE_CURRENT_SOURCE_DIR}/../deps/lua/src"
  "${CMAKE_CURRENT_SOURCE_DIR}/../deps/hdr_histogram"
  "${CMAKE_CURRENT_SOURCE_DIR}/../deps/fpconv"
)

# If you are building these deps from source:
#   add_subdirectory("../deps/hiredis" ...)
#   add_subdirectory("../deps/linenoise" ...)
#   ...
# or link them via find_package, etc.
# For demonstration, assume we have static libraries:
set(HIREDIS_LIB "${CMAKE_CURRENT_SOURCE_DIR}/../deps/hiredis/libhiredis.a")
set(HIREDIS_SSL_LIB "${CMAKE_CURRENT_SOURCE_DIR}/../deps/hiredis/libhiredis_ssl.a")
set(LUA_LIB "${CMAKE_CURRENT_SOURCE_DIR}/../deps/lua/src/liblua.a")
set(HDRHISTOGRAM_LIB "${CMAKE_CURRENT_SOURCE_DIR}/../deps/hdr_histogram/libhdrhistogram.a")
set(FPCONV_LIB "${CMAKE_CURRENT_SOURCE_DIR}/../deps/fpconv/libfpconv.a")
set(LINENOISE_OBJ "${CMAKE_CURRENT_SOURCE_DIR}/../deps/linenoise/linenoise.o")

# ------------------------------------------------------------------------------------
# Targets
# ------------------------------------------------------------------------------------

# 1. Redis server
add_executable(redis-server ${REDIS_SERVER_SRCS})
target_link_libraries(redis-server
  PRIVATE
    ${HIREDIS_LIB}
    ${LUA_LIB}
    ${HDRHISTOGRAM_LIB}
    ${FPCONV_LIB}
    ${OPENSSL_LIBS}   # may be empty if not building TLS
    ${PLATFORM_LIBS}
)

# 2. Redis sentinel, redis-check-rdb, redis-check-aof
#    The Makefile simply copies the redis-server binary to produce these. 
#    In CMake we can do symlinks or separate aliases.  For a quick translation, 
#    we can create custom commands or do “copies” at install time.

# 3. Redis CLI
add_executable(redis-cli ${REDIS_CLI_SRCS})
target_link_libraries(redis-cli
  PRIVATE
    ${HIREDIS_LIB}
    ${LINENOISE_OBJ}
    ${HDRHISTOGRAM_LIB}
    ${OPENSSL_LIBS}
    ${PLATFORM_LIBS}
)

# 4. Redis benchmark
add_executable(redis-benchmark ${REDIS_BENCHMARK_SRCS})
target_link_libraries(redis-benchmark
  PRIVATE
    ${HIREDIS_LIB}
    ${HDRHISTOGRAM_LIB}
    ${OPENSSL_LIBS}
    ${PLATFORM_LIBS}
)

# 5. redis-tls.so if BUILD_TLS=module
if(BUILD_TLS STREQUAL "module")
  add_library(redis-tls MODULE tls.c)
  # The .so is built from a single file in the Makefile, linking hiredis_ssl, SSL, etc.
  target_link_libraries(redis-tls
    PRIVATE
      ${HIREDIS_SSL_LIB}
      ${OPENSSL_LIBS}
      ${PLATFORM_LIBS}
  )
  set_target_properties(redis-tls PROPERTIES
    PREFIX ""           # so the library is called redis-tls.so
    SUFFIX ".so"
  )
endif()

# ------------------------------------------------------------------------------------
# Installation logic (mirrors the 'install' target in Makefile)
# ------------------------------------------------------------------------------------
include(GNUInstallDirs)

install(TARGETS redis-server redis-cli redis-benchmark
  RUNTIME DESTINATION ${CMAKE_INSTALL_BINDIR}
)

# “Sentinel”, “check-rdb”, and “check-aof” are effectively the same binary as redis-server.
# We can either create symlinks or additional copies at install time:
install(CODE "
  execute_process(
    COMMAND \${CMAKE_COMMAND} -E create_symlink
      redis-server \$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/${CMAKE_INSTALL_BINDIR}/redis-check-rdb
  )
  execute_process(
    COMMAND \${CMAKE_COMMAND} -E create_symlink
      redis-server \$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/${CMAKE_INSTALL_BINDIR}/redis-check-aof
  )
  execute_process(
    COMMAND \${CMAKE_COMMAND} -E create_symlink
      redis-server \$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/${CMAKE_INSTALL_BINDIR}/redis-sentinel
  )
")

# ------------------------------------------------------------------------------------
# Optional test targets (like 'test', 'test-sentinel', etc.)
# You could define custom commands that run Redis’s test scripts similarly:
# ------------------------------------------------------------------------------------
add_custom_target(test
  COMMAND "${CMAKE_CURRENT_SOURCE_DIR}/../runtest"
  DEPENDS redis-server redis-cli
  WORKING_DIRECTORY "${CMAKE_CURRENT_SOURCE_DIR}/.."
  COMMENT "Run the Redis test suite"
)

add_custom_target(test-sentinel
  COMMAND "${CMAKE_CURRENT_SOURCE_DIR}/../runtest-sentinel"
  DEPENDS redis-server redis-cli
  WORKING_DIRECTORY "${CMAKE_CURRENT_SOURCE_DIR}/.."
  COMMENT "Run the Sentinel test suite"
)

add_custom_target(test-cluster
  COMMAND "${CMAKE_CURRENT_SOURCE_DIR}/../runtest-cluster"
  DEPENDS redis-server redis-cli
  WORKING_DIRECTORY "${CMAKE_CURRENT_SOURCE_DIR}/.."
  COMMENT "Run the Cluster test suite"
)

# ------------------------------------------------------------------------------------
# “clean” is handled by CMake automatically. For “distclean”, 
# you typically remove the entire build directory in CMake.
# ------------------------------------------------------------------------------------

message(STATUS "Configuration summary for Redis:")
message(STATUS "  Build type:            ${CMAKE_BUILD_TYPE}")
message(STATUS "  Compiler ID:           ${CMAKE_C_COMPILER_ID}")
message(STATUS "  System:                ${CMAKE_SYSTEM_NAME}")
message(STATUS "  C Flags:               ${CMAKE_C_FLAGS}")
message(STATUS "  Linker Flags:          ${CMAKE_EXE_LINKER_FLAGS}")
message(STATUS "  Allocator library:     ${MALLOC_LIB}")
message(STATUS "  TLS build:             ${BUILD_TLS}")
message(STATUS "  Using Systemd:         ${USE_SYSTEMD}")
message(STATUS "  Using backtrace:       ${USE_BACKTRACE}")
message(STATUS "  Sanitizers:            "
                "Address=${SANITIZER_ADDRESS} "
                "UB=${SANITIZER_UNDEFINED} "
                "Thread=${SANITIZER_THREAD}")
