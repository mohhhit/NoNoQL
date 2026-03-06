# TexQL Quick Start Guide

## 🚀 Get Started in 3 Steps

### Step 1: Generate Training Data (5 minutes)

```bash
# Install dependencies
pip install pandas numpy faker

# Generate 5000 training samples
python data_generation.py
```

**Output:**
- `data/training_data.csv` - Full dataset
- `data/train.csv` - Training set (80%)
- `data/val.csv` - Validation set (10%)
- `data/test.csv` - Test set (10%)

### Step 2: Train Models in Google Colab (60 minutes)

1. **Open Google Colab**: https://colab.research.google.com/

2. **Upload Notebook**: Upload `training_colab.ipynb`

3. **Enable GPU**:
   - Runtime → Change runtime type → GPU (T4)

4. **Upload Data**:
   - Mount Google Drive
   - Upload data files to Drive
   - Or use file upload feature

5. **Train SQL Model**:
   ```python
   TARGET_TYPE = 'sql'  # Line in notebook
   # Run all cells
   ```

6. **Train MongoDB Model**:
   ```python
   TARGET_TYPE = 'mongodb'  # Change this line
   # Run all cells again
   ```

7. **Download Models**:
   - Models saved to Google Drive automatically
   - Or download from Colab: `/content/texql-{type}-final/`

### Step 3: Run the Application (2 minutes)

```bash
# Create models directory
mkdir -p models

# Move your trained models
mv texql-sql-final models/
mv texql-mongodb-final models/

# Install frontend dependencies
pip install streamlit transformers torch

# Run the app
streamlit run app.py
```

Open browser: http://localhost:8501

## 📝 Usage Examples

### Web Interface:

1. **Click Example Queries** to try pre-made examples
2. **Enter Custom Query** in the text area
3. **Click "Generate Queries"** to see SQL and MongoDB results
4. **Copy Queries** with one click
5. **View History** of your past queries

### Command Line:

```bash
# Single query
python inference.py \
  --model-path models/texql-sql-final \
  --type sql \
  --query "Show all employees with salary greater than 50000"

# Interactive mode
python inference.py \
  --model-path models/texql-sql-final \
  --type sql \
  --interactive

# Batch processing
echo "Show all employees" > queries.txt
echo "Find departments with budget over 100000" >> queries.txt

python inference.py \
  --model-path models/texql-sql-final \
  --type sql \
  --file queries.txt \
  --output results.json
```

### Python API:

```python
from inference import TexQLInference

# Load model
model = TexQLInference("models/texql-sql-final", target_type="sql")

# Generate query
result = model.generate_query("Show all employees")
print(result)
# Output: SELECT * FROM employees;

# Batch generate
queries = [
    "Show all employees",
    "Find products with price over 1000",
    "Count all orders"
]
results = model.batch_generate(queries)
for q, r in zip(queries, results):
    print(f"{q} → {r}")
```

## 🎯 Sample Natural Language Queries

### READ Operations:
- "Show all employees"
- "Find employees where salary is greater than 50000"
- "Get all departments with budget more than 100000"
- "Show top 10 employees ordered by salary"
- "Count all products in Electronics category"
- "Find orders where customer_name contains Smith"

### CREATE Operations:
- "Insert a new employee with name John Doe, email john@example.com"
- "Add a product with name Laptop, price 1500, category Electronics"
- "Create a new department with name Research, budget 500000"

### UPDATE Operations:
- "Update employees set department to Sales where employee_id is 101"
- "Change product price to 1200 where product_name is Laptop"
- "Increase salary by 5000 for employees in Engineering department"

### DELETE Operations:
- "Delete orders with total_amount less than 1000"
- "Remove products where stock_quantity is 0"
- "Delete employees with age less than 18"

## 🔧 Configuration Tips

### For Better Results:

1. **Use Specific Language**:
   - ✅ "Find employees where salary > 50000"
   - ❌ "Show me people who make a lot"

2. **Include Column Names**:
   - ✅ "Update products set price to 100 where product_id is 5"
   - ❌ "Change the cost to 100 for item 5"

3. **Be Explicit with Operations**:
   - ✅ "Insert a new employee..."
   - ✅ "Delete orders where..."
   - ❌ "I want to add something"

### Adjust Generation Parameters:

- **Temperature** (0.1 - 1.0):
  - Lower (0.3): More deterministic, consistent
  - Higher (0.9): More creative, varied

- **Beam Search** (1 - 10):
  - Higher: Better quality, slower
  - Lower: Faster, may be less accurate

## 📊 Expected Performance

### Training Metrics:
- Training Loss: ~0.3-0.5 (lower is better)
- Validation Loss: ~0.4-0.6
- Training Time: 30-60 min per model (T4 GPU)

### Inference Metrics:
- Accuracy: 60-85% exact match
- Speed: 100-200 queries/sec (GPU)
- Latency: ~50-100ms per query (GPU)

## ❓ Troubleshooting

### Issue: "CUDA out of memory"
**Solution:** Reduce batch size in training notebook
```python
per_device_train_batch_size=4
gradient_accumulation_steps=4
```

### Issue: "Model not found"
**Solution:** Check model path
```bash
ls -la models/texql-sql-final/
# Should show: config.json, pytorch_model.bin, tokenizer files
```

### Issue: "Low accuracy"
**Solution:** 
1. Generate more training data (10,000+ samples)
2. Train for more epochs (15-20)
3. Use larger model (flan-t5-large)

### Issue: "Streamlit not loading model"
**Solution:**
1. Check model path in sidebar
2. Click "Load/Reload Models"
3. Restart Streamlit: `Ctrl+C` then `streamlit run app.py`

## 🎓 Next Steps

1. **Experiment with Examples**: Try all example queries
2. **Test Custom Queries**: Create your own queries
3. **Analyze Results**: Check accuracy on your use cases
4. **Fine-tune**: Retrain with your specific data
5. **Deploy**: Set up as API or web service

## 📚 Additional Resources

- Full documentation: `README.md`
- Training notebook: `training_colab.ipynb`
- Data generation: `data_generation.py`
- Inference script: `inference.py`
- Web app: `app.py`

## 💡 Pro Tips

1. **Save your models**: Always backup to Google Drive
2. **Track experiments**: Use Weights & Biases (optional)
3. **Start small**: Test with 1000 samples first
4. **Monitor training**: Watch loss curves in Colab
5. **Version control**: Keep track of model versions

---

**Need Help?** Check README.md or examine the training logs!

**Ready to Deploy?** Consider using Docker and FastAPI for production!
