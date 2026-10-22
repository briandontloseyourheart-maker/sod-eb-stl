# 3D steady Mach 2 flight of a body with four brake plates at a chosen angle (STL).
# Reuses the CNS solver in ../src/solver and main()/EB setup from ../shock_wedge/src;
# the freestream setup and inflow boundary come from ../brian_20261020_0732/src.
cmake_minimum_required(VERSION 3.20)
project(brake_mach2 VERSION 1.0 LANGUAGES CXX)
if(NOT CMAKE_BUILD_TYPE AND NOT CMAKE_CONFIGURATION_TYPES)
  set(CMAKE_BUILD_TYPE Release CACHE STRING "Build type" FORCE)
endif()
set(AMREX_SOURCE_DIR "${CMAKE_CURRENT_SOURCE_DIR}/../../amrex" CACHE PATH "AMReX source checkout")
if(NOT AMReX_DIR AND NOT EXISTS "${AMREX_SOURCE_DIR}/CMakeLists.txt")
  message(FATAL_ERROR "Set AMREX_SOURCE_DIR to a compatible AMReX checkout")
endif()
set(AMReX_SPACEDIM 3 CACHE STRING "Spatial dimension" FORCE)
set(AMReX_EB ON CACHE BOOL "Embedded boundaries" FORCE)
set(AMReX_AMRLEVEL ON CACHE BOOL "AmrLevel driver" FORCE)
set(AMReX_FORTRAN OFF CACHE BOOL "C++ solver" FORCE)
set(AMReX_MPI OFF CACHE BOOL "MPI" )
set(AMReX_OMP ON CACHE BOOL "OpenMP")
set(AMReX_GPU_BACKEND NONE CACHE STRING "CPU backend" FORCE)
set(AMReX_PARTICLES OFF CACHE BOOL "No particles" FORCE)
set(AMReX_LINEAR_SOLVERS OFF CACHE BOOL "Explicit solver" FORCE)
if(AMReX_DIR)
  find_package(AMReX CONFIG REQUIRED COMPONENTS 3D EB AMRLEVEL)
else()
  add_subdirectory("${AMREX_SOURCE_DIR}" "${CMAKE_BINARY_DIR}/amrex")
endif()
set(SOLVER "${CMAKE_CURRENT_SOURCE_DIR}/../src/solver")
set(SHARED "${CMAKE_CURRENT_SOURCE_DIR}/../shock_wedge/src")
set(FREESTREAM "${CMAKE_CURRENT_SOURCE_DIR}/../brian_20261020_0732/src")
add_executable(brake_mach2
  ${FREESTREAM}/cns_prob.cpp ${FREESTREAM}/CNS_bcfill.cpp ${SHARED}/main.cpp ${SHARED}/CNS_init_eb2.cpp
  ${SOLVER}/CNS.cpp ${SOLVER}/CNSBld.cpp ${SOLVER}/CNS_advance.cpp
  ${SOLVER}/CNS_advance_box.cpp ${SOLVER}/CNS_advance_box_eb.cpp
  ${SOLVER}/CNS_derive.cpp ${SOLVER}/CNS_io.cpp
  ${SOLVER}/CNS_parm.cpp ${SOLVER}/CNS_setup.cpp)
# ${FREESTREAM} first so its freestream cns_prob*.H are used; ${SHARED} only supplies WedgeIF.H.
target_include_directories(brake_mach2 PRIVATE ${FREESTREAM} ${SHARED} ${SOLVER} ${SOLVER}/hydro ${SOLVER}/diffusion)
target_compile_features(brake_mach2 PRIVATE cxx_std_20)
target_link_libraries(brake_mach2 PRIVATE AMReX::amrex_3d)
set_target_properties(brake_mach2 PROPERTIES RUNTIME_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/bin")
