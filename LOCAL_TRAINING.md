# Local Training Guide for GTX 1060 3GB

## 🖥️ Your Hardware
- **GPU**: GTX 1060 3GB (CUDA-enabled)
- **RAM**: 16GB
- **OS**: Windows

## 🎯 Optimizations Applied

Your GTX 1060 has only 3GB VRAM, which is limited for training transformer models. Here's how the training has been optimized:

### Memory Optimizations:
1. **Smaller Model**: Using `flan-t5-small` (80M params) instead of `flan-t5-base` (248M)
2. **Small Batch Size**: 2 samples per batch (instead of 8)
3. **Gradient Accumulation**: 8 steps = effective batch size of 16
4. **Mixed Precision (FP16)**: Reduces memory usage by 50%
5. **Gradient Checkpointing**: Trades computation for memory
6. **Reduced Sequence Lengths**: 128 input, 256 output (instead of 256/512)
7. **Adafactor Optimizer**: More memory-efficient than Adam

### Expected Performance:
- **Training Time**: ~2-3 hours per epoch (20-30 hours total for 10 epochs)
- **GPU Utilization**: ~2.5-2.8 GB VRAM
- **Accuracy**: 70-80% (slightly lower than larger model, but still good)

## 🚀 Quick Start

### Step 1: Generate Data (if not done)
```powershell
python data_generation.py
```

### Step 2: Train SQL Model
```powershell
python train_local.py --target sql --epochs 10
```

### Step 3: Train MongoDB Model
```powershell
python train_local.py --target mongodb --epochs 10
```

## 📝 Command Options

### Basic Training:
```powershell
# Train with defaults (recommended)
python train_local.py --target sql
```

### Custom Configuration:
```powershell
# Custom epochs and batch size
python train_local.py --target sql --epochs 15 --batch-size 2

# Use different model (if you have more VRAM somehow)
python train_local.py --target sql --model t5-small

# Custom output directory
python train_local.py --target sql --output-dir ./my_models/sql_v1

# Skip accuracy calculation (faster)
python train_local.py --target sql --skip-accuracy
```

### All Options:
```
--target          : 'sql' or 'mongodb' (required)
--model           : Model name (default: google/flan-t5-small)
--data-dir        : Data directory (default: data)
--epochs          : Number of epochs (default: 10)
--batch-size      : Batch size (default: 2 for 3GB GPU)
--output-dir      : Output directory
--skip-accuracy   : Skip accuracy calculation
```

## ⚙️ Troubleshooting

### 🔴 "CUDA out of memory"

**Solution 1: Reduce batch size**
```powershell
python train_local.py --target sql --batch-size 1
```

**Solution 2: Use even smaller model**
```powershell
python train_local.py --target sql --model t5-small
```

**Solution 3: Close other applications**
- Close Chrome/browsers (GPU acceleration)
- Close games, video editors, etc.
- Monitor GPU usage: `nvidia-smi`

### 🔴 "Training is too slow"

This is normal for GTX 1060. Expect:
- **~2-3 hours per epoch** (10 epochs = 20-30 hours)
- **Train overnight**: Let it run while you sleep
- **Consider Colab**: Free Tesla T4 GPU (faster)

### 🔴 "Low accuracy after training"

**Solutions:**
1. Train for more epochs (15-20)
2. Generate more training data (10,000+ samples)
3. Use the Colab notebook with larger model

### 🔴 "CUDA not available / Using CPU"

**Check CUDA installation:**
```powershell
python -c "import torch; print(f'CUDA: {torch.cuda.is_available()}')"
```

If False, install CUDA-enabled PyTorch:
```powershell
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

## 📊 Monitoring Training

### During Training:
- Watch the progress bar
- Training loss should decrease (target: < 0.5)
- Validation loss shown after each epoch

### Check GPU Usage:
```powershell
# In another terminal
nvidia-smi -l 1  # Update every 1 second
```

You should see:
- **GPU Utilization**: 90-100%
- **Memory Used**: ~2.5-2.8 GB / 3 GB
- **Temperature**: Should be under 80°C

## 💾 Output Files

After training, you'll find:

```
models/
└── texql-sql-YYYYMMDD_HHMMSS/
    ├── pytorch_model.bin       # Model weights (~320 MB)
    ├── config.json             # Model configuration
    ├── tokenizer files         # Tokenizer files
    └── logs/                   # Training logs
```

Final model saved to:
```
models/texql-sql-final/         # SQL model
models/texql-mongodb-final/     # MongoDB model
```

## 🎯 Training Tips

### 1. Train Overnight
```powershell
# Start training before bed
python train_local.py --target sql --epochs 10
# Come back in the morning (~8-10 hours)
```

### 2. Train One at a Time
Don't try to train both models simultaneously. Train SQL first, then MongoDB.

### 3. Monitor First Epoch
Stay for the first epoch (~2-3 hours) to ensure no errors, then leave it running.

### 4. Save Checkpoints
The script auto-saves after each epoch. If training crashes, you won't lose everything.

### 5. Test Early
After 3-4 epochs, you can test the model:
```powershell
python inference.py --model-path models/texql-sql-model --type sql --interactive
```

## 📈 Expected Results

### Small Model (flan-t5-small - Recommended for your GPU):
- **Training Time**: 20-30 hours (10 epochs)
- **Accuracy**: 70-80%
- **Model Size**: ~320 MB
- **Inference Speed**: Fast

### Base Model (flan-t5-base - May struggle on 3GB):
- **Training Time**: 40-60 hours (10 epochs)
- **Accuracy**: 75-85%
- **Model Size**: ~990 MB
- **May run out of memory** ⚠️

## 🆚 Comparison: Local vs Colab

| Feature | GTX 1060 Local | Colab (T4 GPU) |
|---------|---------------|----------------|
| **VRAM** | 3 GB | 16 GB |
| **Model** | flan-t5-small | flan-t5-base |
| **Batch Size** | 2 | 8 |
| **Time/Epoch** | 2-3 hours | 30-60 min |
| **Total Time** | 20-30 hours | 5-10 hours |
| **Accuracy** | 70-80% | 75-85% |
| **Cost** | Free (electricity) | Free (limited) |
| **Convenience** | Run anytime | Session limits |

## 🎓 Recommendations

### For Best Results:
1. **Use Colab** for training (faster, better accuracy)
2. **Use Local** for inference (your trained model)
3. **Start with small model** locally to test everything works
4. **Then use Colab** for final training with larger model

### For Learning:
1. **Train small model locally** first (understand the process)
2. **Watch training metrics** to learn what "good" looks like
3. **Experiment with parameters** on small datasets
4. **Use Colab for final submission**

## 🔧 Advanced: If You Want Better Performance Locally

### Option 1: Reduce Dataset Size (for testing)
```python
# Edit data_generation.py
df = generate_dataset(total_samples=1000)  # Instead of 5000
```

### Option 2: Use Quantization
```powershell
pip install bitsandbytes
# Then model will use less memory (experimental)
```

### Option 3: Shorter Training
```powershell
# Train for 5 epochs instead of 10
python train_local.py --target sql --epochs 5
```

## 📞 Need Help?

If training fails:
1. Check the error message
2. Try with `--batch-size 1`
3. Ensure no other apps using GPU
4. Check `nvidia-smi` for GPU status
5. Consider using Colab notebook instead

## ✅ Quick Checklist

Before training:
- [ ] Data generated (`data/train.csv` exists)
- [ ] GPU detected (`torch.cuda.is_available()` = True)
- [ ] At least 10GB free disk space
- [ ] No other GPU-intensive apps running
- [ ] Stable power supply (training takes hours)

During training:
- [ ] GPU utilization near 100%
- [ ] Loss decreasing each epoch
- [ ] No "out of memory" errors
- [ ] Temperature under 80°C

After training:
- [ ] Model saved successfully
- [ ] Test with sample queries
- [ ] Calculate accuracy
- [ ] Use in Streamlit app

---

**Ready to train? Run:**
```powershell
python train_local.py --target sql
```

**Let it run overnight, and you'll have your model tomorrow! 🌙**
