cmake_minimum_required(VERSION 3.10)
project(scout_piper_nav)

find_package(ament_cmake REQUIRED)

install(DIRECTORY config launch scripts
  DESTINATION share/${PROJECT_NAME}
)

ament_package()
