cmake_minimum_required(VERSION 4.0)

# Project name and language
project(HdrHistogram C)

# Set C standard
set(CMAKE_C_STANDARD 99)

# Compiler flags
add_compile_options(-Wall)    # Add warning flags
add_compile_options(-Os)      # Optimization flag
add_definitions(-DHDR_MALLOC_INCLUDE="hdr_redis_malloc.h")

# Debug and release flags
set(CMAKE_C_FLAGS_DEBUG "-g") # Debug flag

# Include directories
include_directories(${CMAKE_SOURCE_DIR})

# Create a static library
add_library(hdrhistogram STATIC hdr_histogram.c)

# Target specific properties
set_target_properties(hdrhistogram PROPERTIES OUTPUT_NAME "hdrhistogram")

# Clean custom target (if needed)
# add_custom_target(clean
#     COMMAND ${CMAKE_COMMAND} -E remove -f ${CMAKE_BINARY_DIR}/*.o ${CMAKE_BINARY_DIR}/*.a
# )
