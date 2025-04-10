cmake_minimum_required(VERSION 3.16)

project(hiredis LANGUAGES C VERSION 0.0.0)  # Version is updated later

# Options
option(BUILD_SHARED_LIBS "Build shared libraries" ON)
option(ENABLE_SSL "Build hiredis_ssl for SSL support" OFF)
option(DISABLE_TESTS "If tests should be compiled or not" OFF)
option(ENABLE_SSL_TESTS "Should we test SSL connections" OFF)
option(ENABLE_EXAMPLES "Enable building hiredis examples" OFF)
option(ENABLE_ASYNC_TESTS "Should we run all asynchronous API tests" OFF)

# Extract version from header
macro(getVersionBit name)
  set(VERSION_REGEX "^#define ${name} (.+)$")
  file(STRINGS "${CMAKE_CURRENT_SOURCE_DIR}/hiredis.h" VERSION_BIT REGEX ${VERSION_REGEX})
  string(REGEX REPLACE ${VERSION_REGEX} "\\1" ${name} "${VERSION_BIT}")
endmacro()

getVersionBit(HIREDIS_MAJOR)
getVersionBit(HIREDIS_MINOR)
getVersionBit(HIREDIS_PATCH)
getVersionBit(HIREDIS_SONAME)
set(VERSION "${HIREDIS_MAJOR}.${HIREDIS_MINOR}.${HIREDIS_PATCH}")
message(STATUS "Detected hiredis version: ${VERSION}")
set_property(GLOBAL PROPERTY USE_FOLDERS ON)
project(hiredis VERSION ${VERSION} LANGUAGES C)

include(GNUInstallDirs)

# Set C standard
set(CMAKE_C_STANDARD 99)
set(CMAKE_DEBUG_POSTFIX d)

# Sources
set(hiredis_sources
    alloc.c async.c hiredis.c net.c read.c sds.c sockcompat.c
)

if(WIN32)
    add_definitions(-D_CRT_SECURE_NO_WARNINGS -DWIN32_LEAN_AND_MEAN)
endif()

# Library target
add_library(hiredis ${hiredis_sources})
add_library(hiredis::hiredis ALIAS hiredis)
set(hiredis_export_name hiredis CACHE STRING "Exported target name")
set_target_properties(hiredis PROPERTIES
    EXPORT_NAME ${hiredis_export_name}
    WINDOWS_EXPORT_ALL_SYMBOLS TRUE
    VERSION ${HIREDIS_SONAME}
)

if(MSVC)
    target_compile_options(hiredis PRIVATE /Z7)
endif()

# Platform-specific linking
if(WIN32)
    target_link_libraries(hiredis PUBLIC ws2_32 crypt32)
elseif(CMAKE_SYSTEM_NAME MATCHES "FreeBSD")
    target_link_libraries(hiredis PUBLIC m)
elseif(CMAKE_SYSTEM_NAME MATCHES "SunOS")
    target_link_libraries(hiredis PUBLIC socket)
endif()

target_include_directories(hiredis PUBLIC
    $<INSTALL_INTERFACE:include>
    $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}>
)

# ======================
# SSL Support
# ======================
if(ENABLE_SSL)
    # Show these in the GUI
    set(OPENSSL_INCLUDE_DIR "" CACHE PATH "Path to the OpenSSL include directory")
    set(OPENSSL_SSL_LIBRARY "" CACHE FILEPATH "Path to the OpenSSL SSL static library (.lib)")
    set(OPENSSL_CRYPTO_LIBRARY "" CACHE FILEPATH "Path to the OpenSSL Crypto static library (.lib)")

    # Allow fallback to environment vars (optional)
    if(WIN32)
        foreach(var IN ITEMS OPENSSL_INCLUDE_DIR OPENSSL_SSL_LIBRARY OPENSSL_CRYPTO_LIBRARY)
            if(NOT DEFINED ${var} AND DEFINED ENV{${var}})
                set(${var} $ENV{${var}})
            endif()
        endforeach()
    endif()

    # Validate inputs
    if(NOT OPENSSL_INCLUDE_DIR OR NOT OPENSSL_SSL_LIBRARY OR NOT OPENSSL_CRYPTO_LIBRARY)
        message(FATAL_ERROR "You must set OPENSSL_INCLUDE_DIR, OPENSSL_SSL_LIBRARY, and OPENSSL_CRYPTO_LIBRARY.")
    endif()

    # Create imported targets manually
    add_library(OpenSSL::SSL STATIC IMPORTED GLOBAL)
    set_target_properties(OpenSSL::SSL PROPERTIES
        IMPORTED_LOCATION "${OPENSSL_SSL_LIBRARY}"
        INTERFACE_INCLUDE_DIRECTORIES "${OPENSSL_INCLUDE_DIR}"
    )

    add_library(OpenSSL::Crypto STATIC IMPORTED GLOBAL)
    set_target_properties(OpenSSL::Crypto PROPERTIES
        IMPORTED_LOCATION "${OPENSSL_CRYPTO_LIBRARY}"
        INTERFACE_INCLUDE_DIRECTORIES "${OPENSSL_INCLUDE_DIR}"
    )

    # Sources
    set(hiredis_ssl_sources ssl.c)

    # Define library
    add_library(hiredis_ssl ${hiredis_ssl_sources})
    add_library(hiredis::hiredis_ssl ALIAS hiredis_ssl)

    set_target_properties(hiredis_ssl PROPERTIES
        WINDOWS_EXPORT_ALL_SYMBOLS TRUE
        VERSION "${HIREDIS_SONAME}"
    )

    target_include_directories(hiredis_ssl PUBLIC
        $<INSTALL_INTERFACE:include/hiredis>
        $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}>
    )

    target_link_libraries(hiredis_ssl PRIVATE
        hiredis
        OpenSSL::SSL
        OpenSSL::Crypto
    )

    if(MSVC)
        target_compile_options(hiredis_ssl PRIVATE /Z7)
    endif()

    # .pc file for pkg-config
    configure_file(hiredis_ssl.pc.in hiredis_ssl.pc @ONLY)
endif()

# ======================
# Installation
# ======================
install(TARGETS hiredis
    EXPORT hiredis-targets
    RUNTIME DESTINATION ${CMAKE_INSTALL_BINDIR}
    LIBRARY DESTINATION ${CMAKE_INSTALL_LIBDIR}
    ARCHIVE DESTINATION ${CMAKE_INSTALL_LIBDIR}
)

if(MSVC AND BUILD_SHARED_LIBS)
    install(FILES $<TARGET_PDB_FILE:hiredis>
        DESTINATION ${CMAKE_INSTALL_BINDIR}
        CONFIGURATIONS Debug RelWithDebInfo)
endif()

install(FILES hiredis.h read.h sds.h async.h alloc.h sockcompat.h
    DESTINATION ${CMAKE_INSTALL_INCLUDEDIR}/hiredis)
install(DIRECTORY adapters DESTINATION ${CMAKE_INSTALL_INCLUDEDIR}/hiredis)
configure_file(hiredis.pc.in hiredis.pc @ONLY)
install(FILES ${CMAKE_CURRENT_BINARY_DIR}/hiredis.pc DESTINATION ${CMAKE_INSTALL_LIBDIR}/pkgconfig)

if(ENABLE_SSL)
    install(TARGETS hiredis_ssl
        EXPORT hiredis_ssl-targets
        RUNTIME DESTINATION ${CMAKE_INSTALL_BINDIR}
        LIBRARY DESTINATION ${CMAKE_INSTALL_LIBDIR}
        ARCHIVE DESTINATION ${CMAKE_INSTALL_LIBDIR}
    )

    if(MSVC AND BUILD_SHARED_LIBS)
        install(FILES $<TARGET_PDB_FILE:hiredis_ssl>
            DESTINATION ${CMAKE_INSTALL_BINDIR}
            CONFIGURATIONS Debug RelWithDebInfo)
    endif()

    install(FILES hiredis_ssl.h DESTINATION ${CMAKE_INSTALL_INCLUDEDIR}/hiredis)
    install(FILES ${CMAKE_CURRENT_BINARY_DIR}/hiredis_ssl.pc DESTINATION ${CMAKE_INSTALL_LIBDIR}/pkgconfig)
endif()

# ======================
# CMake Config Package
# ======================
if(WIN32)
    set(CMAKE_CONF_INSTALL_DIR share/hiredis)
else()
    set(CMAKE_CONF_INSTALL_DIR ${CMAKE_INSTALL_LIBDIR}/cmake/hiredis)
endif()

set(INCLUDE_INSTALL_DIR include)
include(CMakePackageConfigHelpers)

write_basic_package_version_file(
    "${CMAKE_CURRENT_BINARY_DIR}/hiredis-config-version.cmake"
    COMPATIBILITY SameMajorVersion
)

configure_package_config_file(hiredis-config.cmake.in
    ${CMAKE_CURRENT_BINARY_DIR}/hiredis-config.cmake
    INSTALL_DESTINATION ${CMAKE_CONF_INSTALL_DIR}
    PATH_VARS INCLUDE_INSTALL_DIR
)

install(EXPORT hiredis-targets
    FILE hiredis-targets.cmake
    NAMESPACE hiredis::
    DESTINATION ${CMAKE_CONF_INSTALL_DIR}
)

install(FILES
    ${CMAKE_CURRENT_BINARY_DIR}/hiredis-config.cmake
    ${CMAKE_CURRENT_BINARY_DIR}/hiredis-config-version.cmake
    DESTINATION ${CMAKE_CONF_INSTALL_DIR}
)

# SSL Config export
if(ENABLE_SSL)
    if(WIN32)
        set(CMAKE_CONF_INSTALL_DIR share/hiredis_ssl)
    else()
        set(CMAKE_CONF_INSTALL_DIR ${CMAKE_INSTALL_LIBDIR}/cmake/hiredis_ssl)
    endif()

    configure_package_config_file(hiredis_ssl-config.cmake.in
        ${CMAKE_CURRENT_BINARY_DIR}/hiredis_ssl-config.cmake
        INSTALL_DESTINATION ${CMAKE_CONF_INSTALL_DIR}
        PATH_VARS INCLUDE_INSTALL_DIR
    )

    install(EXPORT hiredis_ssl-targets
        FILE hiredis_ssl-targets.cmake
        NAMESPACE hiredis::
        DESTINATION ${CMAKE_CONF_INSTALL_DIR}
    )

    install(FILES
        ${CMAKE_CURRENT_BINARY_DIR}/hiredis_ssl-config.cmake
        DESTINATION ${CMAKE_CONF_INSTALL_DIR}
    )
endif()

# ======================
# Tests
# ======================
if(NOT DISABLE_TESTS)
    enable_testing()
    add_executable(hiredis-test test.c)
    target_link_libraries(hiredis-test hiredis)

    if(ENABLE_SSL_TESTS)
        target_compile_definitions(hiredis-test PRIVATE -DHIREDIS_TEST_SSL=1)
        target_link_libraries(hiredis-test hiredis_ssl)
    endif()

    if(ENABLE_ASYNC_TESTS)
        target_compile_definitions(hiredis-test PRIVATE -DHIREDIS_TEST_ASYNC=1)
        target_link_libraries(hiredis-test event)
    endif()

    add_test(NAME hiredis-test COMMAND ${CMAKE_CURRENT_SOURCE_DIR}/test.sh)
endif()

# ======================
# Examples
# ======================
if(ENABLE_EXAMPLES)
    add_subdirectory(examples)
endif()
