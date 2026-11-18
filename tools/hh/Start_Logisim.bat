@echo off
REM Starts Logisim 2.7.1 using the installed Java (fixes "Java Runtime Environment required")
start "" javaw -jar "%~dp0tools\logisim.jar" %*
