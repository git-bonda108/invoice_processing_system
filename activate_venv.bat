@echo off
REM Activation script for Windows systems

echo 🚀 Activating Invoice Processing System Virtual Environment...

REM Check if virtual environment exists
if not exist ".venv" (
    echo ❌ Virtual environment not found!
    echo 📦 Please run: python setup_venv.py
    pause
    exit /b 1
)

REM Activate virtual environment
call .venv\Scripts\activate.bat

echo ✅ Virtual environment activated!
echo 💡 You can now run: python main.py
echo 🔄 To deactivate later, run: deactivate