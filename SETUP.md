# TexQL Setup Guide

Quick setup guide for running TexQL on your local machine.

## Prerequisites

- Python 3.8 or higher
- 4GB RAM minimum (8GB recommended)
- Internet connection (for downloading dependencies)

## Step-by-Step Setup

### 1. Create Virtual Environment

```bash
# Navigate to project directory
cd TexQL

# Create virtual environment
python -m venv venv
```

### 2. Activate Virtual Environment

**Windows (PowerShell):**
```powershell
.\venv\Scripts\Activate.ps1
```

**Windows (Command Prompt):**
```cmd
.\venv\Scripts\activate.bat
```

**Linux/Mac:**
```bash
source venv/bin/activate
```

You should see `(venv)` prefix in your terminal.

### 3. Install Dependencies

**For running the app only (recommended):**
```bash
pip install -r requirements-app.txt
```

**For full development (including training tools):**
```bash
pip install -r requirements.txt
```

### 4. Verify Installation

```bash
# Check installed packages
pip list

# Should see:
# - torch
# - transformers
# - streamlit
# - pandas
# - faker
```

## Usage

### Generate Training Data

```bash
python data_generation.py
```

- Generates 12,000 balanced samples
- Output in `data/` directory
- Takes ~2-3 minutes

### Test the Model

```bash
python demo.py
```

- Tests 9 sample queries
- Shows both SQL and MongoDB outputs
- Verifies model is working

### Run Web Application

```bash
streamlit run app.py
```

- Opens browser at `http://localhost:8501`
- Interactive UI with parameter controls
- Query history and export

### Command-Line Inference

```bash
# Single query
python inference.py --query "Show all employees"

# Both SQL and MongoDB
python inference.py --query "Show all employees" --type both

# From file
python inference.py --file queries.txt --output results.json
```

## Training (Google Colab)

1. Generate data locally: `python data_generation.py`
2. Upload `training_colab_balanced.ipynb` to Google Colab
3. Upload data files to Google Drive
4. Run all cells in Colab notebook
5. Download trained model
6. Extract to `models/` directory

## Deactivating Virtual Environment

When you're done:

```bash
deactivate
```

## Troubleshooting

### Virtual Environment Not Activating

**Windows PowerShell ExecutionPolicy Error:**
```powershell
# Run PowerShell as Administrator
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**Alternative:**
```powershell
# Use Command Prompt instead
.\venv\Scripts\activate.bat
```

### Module Not Found Errors

```bash
# Make sure venv is activated
.\venv\Scripts\Activate.ps1

# Reinstall requirements
pip install -r requirements-app.txt
```

### Streamlit Not Running

```bash
# Check if streamlit is installed
pip show streamlit

# If not, install it
pip install streamlit

# Clear cache and retry
streamlit cache clear
streamlit run app.py
```

### Model Not Found

```bash
# Check if model directory exists
ls models/

# Should contain:
# - config.json
# - model.safetensors
# - tokenizer files

# If missing, train model on Colab first
```

### CUDA/GPU Issues

The app runs on CPU by default. GPU is not required for inference.

If you see CUDA errors but want to use CPU only:
```python
# The app automatically handles this, but you can force CPU:
import os
os.environ['CUDA_VISIBLE_DEVICES'] = ''
```

## File Structure After Setup

```
TexQL/
├── venv/                      # Virtual environment (not in git)
├── data/                      # Generated training data
│   ├── training_data.csv
│   ├── train.csv
│   └── val.csv
├── models/                    # Trained models (not in git)
│   ├── config.json
│   └── model.safetensors
├── app.py                     # Main application
├── demo.py                    # Test script
├── inference.py               # CLI tool
├── data_generation.py         # Data generator
└── requirements-app.txt       # Dependencies
```

## Next Steps

1. ✅ Setup complete - venv created and activated
2. ✅ Dependencies installed
3. 📊 Generate training data: `python data_generation.py`
4. 🚀 Test the app: `python demo.py`
5. 🌐 Run web interface: `streamlit run app.py`
6. 🎓 Train on Colab (optional): Upload `training_colab_balanced.ipynb`

## Quick Reference

| Command | Purpose |
|---------|---------|
| `python -m venv venv` | Create virtual environment |
| `.\venv\Scripts\Activate.ps1` | Activate (Windows) |
| `source venv/bin/activate` | Activate (Linux/Mac) |
| `pip install -r requirements-app.txt` | Install dependencies |
| `python data_generation.py` | Generate training data |
| `python demo.py` | Test model |
| `streamlit run app.py` | Run web app |
| `python inference.py --query "..."` | CLI inference |
| `deactivate` | Exit virtual environment |

---

**Need Help?** Check [README.md](README.md) for detailed documentation.
