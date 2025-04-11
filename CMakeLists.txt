# --- Dependencies First ---
# OpenSSL
if(REDIS_ENABLE_TLS)
  set(OPENSSL_INCLUDE_DIR "${OPENSSL_WIN64_ROOT}/include")
  set(OPENSSL_LIBRARIES "${OPENSSL_WIN64_ROOT}/lib/libssl" "${OPENSSL_WIN64_ROOT}/lib/libcrypto")
endif()

# Set policy for linenoise to avoid warnings
cmake_policy(SET CMP0048 NEW)

# Add subdirectories for dependencies
add_subdirectory(deps/hiredis)
add_subdirectory(deps/linenoise)
add_subdirectory(deps/jemalloc)

# Set compile definitions for MSVC
if(MSVC)
  target_compile_definitions(jemalloc PRIVATE __STDC_VERSION__=199000L)
endif()
# --------------------------

cmake_minimum_required(VERSION 4.0)

if(POLICY CMP0042)
  cmake_policy(SET CMP0042 NEW)
endif()

project(redis-windows VERSION 7.2 LANGUAGES C CXX)

# --- Build type configuration ---
if(NOT CMAKE_BUILD_TYPE)
  set(CMAKE_BUILD_TYPE Release)
endif()

# --- Configuration Options ---
option(REDIS_ENABLE_TLS "Enable TLS support (OPENSSL)" OFF)
option(REDIS_BUILD_TESTS "Build tests" OFF)
option(REDIS_USE_STATIC_RUNTIME "Use static C runtime" OFF)
option(REDIS_BUILD_BENCHMARK "Build redis-benchmark utility" OFF)
option(REDIS_BUILD_CLI "Build redis-cli utility" OFF)
set(OPENSSL_WIN64_ROOT "${CMAKE_CURRENT_SOURCE_DIR}/deps/OpenSSL" CACHE PATH "Path to OpenSSL-Win64 root directory")
set(LUA_INCLUDE_DIR "${CMAKE_CURRENT_SOURCE_DIR}/deps/lua/include" CACHE PATH "Path to lua include directory")
set(LUA_LIBRARY "${CMAKE_CURRENT_SOURCE_DIR}/deps/lua/lua.lib" CACHE PATH "Path to lua library")

# --- Compiler Settings ---
set(CMAKE_C_STANDARD 99)
set(CMAKE_C_STANDARD_REQUIRED ON)

if(MSVC)
  add_definitions(-D_CRT_SECURE_NO_WARNINGS)
  
  # Configure static runtime if requested
  if(REDIS_USE_STATIC_RUNTIME)
    foreach(flag_var
        CMAKE_C_FLAGS CMAKE_C_FLAGS_DEBUG CMAKE_C_FLAGS_RELEASE
        CMAKE_C_FLAGS_MINSIZEREL CMAKE_C_FLAGS_RELWITHDEBINFO
        CMAKE_CXX_FLAGS CMAKE_CXX_FLAGS_DEBUG CMAKE_CXX_FLAGS_RELEASE
        CMAKE_CXX_FLAGS_MINSIZEREL CMAKE_CXX_FLAGS_RELWITHDEBINFO)
      if(${flag_var} MATCHES "/MD")
        string(REGEX REPLACE "/MD" "/MT" ${flag_var} "${${flag_var}}")
      endif()
    endforeach()
  endif()

  set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} /wd5105 /wd4267")
  set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} /FC /d2Zi+ /Zi /FS /nologo /W3 /WX /GS /Zc:wchar_t /Zc:forScope /errorReport:queue /D_PREFAST_=1")

endif()



# --- Common Definitions and Libraries ---
set(REDIS_COMMON_DEFINITIONS
  _WIN32_WINNT=0x0601
  WIN32_LEAN_AND_MEAN
  NOMINMAX
  UNICODE
  _UNICODE
  _WIN64
)

if(REDIS_ENABLE_TLS)
  list(APPEND REDIS_COMMON_DEFINITIONS USE_OPENSSL)
endif()

list(APPEND REDIS_COMMON_DEFINITIONS USE_JEMALLOC)

set(REDIS_COMMON_LIBS
  ws2_32
  advapi32
  userenv
  crypt32
  shlwapi
  bcrypt
  psapi
)

if(REDIS_ENABLE_TLS)
  list(APPEND REDIS_COMMON_LIBS ${OPENSSL_LIBRARIES})
endif()

# --- Include Directories ---
include_directories(
  ${CMAKE_CURRENT_SOURCE_DIR}/src
  ${CMAKE_CURRENT_SOURCE_DIR}/src/modules
  ${CMAKE_CURRENT_SOURCE_DIR}/deps/hiredis
  ${CMAKE_CURRENT_SOURCE_DIR}/deps/linenoise/include
  ${LUA_INCLUDE_DIR}
  ${CMAKE_CURRENT_SOURCE_DIR}/deps/jemalloc/include
  ${CMAKE_CURRENT_SOURCE_DIR}/deps/jemalloc/include/msvc_compat
)

if(REDIS_ENABLE_TLS)
  include_directories(${OPENSSL_INCLUDE_DIR})
endif()

# --- Windows Interop Files ---
set(WIN32_INTEROP_SRC
  # src/Win32_Interop/Win32_APIs.c
  # src/Win32_Interop/Win32_Error.c
  # src/Win32_Interop/Win32_Time.c
  # src/Win32_Interop/Win32_PThread.c
  # src/Win32_Interop/Win32_Signal_Process.c
  # src/Win32_Interop/Win32_ThreadControl.c
  # src/Win32_Interop/win32fixes.c
  # src/Win32_Interop/win32_wsiocp.c
  # src/Win32_Interop/Win32_FDAPI.cpp
  # src/Win32_Interop/Win32_Common.cpp
  # src/Win32_Interop/Win32_RedisLog.c
  # src/Win32_Interop/win32_rfdmap.cpp
  # src/Win32_Interop/Win32_EventLog.cpp
  # src/Win32_Interop/Win32_QFork_impl.c
  # src/Win32_Interop/Win32_QFork.cpp
  # src/Win32_Interop/Win32_variadicFunctor.cpp
  # src/Win32_Interop/Win32_service.cpp
)

# --- Redis Server ---
file(GLOB_RECURSE REDIS_SRC
  src/*.c
  src/modules/*.c
)

# Filter out specific files
list(FILTER REDIS_SRC EXCLUDE REGEX ".*test.*.c$")
list(FILTER REDIS_SRC EXCLUDE REGEX ".*posix.*.c$")
list(FILTER REDIS_SRC EXCLUDE REGEX ".*redis-benchmark\\.c$")
list(FILTER REDIS_SRC EXCLUDE REGEX ".*redis-cli\\.c$")

# Remove platform-specific files on Windows
if(WIN32)
  list(FILTER REDIS_SRC EXCLUDE REGEX ".*ae_epoll\\.c$")
  list(FILTER REDIS_SRC EXCLUDE REGEX ".*ae_evport\\.c$")
  list(FILTER REDIS_SRC EXCLUDE REGEX ".*ae_kqueue\\.c$")
  list(FILTER REDIS_SRC EXCLUDE REGEX ".*ae_select\\.c$")
  add_executable(redis-server ${REDIS_SRC} ${WIN32_INTEROP_SRC})
else()
  add_executable(redis-server ${REDIS_SRC})
endif()
target_compile_definitions(redis-server PRIVATE ${REDIS_COMMON_DEFINITIONS})
target_link_libraries(redis-server ${REDIS_COMMON_LIBS} ${LUA_LIBRARY} jemalloc)

# --- Redis Benchmark ---
if(REDIS_BUILD_BENCHMARK)
  set(BENCHMARK_SRC
    src/redis-benchmark.c
    src/ae.c
    src/zmalloc.c
    src/adlist.c
    src/sds.c
  )

  if(WIN32)
    list(APPEND BENCHMARK_SRC ${WIN32_INTEROP_SRC})
  endif()

  add_executable(redis-benchmark ${BENCHMARK_SRC})
  target_compile_definitions(redis-benchmark PRIVATE ${REDIS_COMMON_DEFINITIONS})
  if(MSVC)
    target_compile_options(redis-benchmark PRIVATE /wd5105)
  endif()
  target_link_libraries(redis-benchmark hiredis ${REDIS_COMMON_LIBS})
endif()

# --- Redis CLI ---
if(REDIS_BUILD_CLI)
  set(CLI_SRC
    src/redis-cli.c
    src/ae.c
    src/zmalloc.c
    src/adlist.c
    src/sds.c
    src/dict.c
    src/anet.c
    src/crc16.c
    src/crc64.c
  )

  if(WIN32)
    list(APPEND CLI_SRC 
      ${WIN32_INTEROP_SRC}
      src/Win32_Interop/Win32_ANSI.c
    )
  endif()

  add_executable(redis-cli ${CLI_SRC})
  target_compile_definitions(redis-cli PRIVATE ${REDIS_COMMON_DEFINITIONS})
  if(MSVC)
    target_compile_options(redis-cli PRIVATE /wd5105)
  endif()
  target_link_libraries(redis-cli hiredis linenoise ${REDIS_COMMON_LIBS})
endif()

# --- Output and Install Configuration ---
set(REDIS_TARGETS redis-server)
if(REDIS_BUILD_BENCHMARK)
  list(APPEND REDIS_TARGETS redis-benchmark)
endif()
if(REDIS_BUILD_CLI)
  list(APPEND REDIS_TARGETS redis-cli)
endif()

foreach(target ${REDIS_TARGETS})
  set_target_properties(${target} PROPERTIES
    OUTPUT_NAME "${target}"
    RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/bin
  )
endforeach()

install(TARGETS ${REDIS_TARGETS} DESTINATION bin)