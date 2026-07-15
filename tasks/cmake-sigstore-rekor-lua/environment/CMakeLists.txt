cmake_minimum_required(VERSION 3.22)
project(release_verifier LANGUAGES NONE)

set(APP_ROOT "${CMAKE_SOURCE_DIR}" CACHE PATH "Application root")

include(${CMAKE_SOURCE_DIR}/cmake/StaticAnalysis.cmake)
include(${CMAKE_SOURCE_DIR}/cmake/VerifyRelease.cmake)

add_custom_target(static-analysis
  COMMAND ${CMAKE_COMMAND} -E env APP_ROOT=${APP_ROOT} ${Python3_EXECUTABLE} ${APP_ROOT}/tools/static_analysis_check.py
  WORKING_DIRECTORY ${APP_ROOT}
  COMMENT "Running static analysis on Lua verifier modules"
)

add_custom_target(verify-release
  COMMAND ${CMAKE_COMMAND} -E env APP_ROOT=${APP_ROOT} LUA_PATH="${CMAKE_SOURCE_DIR}/lua/?.lua;;" lua ${CMAKE_SOURCE_DIR}/lua/verify_release.lua
  WORKING_DIRECTORY ${APP_ROOT}
  COMMENT "Verifying release attestations against Rekor"
  DEPENDS static-analysis
)
