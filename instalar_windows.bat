@echo off
REM Instala um motor de voz no Windows e gera um pedido.
REM Uso:  instalar_windows.bat MOTOR            (instala)
REM       instalar_windows.bat MOTOR PEDIDO     (instala e ja gera; ex.: kokoro pedidos\docinhos.json)
REM MOTOR: chatterbox | chatterbox-ptbr | kokoro | piper | edge
REM Precisa do Python 3.11 (python.org) e do ffmpeg no PATH. Kokoro e Piper precisam do espeak-ng (.msi em github.com/espeak-ng/espeak-ng/releases).
setlocal
set MOTOR=%1
if "%MOTOR%"=="" set MOTOR=kokoro
cd /d "%~dp0"
if not exist venv\Scripts\python.exe (
  py -3.11 -m venv venv || python -m venv venv
)
set PY=venv\Scripts\python.exe
%PY% -m pip install -q --upgrade pip
%PY% -m pip install -q --retries 10 --timeout 60 -r requisitos\base.txt
if /I "%MOTOR%"=="chatterbox" goto cb
if /I "%MOTOR%"=="chatterbox-ptbr" goto cb
%PY% -m pip install -q --retries 10 --timeout 60 -r requisitos\%MOTOR%.txt
goto fim
:cb
where nvidia-smi >nul 2>nul && (%PY% -m pip install -q torch torchaudio --index-url https://download.pytorch.org/whl/cu124) || (%PY% -m pip install -q torch torchaudio --index-url https://download.pytorch.org/whl/cpu)
%PY% -m pip install -q -r requisitos\chatterbox.txt
:fim
echo Instalado: %MOTOR%
if not "%2"=="" %PY% voz.py %2 --motor %MOTOR% --zip
endlocal
