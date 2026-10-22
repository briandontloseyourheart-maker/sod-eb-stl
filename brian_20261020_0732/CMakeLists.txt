# 2D Mach 3 flow around a circular cylinder in a channel, cylinder from STL.
# Reuses the CNS solver in ../src/solver and main()/EB setup from ../shock_wedge/src;
# only the freestream problem setup and inflow boundary live in src/ here.
cmake_minimum_required(VERSION 3.20)
project(cylinder_mach3 VERSION 1.0 LANGUAGES CXX)
if(NOT CMAKE_BUILD_TYPE AND NOT CMAKE_CONFIGURATION_TYPES)
  set(CMAKE_BUILD_TYPE Release CACHE STRING "Build type" FORCE)
endif()
set(AMREX_SOURCE_DIR "${CMAKE_CURRENT_SOURCE_DIR}/../../amrex" CACHE PATH "AMReX source checkout")
if(NOT AMReX_DIR AND NOT EXISTS "${AMREX_SOURCE_DIR}/CMakeLists.txt")
  message(FATAL_ERROR "Set AMREX_SOURCE_DIR to a compatible AMReX checkout")
endif()
set(AMReX_SPACEDIM 2 CACHE STRING "Spatial dimension" FORCE)
set(AMReX_EB ON CACHE BOOL "Embedded boundaries" FORCE)
set(AMReX_AMRLEVEL ON CACHE BOOL "AmrLevel driver" FORCE)
set(AMReX_FORTRAN OFF CACHE BOOL "C++ solver" FORCE)
set(AMReX_MPI OFF CACHE BOOL "MPI" )
set(AMReX_OMP ON CACHE BOOL "OpenMP")
set(AMReX_GPU_BACKEND NONE CACHE STRING "CPU backend" FORCE)
set(AMReX_PARTICLES OFF CACHE BOOL "No particles" FORCE)
set(AMReX_LINEAR_SOLVERS OFF CACHE BOOL "Explicit solver" FORCE)
if(AMReX_DIR)
  find_package(AMReX CONFIG REQUIRED COMPONENTS 2D EB AMRLEVEL)
else()
  add_subdirectory("${AMREX_SOURCE_DIR}" "${CMAKE_BINARY_DIR}/amrex")
endif()
set(SOLVER "${CMAKE_CURRENT_SOURCE_DIR}/../src/solver")
set(SHARED "${CMAKE_CURRENT_SOURCE_DIR}/../shock_wedge/src")
add_executable(cylinder_mach3
  src/cns_prob.cpp src/CNS_bcfill.cpp ${SHARED}/main.cpp ${SHARED}/CNS_init_eb2.cpp
  ${SOLVER}/CNS.cpp ${SOLVER}/CNSBld.cpp ${SOLVER}/CNS_advance.cpp
  ${SOLVER}/CNS_advance_box.cpp ${SOLVER}/CNS_advance_box_eb.cpp
  ${SOLVER}/CNS_derive.cpp ${SOLVER}/CNS_io.cpp
  ${SOLVER}/CNS_parm.cpp ${SOLVER}/CNS_setup.cpp)
# src/ first so cns_prob*.H here are used; ${SHARED} only supplies WedgeIF.H.
target_include_directories(cylinder_mach3 PRIVATE src ${SHARED} ${SOLVER} ${SOLVER}/hydro ${SOLVER}/diffusion)
target_compile_features(cylinder_mach3 PRIVATE cxx_std_20)
target_link_libraries(cylinder_mach3 PRIVATE AMReX::amrex_2d)
set_target_properties(cylinder_mach3 PROPERTIES RUNTIME_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/bin")
