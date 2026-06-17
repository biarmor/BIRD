# Python Version Compatibility Fix

## Problem
You're using Python 3.14, which is newer than what pydantic-core supports (max 3.12).

## Solution Options

### Option 1: Use Python 3.12 or 3.11 (Recommended)
```bash
# Check your Python versions
python3 --version
python3.12 --version
python3.11 --version

# Use Python 3.12 or 3.11 instead
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Option 2: Downgrade Python 3.14 to 3.12
```bash
# On macOS (using Homebrew)
brew install python@3.12
python3.12 -m venv venv

# On Ubuntu/Debian
sudo apt install python3.12 python3.12-venv
python3.12 -m venv venv

# On Windows
# Download Python 3.12 from python.org
```

### Option 3: Use Python 3.14 with Compatibility Flag
```bash
# Create venv with Python 3.14
python3 -m venv venv
source venv/bin/activate

# Set compatibility flag
export PYO3_USE_ABI3_FORWARD_COMPATIBILITY=1

# Install
pip install -r requirements.txt
```

## Recommended: Use Python 3.11 or 3.12

Python 3.11 and 3.12 are the most stable and have the best package support.

```bash
# Check available versions
python3.12 --version
python3.11 --version

# Create venv with Python 3.12
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## After Installation
```bash
# Verify
python3 -c "import fastapi; print('✅ Success')"

# Run BIRD
python3 -m uvicorn app.main:app --reload
```
