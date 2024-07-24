# Set the minimum version of CMake required
cmake_minimum_required(VERSION 3.10)

# Define the project name
project(LinenoiseExample)

add_definitions(-DASIO_STANDALONE)

# Set the standard compiler flags and optimizations
add_compile_options(-Wall -Os -g)

# Create a library target for linenoise
add_library(linenoise STATIC linenoise.h linenoise.c)

# Create an executable target for the linenoise_example
add_executable(linenoise_example example.c)
target_link_libraries(linenoise_example PRIVATE linenoise)

# Add a 'clean' custom target if you like the make clean functionality
# add_custom_target(clean
#     COMMAND ${CMAKE_COMMAND} -P ${CMAKE_BINARY_DIR}/cmake_clean.cmake
# )
