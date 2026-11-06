@echo off
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\gameplay-docker.ps1" up
if errorlevel 1 pause
