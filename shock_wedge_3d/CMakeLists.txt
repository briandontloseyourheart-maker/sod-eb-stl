# 3D Mach 1.3 shock diffracting over a finite-span triangular wedge read from STL.
# Reuses the CNS solver in ../src/solver and the shock setup in ../shock_wedge/src
# (Rankine-Hugoniot initial state, post-shock inflow boundary); both are
# dimension independent.
cmake_minimum_required(VERSION 3.20)
project(shock_wedge_3d VERSION 1.0 LANGUAGES CXX)
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
set(PROB "${CMAKE_CURRENT_SOURCE_DIR}/../shock_wedge/src")
add_executable(shock_wedge_3d
  ${PROB}/main.cpp ${PROB}/cns_prob.cpp ${PROB}/CNS_bcfill.cpp ${PROB}/CNS_init_eb2.cpp
  ${SOLVER}/CNS.cpp ${SOLVER}/CNSBld.cpp ${SOLVER}/CNS_advance.cpp
  ${SOLVER}/CNS_advance_box.cpp ${SOLVER}/CNS_advance_box_eb.cpp
  ${SOLVER}/CNS_derive.cpp ${SOLVER}/CNS_io.cpp
  ${SOLVER}/CNS_parm.cpp ${SOLVER}/CNS_setup.cpp)
# ${PROB} first so its cns_prob*.H replace the Sod versions in ../src/problem.
target_include_directories(shock_wedge_3d PRIVATE ${PROB} ${SOLVER} ${SOLVER}/hydro ${SOLVER}/diffusion)
target_compile_features(shock_wedge_3d PRIVATE cxx_std_20)
target_link_libraries(shock_wedge_3d PRIVATE AMReX::amrex_3d)
set_target_properties(shock_wedge_3d PROPERTIES RUNTIME_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/bin")
