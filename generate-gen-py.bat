setlocal
if "%_PYTHON_DIR%" == "" (
    if exist c:\Python27 (
        set _PYTHON_DIR=c:\Python27
    ) else if exist c:\Python26 (
        set _PYTHON_DIR=c:\Python26
    ) else (
        echo Error: Python not found!
        goto :eof
    )
)
    
%_PYTHON_DIR%\Lib\site-packages\PyQt4\uic\pyuic.py gui.ui > gen.py
pause
