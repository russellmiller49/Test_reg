@echo off
REM Windows batch file to set up WSL environment
REM Run this from Windows Command Prompt or PowerShell

echo 🚀 Setting up Bronchoscopy Registry annotation environment in WSL...
echo.

REM Check if WSL is installed
wsl --list --quiet >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ WSL is not installed or not running.
    echo Please install WSL first: https://docs.microsoft.com/en-us/windows/wsl/install
    pause
    exit /b 1
)

echo ✅ WSL detected
echo.

REM Run the setup script in WSL
echo 📦 Running setup script in WSL...
wsl bash -c "curl -sSL https://raw.githubusercontent.com/russellmiller49/Test_reg/main/tools/setup_wsl.sh | bash"

if %errorlevel% equ 0 (
    echo.
    echo 🎉 Setup complete!
    echo.
    echo 💡 To start annotating:
    echo    1. Open WSL terminal
    echo    2. Run: cd Test_reg
    echo    3. Run: ./tools/start_annotation.sh
    echo    4. Open browser to: http://localhost:8501
) else (
    echo.
    echo ❌ Setup failed. Please check the error messages above.
)

echo.
pause
