@echo off
REM Commit + push main, bangun Jupyter Book, lalu deploy HTML ke branch gh-pages.
setlocal enabledelayedexpansion

if "%~1"=="" (
    echo Cara pakai: push.bat "pesan commit"
    exit /b 1
)
set MSG=%~1

echo [1/5] Commit + push branch main ...
git add -A
git commit -m "%MSG%"
if %errorlevel% neq 0 (
    echo Tidak ada perubahan untuk di-commit, lanjut deploy.
)
git push origin main
if %errorlevel% neq 0 (
    echo PUSH MAIN GAGAL
    exit /b 1
)

echo [2/5] Build Jupyter Book ...
if exist _build rmdir /s /q _build
REM CATATAN: pakai CLI `jupyter-book` (dengan strip), bukan `python -m jupyter_book`
jupyter-book build .
if %errorlevel% neq 0 (
    echo BUILD GAGAL
    exit /b 1
)

echo [3/5] Menyiapkan folder deploy (gh-pages) ...
set DEPLOY=%TEMP%\psd_gh_pages
if exist %DEPLOY% rmdir /s /q %DEPLOY%
mkdir %DEPLOY%
xcopy _build\html %DEPLOY% /E /I /Q /Y >nul
echo > %DEPLOY%\.nojekyll

echo [4/5] Push ke branch gh-pages ...
cd %DEPLOY%
git init -q
git checkout -q -b gh-pages
git add -A
git -c user.name="deploy-bot" -c user.email="deploy@local" commit -q -m "deploy: %DATE% %TIME%"
git push -f https://github.com/safamaster223/PSD.git gh-pages
if %errorlevel% neq 0 (
    echo PUSH GH-PAGES GAGAL
    cd %~dp0
    exit /b 1
)
cd %~dp0

echo [5/5] SELESAI. Situs: https://safamaster223.github.io/PSD/
endlocal
