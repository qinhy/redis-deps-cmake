cmake_minimum_required(VERSION 3.10)

# Set the project name and version
project(fpconv VERSION 1.0)

# Specify the C++ standard
set(CMAKE_C_STANDARD 99)
set(CMAKE_C_STANDARD_REQUIRED True)

# Set compile options
add_compile_options(-Wall -Os -g)

# Add an executable
add_library(fpconv STATIC fpconv_dtoa.c)

# Include directories
target_include_directories(fpconv PUBLIC "${PROJECT_BINARY_DIR}")

# Set the output name of the library
set_target_properties(fpconv PROPERTIES OUTPUT_NAME "fpconv")

# Add a clean target
# add_custom_target(clean
#     COMMAND ${CMAKE_COMMAND} -E remove -f ${PROJECT_BINARY_DIR}/*.o
#     COMMAND ${CMAKE_COMMAND} -E remove -f ${PROJECT_BINARY_DIR}/*.a
# )
