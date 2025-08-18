#!/bin/bash
# Activation script for Unix/Linux/macOS systems

echo "🚀 Activating Invoice Processing System Virtual Environment..."

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "❌ Virtual environment not found!"
    echo "📦 Please run: python setup_venv.py"
    exit 1
fi

# Activate virtual environment
source .venv/bin/activate

echo "✅ Virtual environment activated!"
echo "💡 You can now run: python main.py"
echo "🔄 To deactivate later, run: deactivate"