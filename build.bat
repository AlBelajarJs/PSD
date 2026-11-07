@echo off
REM Bangun Jupyter Book (HTML) secara lokal ke _build\html
echo [1/2] Membersihkan artefak lama ...
if exist _build rmdir /s /q _build
echo [2/2] Menjalankan jupyter-book build ...
REM CATATAN: pakai CLI `jupyter-book` (dengan strip). `python -m jupyter_book`
REM GAGAL -- paket ini tidak punya __main__.py.
jupyter-book build .
if %errorlevel% neq 0 (
    echo BUILD GAGAL
    exit /b 1
)
echo.
echo BUILD OK -> _build\html\index.html
