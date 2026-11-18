@echo off
REM Opens all lab circuits in Logisim 2.7.1 using the installed Java
start "" javaw -jar "%~dp0tools\logisim.jar" "%~dp0DE_Lab_All_Circuits.circ"
