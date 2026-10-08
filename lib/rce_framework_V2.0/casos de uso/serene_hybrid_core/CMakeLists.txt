cmake_minimum_required(VERSION 3.16)
project(SereneHybridCore LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_AUTOMOC ON)
set(CMAKE_AUTORCC ON)
set(CMAKE_AUTOUIC ON)

find_package(Qt6 REQUIRED COMPONENTS Gui Qml Quick)

add_executable(SereneHybridCore
    src/engine/app.cpp
)

target_link_libraries(SereneHybridCore PRIVATE Qt6::Gui Qt6::Qml Qt6::Quick)
