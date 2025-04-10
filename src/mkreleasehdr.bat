@echo off
setlocal enabledelayedexpansion

rem Get Git SHA1 (first 8 characters)
for /f "delims=" %%a in ('git rev-parse --short=8 HEAD 2^>nul') do set GIT_SHA1=%%a
if not defined GIT_SHA1 set GIT_SHA1=00000000

rem Check for dirty state (count of diff lines)
for /f %%a in ('git diff --no-ext-diff -- src deps 2^>nul ^| find /v /c ""') do set GIT_DIRTY=%%a

rem Generate build ID: machine name + current timestamp
for /f %%a in ('hostname') do set HOSTNAME=%%a
for /f %%a in ('powershell -NoProfile -Command "[int][double]::Parse((Get-Date -UFormat %%s))"') do set TIMESTAMP=%%a
set BUILD_ID=%HOSTNAME%-%TIMESTAMP%

rem Use SOURCE_DATE_EPOCH if defined
if defined SOURCE_DATE_EPOCH (
    for /f %%a in ('powershell -NoProfile -Command "[int][double]::Parse((Get-Date -Date ([System.DateTimeOffset]::FromUnixTimeSeconds(%SOURCE_DATE_EPOCH%)).DateTime -UFormat %%s))"') do set BUILD_ID=%HOSTNAME%-%%a
)

rem Check if release.h exists
if not exist release.h type nul > release.h

rem Check if already up to date
findstr /C:"#define REDIS_GIT_SHA1 \"%GIT_SHA1%\"" release.h >nul
if %errorlevel%==0 (
    findstr /C:"#define REDIS_GIT_DIRTY \"%GIT_DIRTY%\"" release.h >nul
    if %errorlevel%==0 exit /b 0
)

rem Write new release.h
(
    echo #define REDIS_GIT_SHA1 "%GIT_SHA1%"
    echo #define REDIS_GIT_DIRTY "%GIT_DIRTY%"
    echo #define REDIS_BUILD_ID "%BUILD_ID%"
    echo #include "version.h"
    echo #define REDIS_BUILD_ID_RAW REDIS_VERSION REDIS_BUILD_ID REDIS_GIT_DIRTY REDIS_GIT_SHA1
) > release.h

rem Touch release.c to force recompilation
copy /b release.c +,, >nul 2>&1
