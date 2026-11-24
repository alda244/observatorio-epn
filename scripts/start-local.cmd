@echo off
setlocal
pushd "%~dp0.." || exit /b 1
docker compose up -d --build
set "result=%errorlevel%"
popd
exit /b %result%
