---
language:
- en
license: apache-2.0
tags:
- text2text-generation
- natural-language-to-sql
- natural-language-to-mongodb
- query-generation
- database
- t5
datasets:
- custom
metrics:
- bleu
- accuracy
pipeline_tag: text-generation
widget:
- text: "Find employees where salary is greater than 50000"
  example_title: "SELECT Query"
- text: "Delete orders with total_amount less than 1000"
  example_title: "DELETE Query"
- text: "Update employees set department to Sales where employee_id is 101"
  example_title: "UPDATE Query"
- text: "Insert a new employee with name John Doe, email john@example.com, department Engineering"
  example_title: "INSERT Query"
---

# NoNoQL - Natural Language to SQL/MongoDB Query Generator

**NoNoQL** (formerly TexQL) is a T5-based transformer model that converts natural language queries into both SQL and MongoDB queries. It supports SELECT, INSERT, UPDATE, DELETE, and other database operations.

## 🎯 Model Description

This model translates natural language database queries into syntactically correct SQL and MongoDB commands. It's trained on a custom dataset of 30,000+ query pairs covering various database operations, tables, and query patterns.

### Key Features

- ✅ **Dual Output**: Generates both SQL and MongoDB queries from a single natural language input
- ✅ **Multi-Operation Support**: SELECT, INSERT, UPDATE, DELETE, CREATE TABLE, and more
- ✅ **Comparison Operators**: Handles greater than, less than, equal to, and other comparisons
- ✅ **Complex Queries**: Supports WHERE clauses, aggregations, ordering, and limiting
- ✅ **Post-Processing**: Includes fixes for common model hallucinations and syntax errors

## 📊 Model Details

- **Model Architecture**: T5 (Text-to-Text Transfer Transformer)
- **Base Model**: google/t5-small
- **Parameters**: ~60M
- **Training Data**: 30,000+ natural language to SQL/MongoDB query pairs
- **Training Strategy**: Unified model trained on both SQL and MongoDB simultaneously
- **Input Format**: `translate to {sql|mongodb}: {natural_language_query}`

### Supported Tables/Collections

- **employees**: employee_id, name, email, department, salary, hire_date, age
- **departments**: department_id, department_name, manager_id, budget, location
- **projects**: project_id, project_name, start_date, end_date, budget, status
- **orders**: order_id, customer_name, product_name, quantity, order_date, total_amount
- **products**: product_id, product_name, category, price, stock_quantity, supplier

## 🚀 Usage

### Installation

```bash
pip install transformers torch
```

### Basic Usage

```python
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

# Load model and tokenizer
model_name = "mohhhhhit/nonoql"  # Replace with your HF model path
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSeq2SeqLM.from_pretrained(model_name)

# Generate SQL query
def generate_query(natural_language, target_type='sql'):
    input_text = f"translate to {target_type}: {natural_language}"
    inputs = tokenizer(input_text, return_tensors="pt", max_length=256, truncation=True)
    
    outputs = model.generate(
        **inputs,
        max_length=512,
        num_beams=10,
        temperature=0.3,
        repetition_penalty=1.2,
        length_penalty=0.8,
        early_stopping=True
    )
    
    return tokenizer.decode(outputs[0], skip_special_tokens=True)

# Example usage
nl_query = "Find employees where salary is greater than 50000"

sql_query = generate_query(nl_query, target_type='sql')
print(f"SQL: {sql_query}")
# Output: SELECT * FROM employees WHERE salary > 50000;

mongodb_query = generate_query(nl_query, target_type='mongodb')
print(f"MongoDB: {mongodb_query}")
# Output: db.employees.find({"salary": {$gt: 50000}});
```

### Example Queries

| Natural Language | SQL Output | MongoDB Output |
|-----------------|------------|----------------|
| Show all employees | `SELECT * FROM employees;` | `db.employees.find({});` |
| Find products where price is less than 100 | `SELECT * FROM products WHERE price < 100;` | `db.products.find({"price": {$lt: 100}});` |
| Update employees set department to Sales where employee_id is 101 | `UPDATE employees SET department = 'Sales' WHERE employee_id = 101;` | `db.employees.updateMany({employee_id: 101}, {$set: {department: "Sales"}});` |
| Delete orders with total_amount less than 1000 | `DELETE FROM orders WHERE total_amount < 1000;` | `db.orders.deleteMany({"total_amount": {$lt: 1000}});` |
| Insert a new employee with name John, email john@example.com | `INSERT INTO employees (name, email) VALUES ('John', 'john@example.com');` | `db.employees.insertOne({"name": "John", "email": "john@example.com"});` |

## 🎓 Training

### Dataset

- **Size**: 30,000+ query pairs
- **Operations**: SELECT (40%), INSERT (20%), UPDATE (20%), DELETE (15%), CREATE (5%)
- **Tables**: 5 main tables with realistic schemas
- **Generation**: Synthetic data with varied patterns and complexity

### Training Configuration

```python
training_args = {
    "learning_rate": 3e-4,
    "per_device_train_batch_size": 8,
    "per_device_eval_batch_size": 8,
    "num_train_epochs": 10,
    "weight_decay": 0.01,
    "warmup_steps": 500,
    "max_seq_length": 512,
}
```

### Evaluation Metrics

- **BLEU Score**: ~85%
- **Exact Match**: ~78%
- **Syntax Correctness**: ~92% (after post-processing)

## ⚙️ Post-Processing

The model includes several post-processing fixes to handle common issues:

1. **Comparison Operators**: Converts `=` to `>`, `<`, `>=`, `<=` based on keywords like "greater than", "less than"
2. **Operation Type**: Fixes wrong operations (e.g., SELECT when DELETE is intended)
3. **MongoDB Syntax**: Adds missing curly braces and converts to proper MongoDB operators
4. **UPDATE Queries**: Reconstructs malformed UPDATE statements
5. **CREATE TABLE**: Fixes hallucinated columns in table creation

## ⚠️ Limitations

- **Schema Awareness**: Model is trained on specific tables; may not generalize to completely new schemas
- **Complex Joins**: Limited support for multi-table JOINs and subqueries
- **Advanced Features**: May struggle with window functions, CTEs, and advanced SQL features
- **Hallucinations**: Can generate incorrect column names for unseen patterns (mitigated by post-processing)
- **Case Sensitivity**: Works best with lowercase natural language inputs

## 📝 Known Issues & Fixes

| Issue | Fix Applied |
|-------|-------------|
| Model outputs `=` instead of `>` or `<` | Post-processing detects comparison keywords and replaces operators |
| MongoDB missing `{}` braces | Adds curly braces around query objects |
| `SELECT` instead of `DELETE` | Detects operation intent from keywords |
| Incomplete UPDATE queries | Reconstructs from natural language parsing |

## 🛠️ Use Cases

- **Database Query Assistants**: Help non-technical users query databases
- **Educational Tools**: Teach SQL/MongoDB syntax through examples
- **Prototyping**: Quickly generate queries for testing
- **Documentation**: Auto-generate query examples
- **Migration Tools**: Convert between SQL and MongoDB syntaxes

## 📄 Citation

If you use this model in your research or application, please cite:

```bibtex
@misc{nonoql2026,
  title={NoNoQL: Natural Language to SQL and MongoDB Query Generation},
  author={Mohit Panchal},
  year={2026},
  howpublished={\url{https://huggingface.co/mohhhhhit/nonoql}},
}
```

## 📜 License

This model is released under the Apache 2.0 License.

## 🤝 Contributing

Contributions, feedback, and suggestions are welcome! Please feel free to:
- Report issues or bugs
- Suggest new features
- Improve the training data
- Add support for more database systems

## 🔗 Links

- **Model Repository**: [Hugging Face](https://huggingface.co/mohhhhhit/nonoql)
- **GitHub**: [Source Code](https://github.com/mohhhit/NoNoQL)
- **Demo**: [Streamlit App](your-demo-url)

## 🙏 Acknowledgments

- Built on the T5 architecture by Google Research
- Trained using the Hugging Face Transformers library
- Inspired by the need for more accessible database querying tools

---

**Note**: This model is designed for educational and prototyping purposes. Always validate generated queries before executing them on production databases.
