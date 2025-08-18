# 🚀 Complete Setup Guide - Invoice Processing System

This comprehensive guide will help you set up the Invoice Processing System with proper virtual environment management and best practices.

## 📋 Prerequisites

### System Requirements
- **Python**: 3.8 or higher
- **Operating System**: Windows, macOS, or Linux
- **Memory**: Minimum 4GB RAM (8GB recommended)
- **Storage**: At least 1GB free space
- **API Keys**: OpenAI API key (required), Anthropic API key (optional)

### Check Python Installation
```bash
python --version
# or
python3 --version
```

If Python is not installed, download it from [python.org](https://www.python.org/downloads/).

## 🔧 Quick Setup (Recommended)

### 1. Clone or Download the Project
```bash
# If using git
git clone <repository-url>
cd invoice_processing_system

# Or download and extract the ZIP file
```

### 2. Automated Setup
```bash
# Run the automated setup script
python setup_venv.py
```

This script will:
- ✅ Check Python version compatibility
- ✅ Create a virtual environment in `.venv/`
- ✅ Upgrade pip to the latest version
- ✅ Install all required dependencies
- ✅ Provide activation instructions

### 3. Configure API Keys
```bash
# Copy the example environment file
cp .env.example .env

# Edit the .env file and add your API keys:
# OPENAI_API_KEY="your_openai_key_here"
# ANTHROPIC_API_KEY="your_anthropic_key_here"
```

**Getting API Keys:**
- **OpenAI**: Visit [https://platform.openai.com/api-keys](https://platform.openai.com/api-keys)
- **Anthropic**: Visit [https://console.anthropic.com/settings/keys](https://console.anthropic.com/settings/keys)

### 4. Activate Virtual Environment

**Windows:**
```cmd
.venv\Scripts\activate
```

**macOS/Linux:**
```bash
source .venv/bin/activate
```

**Or use convenience scripts:**
```bash
# Windows
activate_venv.bat

# macOS/Linux
./activate_venv.sh
```

### 5. Launch the Application
```bash
python main.py
```

## 🛠️ Manual Setup (Alternative)

If you prefer manual setup or the automated script doesn't work:

### 1. Create Virtual Environment
```bash
python -m venv .venv
```

### 2. Activate Virtual Environment
**Windows:**
```cmd
.venv\Scripts\activate
```

**macOS/Linux:**
```bash
source .venv/bin/activate
```

### 3. Upgrade pip
```bash
python -m pip install --upgrade pip
```

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

### 5. Verify Installation
```bash
python main.py
```

## 🧪 Development Setup

For developers who want to contribute or modify the system:

### 1. Install Development Dependencies
```bash
pip install -r requirements-dev.txt
```

### 2. Install Pre-commit Hooks (Optional)
```bash
pre-commit install
```

### 3. Run Tests
```bash
python -m pytest tests/ -v
```

## 🔍 Troubleshooting

### Common Issues and Solutions

#### Issue: "Python not found"
**Solution:**
- Ensure Python is installed and added to PATH
- Try using `python3` instead of `python`
- On Windows, try `py` command

#### Issue: "Permission denied" on Linux/macOS
**Solution:**
```bash
chmod +x activate_venv.sh
./activate_venv.sh
```

#### Issue: Virtual environment not activating
**Solution:**
- Check if you're in the correct directory
- Ensure the `.venv` folder exists
- Try recreating the virtual environment:
  ```bash
  rm -rf .venv  # or rmdir /s .venv on Windows
  python setup_venv.py
  ```

#### Issue: Package installation fails
**Solution:**
- Ensure you're in the virtual environment
- Update pip: `python -m pip install --upgrade pip`
- Try installing packages individually:
  ```bash
  pip install streamlit pandas numpy plotly
  ```

#### Issue: Streamlit not launching
**Solution:**
- Check if port 8501 is available
- Try a different port:
  ```bash
  streamlit run ui/streamlit_app.py --server.port 8502
  ```

### Getting Help

If you encounter issues not covered here:

1. **Check the logs**: Look in the `logs/` directory for error messages
2. **Verify dependencies**: Run `pip list` to see installed packages
3. **Check Python version**: Ensure you're using Python 3.8+
4. **Virtual environment**: Confirm you're in the virtual environment

## 📊 Verification Checklist

After setup, verify everything is working:

- [ ] Virtual environment is activated
- [ ] All dependencies are installed (`pip list`)
- [ ] Main application launches (`python main.py`)
- [ ] Dashboard opens in browser
- [ ] Sample data is available
- [ ] No error messages in logs

## 🔄 Environment Management

### Daily Usage
```bash
# Activate environment
source .venv/bin/activate  # macOS/Linux
.venv\Scripts\activate     # Windows

# Run application
python main.py

# Deactivate when done
deactivate
```

### Updating Dependencies
```bash
# Update a specific package
pip install --upgrade package_name

# Update all packages (use with caution)
pip list --outdated --format=freeze | grep -v '^\-e' | cut -d = -f 1 | xargs -n1 pip install -U

# Save updated requirements
pip freeze > requirements.txt
```

### Cleaning Up
```bash
# Remove virtual environment
rm -rf .venv  # macOS/Linux
rmdir /s .venv  # Windows

# Clean temporary files
make clean  # if using Makefile
```

## 🎯 Next Steps

Once setup is complete:

1. **Explore the Dashboard**: Launch the application and explore all features
2. **Upload Documents**: Try uploading sample documents
3. **Chat with Agents**: Use the conversation feature
4. **Review Anomalies**: Check the anomaly detection capabilities
5. **Customize Settings**: Adjust agent configurations as needed

## 💡 Best Practices

- **Always use virtual environments** for Python projects
- **Keep requirements.txt updated** when adding new dependencies
- **Regularly update packages** for security and performance
- **Use version control** to track changes
- **Document any custom modifications** you make

---

🎉 **Congratulations!** Your Invoice Processing System is now ready to use with proper virtual environment management!