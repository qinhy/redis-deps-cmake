cmake_minimum_required(VERSION 3.16)
project(redis-windows VERSION 7.2 LANGUAGES C)

set(CMAKE_C_STANDARD 11)
set(CMAKE_C_STANDARD_REQUIRED ON)

# Optional: Enable Release by default
if(NOT CMAKE_BUILD_TYPE)
  set(CMAKE_BUILD_TYPE Release)
endif()

# --- Configuration Options ---
option(REDIS_ENABLE_TLS "Enable TLS support" ON)
option(REDIS_BUILD_TESTS "Build tests" OFF)
option(REDIS_USE_STATIC_RUNTIME "Use static C runtime" OFF)
set(OPENSSL_WIN64_ROOT "C:/OpenSSL-Win64" CACHE PATH "Path to OpenSSL-Win64 root directory")

# --- Compiler Flags ---
if(MSVC)
  add_definitions(-D_CRT_SECURE_NO_WARNINGS)
  if(REDIS_USE_STATIC_RUNTIME)
    foreach(flag_var
        CMAKE_C_FLAGS CMAKE_C_FLAGS_DEBUG CMAKE_C_FLAGS_RELEASE
        CMAKE_C_FLAGS_MINSIZEREL CMAKE_C_FLAGS_RELWITHDEBINFO)
      if(${flag_var} MATCHES "/MD")
        string(REGEX REPLACE "/MD" "/MT" ${flag_var} "${${flag_var}}")
      endif()
    endforeach()
  endif()
endif()

# --- Manually Specify OpenSSL ---
set(OPENSSL_INCLUDE_DIR "${OPENSSL_WIN64_ROOT}/include")
set(OPENSSL_LIBRARIES "${OPENSSL_WIN64_ROOT}/lib/libssl.lib" "${OPENSSL_WIN64_ROOT}/lib/libcrypto.lib")

# --- Include Directories ---
include_directories(
  ${CMAKE_CURRENT_SOURCE_DIR}/src
  ${CMAKE_CURRENT_SOURCE_DIR}/src/modules
  ${OPENSSL_INCLUDE_DIR}
)

set(LUA_INCLUDE_DIR "C:/path/to/lua/include" CACHE PATH "Path to lua")
set(LUA_LIBRARY "C:/path/to/lua/lua.lib" CACHE PATH "Path to lua")

include_directories(${LUA_INCLUDE_DIR})


# --- Sources ---
file(GLOB_RECURSE REDIS_SRC
  src/*.c
  src/modules/*.c
)

# Filter out tests or platform-specific files
list(FILTER REDIS_SRC EXCLUDE REGEX ".*test.*.c$")
list(FILTER REDIS_SRC EXCLUDE REGEX ".*posix.*.c$")

# Remove incompatible files on Windows
if(WIN32)
  list(FILTER REDIS_SRC EXCLUDE REGEX ".*ae_epoll\\.c$")
  list(FILTER REDIS_SRC EXCLUDE REGEX ".*ae_evport\\.c$")
  list(FILTER REDIS_SRC EXCLUDE REGEX ".*ae_kqueue\\.c$")
  list(FILTER REDIS_SRC EXCLUDE REGEX ".*ae_select\\.c$")
endif()

# --- Executables ---
add_executable(redis-server ${REDIS_SRC})

# --- Definitions ---
target_compile_definitions(redis-server PRIVATE
  _WIN32_WINNT=0x0601
  WIN32_LEAN_AND_MEAN
  NOMINMAX
  UNICODE
  _UNICODE
  _WIN64
  USE_OPENSSL
)

# --- Link Libraries ---
target_link_libraries(redis-server
  ${OPENSSL_LIBRARIES}
  ${LUA_LIBRARY}
  ws2_32
  advapi32
  userenv
  crypt32
  shlwapi
  bcrypt
)

# --- Output ---
set_target_properties(redis-server PROPERTIES
  OUTPUT_NAME "redis-server"
  RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/bin
)

# --- Install ---
install(TARGETS redis-server DESTINATION bin)

# --- Optional: redis-cli ---
# You can add a similar block for redis-cli if needed
# file(GLOB CLI_SRC src/redis-cli.c src/some_common_cli_code.c)
# add_executable(redis-cli ${CLI_SRC})