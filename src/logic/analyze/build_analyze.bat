@echo off
set OPENCV_ROOT=D:\ProjectsGit\app-wave-front-metric\lib\opencv\OpenCV-MinGW-Build
set CNPY_ROOT=D:\ProjectsGit\app-wave-front-metric\lib\cnpy
set SQLITE3_ROOT=D:\ProjectsGit\app-wave-front-metric\lib\sqlite3
set JSON_ROOT=D:\ProjectsGit\app-wave-front-metric\lib\json

echo Compiling analyze.cpp...
g++ -static -std=c++17 -c analyze.cpp -o analyze.o ^
    -I"%OPENCV_ROOT%\include" -I"%CNPY_ROOT%" -I"%SQLITE3_ROOT%" -I"%JSON_ROOT%"

echo Compiling cnpy.cpp...
g++ -std=c++17 -c "%CNPY_ROOT%\cnpy.cpp" -o cnpy.o -I"%CNPY_ROOT%"

echo Compiling sqlite3.c...
gcc -c "%SQLITE3_ROOT%\sqlite3.c" -o sqlite3.o

echo Linking...
g++ -o analyze.exe analyze.o cnpy.o sqlite3.o ^
    -L"%OPENCV_ROOT%\x64\mingw\lib" ^
    -lopencv_core455 -lopencv_imgproc455 -lopencv_imgcodecs455 -lz

echo Build complete.