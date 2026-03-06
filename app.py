"""
NoNoQL - Natural Language to SQL/MongoDB Query Generator
Streamlit Frontend Application
"""

import streamlit as st
import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import os
import json
from datetime import datetime

HISTORY_FILE_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "data",
    "query_history.json"
)

SCHEMA_FILE_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "data",
    "database_schema.txt"
)

DEFAULT_SCHEMA = """**employees**
- employee_id, name, email
- department, salary, hire_date, age

**departments**
- department_id, department_name
- manager_id, budget, location

**projects**
- project_id, project_name
- start_date, end_date, budget, status

**orders**
- order_id, customer_name
- product_name, quantity
- order_date, total_amount

**products**
- product_id, product_name
- category, price
- stock_quantity, supplier"""

# Page configuration
st.set_page_config(
    page_title="NoNoQL - Natural Language to SQL/MongoDB Query Generator",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    /* Inject title into Streamlit header bar */
    header[data-testid="stHeader"] {
        background-color: rgba(14, 17, 23, 0.95) !important;
    }
    
    header[data-testid="stHeader"]::before {
        content: "NoNoQL";
        color: white;
        font-size: 1.3rem;
        font-weight: 600;
        position: absolute;
        left: 1rem;
        top: 50%;
        transform: translateY(-50%);
        z-index: 999;
    }
    
    .query-box {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 20px;
        margin: 10px 0;
        border-left: 5px solid #1E88E5;
    }
    .success-box {
        background-color: #d4edda;
        border-radius: 10px;
        padding: 20px;
        margin: 10px 0;
        border-left: 5px solid #28a745;
    }
    .example-query {
        background-color: #fff3cd;
        border-radius: 5px;
        padding: 10px;
        margin: 5px 0;
        cursor: pointer;
    }
    .example-query:hover {
        background-color: #ffe69c;
    }
    .stButton>button {
        width: 100%;
        background-color: #1E88E5;
        color: white;
        font-size: 1.1rem;
        padding: 0.5rem 1rem;
        border-radius: 10px;
        border: none;
        margin-top: 1rem;
    }
    .stButton>button:hover {
        background-color: #1565C0;
    }
</style>
""", unsafe_allow_html=True)


def extract_columns_from_nl(natural_language_query):
    """Extract table name and column names from natural language query"""
    import re
    
    nl = natural_language_query.lower().strip()
    
    # Extract table name
    table_match = re.search(r'(?:table|collection)\s+(?:named|called)?\s*(\w+)', nl)
    table_name = table_match.group(1) if table_match else None
    
    # Extract column names - look for patterns like "columns as X, Y, Z" or "with X, Y, Z"
    columns = []
    
    # Pattern 1: "columns as/named X, Y, Z"
    col_match = re.search(r'columns?\s+(?:as|named|like|called)?\s*([^,]+(?:,\s*[^,]+)*)', nl)
    if col_match:
        col_text = col_match.group(1)
        # Split by comma or 'and'
        columns = re.split(r',|\s+and\s+', col_text)
        columns = [c.strip() for c in columns if c.strip()]
    
    # Pattern 2: "add columns X, Y, Z" 
    if not columns:
        col_match = re.search(r'(?:add|with)\s+(?:columns?)?\s*([^,]+(?:,\s*[^,]+)*)', nl)
        if col_match:
            col_text = col_match.group(1)
            columns = re.split(r',|\s+and\s+', col_text)
            columns = [c.strip() for c in columns if c.strip()]
    
    return table_name, columns


def fix_create_table_sql(generated_sql, table_name, requested_columns):
    """Replace hallucinated columns with actual requested columns in CREATE TABLE"""
    import re
    
    if not table_name or not requested_columns:
        return generated_sql
    
    # Check if it's a CREATE TABLE query
    if not re.search(r'CREATE\s+TABLE', generated_sql, re.IGNORECASE):
        return generated_sql
    
    # Default data types for common column patterns
    def infer_type(col_name):
        col_lower = col_name.lower()
        if 'id' in col_lower:
            return 'INT PRIMARY KEY'
        elif any(word in col_lower for word in ['name', 'title', 'description', 'address', 'city']):
            return 'VARCHAR(100)'
        elif any(word in col_lower for word in ['email']):
            return 'VARCHAR(100)'
        elif any(word in col_lower for word in ['phone', 'contact', 'mobile']):
            return 'VARCHAR(20)'
        elif any(word in col_lower for word in ['date', 'created', 'updated']):
            return 'DATE'
        elif any(word in col_lower for word in ['price', 'salary', 'amount', 'cost']):
            return 'DECIMAL(10,2)'
        elif any(word in col_lower for word in ['age', 'quantity', 'count', 'stock']):
            return 'INT'
        elif any(word in col_lower for word in ['status', 'type', 'category']):
            return 'VARCHAR(50)'
        else:
            return 'VARCHAR(100)'
    
    # Build column definitions
    col_defs = []
    for col in requested_columns:
        col_clean = col.strip()
        if col_clean:
            col_type = infer_type(col_clean)
            col_defs.append(f"{col_clean} {col_type}")
    
    # Rebuild a clean CREATE TABLE statement from requested columns.
    # This avoids malformed model output leaking extra columns outside parentheses.
    if_not_exists_match = re.search(
        r'CREATE\s+TABLE\s+IF\s+NOT\s+EXISTS\s+' + re.escape(table_name),
        generated_sql,
        re.IGNORECASE
    )
    if if_not_exists_match:
        create_clause = if_not_exists_match.group(0)
    else:
        create_match = re.search(
            r'CREATE\s+TABLE\s+' + re.escape(table_name),
            generated_sql,
            re.IGNORECASE
        )
        if not create_match:
            return generated_sql
        create_clause = create_match.group(0)

    new_columns = ', '.join(col_defs)
    return f"{create_clause} ({new_columns});"


def fix_create_collection_mongo(generated_mongo, table_name, requested_columns):
    """Fix MongoDB createCollection to use correct collection name and sample document"""
    if not table_name:
        return generated_mongo
    
    # Build sample document with requested columns
    doc_fields = []
    for col in requested_columns:
        col_clean = col.strip()
        if col_clean:
            # Provide example values based on column name
            if 'id' in col_clean.lower():
                doc_fields.append(f'"{col_clean}": 1')
            elif any(word in col_clean.lower() for word in ['name', 'title']):
                doc_fields.append(f'"{col_clean}": "sample_name"')
            elif 'email' in col_clean.lower():
                doc_fields.append(f'"{col_clean}": "user@example.com"')
            elif any(word in col_clean.lower() for word in ['phone', 'contact']):
                doc_fields.append(f'"{col_clean}": "1234567890"')
            else:
                doc_fields.append(f'"{col_clean}": "sample_value"')
    
    # Create proper MongoDB command
    if doc_fields:
        fixed_mongo = f"db.{table_name}.insertOne({{{', '.join(doc_fields)}}});"
    else:
        fixed_mongo = f"db.createCollection('{table_name}');"
    
    return fixed_mongo


def detect_comparison_operator(natural_language_query):
    """Detect comparison operator from natural language
    
    Returns: operator string ('>', '<', '>=', '<=', '=') or None
    """
    import re
    
    nl = natural_language_query.lower()
    
    # Check for comparison keywords
    if re.search(r'\b(greater than|more than|above|exceeds?)\b', nl):
        return '>'
    elif re.search(r'\b(less than|fewer than|below|under)\b', nl):
        return '<'
    elif re.search(r'\b(greater than or equal to|at least|minimum)\b', nl):
        return '>='
    elif re.search(r'\b(less than or equal to|at most|maximum)\b', nl):
        return '<='
    elif re.search(r'\b(equals?|is|=)\b', nl):
        return '='
    
    return None


def fix_sql_operation_type(generated_sql, natural_language_query):
    """Fix SQL queries with wrong operation type (SELECT vs DELETE vs UPDATE vs INSERT)"""
    import re
    
    nl = natural_language_query.lower()
    
    # Detect intended operation from natural language
    if re.search(r'\b(delete|remove)\b', nl):
        # Should be DELETE, not SELECT
        if re.match(r'SELECT\s+\*\s+FROM', generated_sql, re.IGNORECASE):
            # Extract table and WHERE clause
            match = re.search(r'SELECT\s+\*\s+FROM\s+(\w+)(\s+WHERE\s+.+)?', generated_sql, re.IGNORECASE)
            if match:
                table = match.group(1)
                where_clause = match.group(2) if match.group(2) else ''
                generated_sql = f"DELETE FROM {table}{where_clause}"
    
    return generated_sql


def fix_mongodb_operation_type(generated_mongo, natural_language_query):
    """Fix MongoDB queries with wrong operation type"""
    import re
    
    nl = natural_language_query.lower()
    
    # Detect intended operation from natural language
    if re.search(r'\b(delete|remove)\b', nl):
        # Should be deleteMany, not find, insertOne, or deleteOne
        if re.search(r'\.(find|findOne|insertOne|deleteOne)\s*\(', generated_mongo):
            # Replace with deleteMany
            generated_mongo = re.sub(
                r'\.(find|findOne|insertOne|deleteOne)\s*\(',
                '.deleteMany(',
                generated_mongo
            )
    
    return generated_mongo


def fix_mongodb_missing_braces(generated_mongo):
    """Fix MongoDB queries that are missing curly braces around query objects
    
    Example: db.collection.find("field": value) -> db.collection.find({"field": value})
    """
    import re
    
    # Pattern: .method("field": value) or .method(field: value)
    # Missing the outer { } around the query object
    
    # Pattern 1: .find("field": value) -> .find({"field": value})
    pattern1 = r'(\.\w+)\(\"(\w+)\":\s*([^)]+)\)'
    match = re.search(pattern1, generated_mongo)
    if match:
        method = match.group(1)  # e.g., .find
        field = match.group(2)    # e.g., salary
        value = match.group(3).strip()  # e.g., 50000
        # Remove trailing semicolon if present
        value = value.rstrip(';')
        # Reconstruct with proper braces
        generated_mongo = re.sub(
            pattern1,
            method + '({"' + field + '": ' + value + '})',
            generated_mongo
        )
    else:
        # Pattern 2: .find(field: value) -> .find({field: value})
        pattern2 = r'(\.\w+)\((\w+):\s*([^)]+)\)'
        match = re.search(pattern2, generated_mongo)
        if match:
            method = match.group(1)
            field = match.group(2)
            value = match.group(3).strip()
            value = value.rstrip(';')
            generated_mongo = re.sub(
                pattern2,
                method + '({' + field + ': ' + value + '})',
                generated_mongo
            )
    
    return generated_mongo


def fix_comparison_operator_sql(generated_sql, natural_language_query):
    """Fix SQL queries with wrong comparison operators"""
    import re
    
    correct_op = detect_comparison_operator(natural_language_query)
    
    if correct_op and correct_op != '=':
        # Replace = with correct operator in WHERE clause
        # Pattern: WHERE column = value
        generated_sql = re.sub(
            r'(WHERE\s+\w+)\s*=\s*',
            r'\1 ' + correct_op + ' ',
            generated_sql,
            flags=re.IGNORECASE
        )
    
    return generated_sql


def fix_comparison_operator_mongodb(generated_mongo, natural_language_query):
    """Fix MongoDB queries with wrong comparison operators"""
    import re
    
    correct_op = detect_comparison_operator(natural_language_query)
    
    if correct_op and correct_op != '=':
        # Map SQL operators to MongoDB operators
        mongo_op_map = {
            '>': '$gt',
            '<': '$lt',
            '>=': '$gte',
            '<=': '$lte'
        }
        
        mongo_op = mongo_op_map.get(correct_op)
        
        if mongo_op:
            # More robust pattern matching for MongoDB queries
            # Handles: db.collection.operation({"field": value}) or db.collection.operation({field: value})
            
            # Pattern 1: {"field": value} - quoted field name
            pattern1 = r'\{"(\w+)":\s*([^,}{]+)\}'
            match = re.search(pattern1, generated_mongo)
            if match:
                field = match.group(1)
                value = match.group(2).strip()
                # Replace with comparison operator
                replacement = '{"' + field + '": {' + mongo_op + ': ' + value + '}}'
                generated_mongo = re.sub(pattern1, replacement, generated_mongo, count=1)
            else:
                # Pattern 2: {field: value} - unquoted field name
                pattern2 = r'\{(\w+):\s*([^,}{]+)\}'
                match = re.search(pattern2, generated_mongo)
                if match:
                    field = match.group(1)
                    value = match.group(2).strip()
                    # Replace with comparison operator
                    replacement = '{' + field + ': {' + mongo_op + ': ' + value + '}}'
                    generated_mongo = re.sub(pattern2, replacement, generated_mongo, count=1)
    
    return generated_mongo


def parse_update_query(natural_language_query):
    """Parse UPDATE query from natural language
    
    Example: "Update employees set department to Sales where employee_id is 101"
    Returns: (table, set_column, set_value, where_column, where_value)
    """
    import re
    
    # Use case-insensitive matching but preserve original values
    
    # Pattern 1: "update X set Y to Z where A is B"
    match = re.search(
        r'update\s+(\w+)\s+set\s+(\w+)\s+to\s+([^\s]+(?:\s+[^\s]+)*?)\s+where\s+(\w+)\s+(?:is|equals?|=)\s+(.+)',
        natural_language_query,
        re.IGNORECASE
    )
    
    if match:
        table_name = match.group(1)
        set_column = match.group(2)
        set_value = match.group(3).strip()
        where_column = match.group(4)
        where_value = match.group(5).strip()
        return (table_name, set_column, set_value, where_column, where_value)
    
    # Pattern 2: "update X set Y = Z where A = B"
    match = re.search(
        r'update\s+(\w+)\s+set\s+(\w+)\s*=\s*([^\s]+(?:\s+[^\s]+)*?)\s+where\s+(\w+)\s*=\s*(.+)',
        natural_language_query,
        re.IGNORECASE
    )
    
    if match:
        table_name = match.group(1)
        set_column = match.group(2)
        set_value = match.group(3).strip()
        where_column = match.group(4)
        where_value = match.group(5).strip()
        return (table_name, set_column, set_value, where_column, where_value)
    
    return None


def fix_update_query_sql(generated_sql, natural_language_query):
    """Fix malformed UPDATE SQL queries"""
    import re
    
    # Check if model generated garbage for UPDATE
    if 'update' in natural_language_query.lower():
        # If output doesn't look like proper SQL UPDATE
        if not re.search(r'UPDATE\s+\w+\s+SET', generated_sql, re.IGNORECASE):
            parsed = parse_update_query(natural_language_query)
            if parsed:
                table, set_col, set_val, where_col, where_val = parsed
                
                # Determine if value should be quoted (string vs number)
                try:
                    # Try to parse as number
                    float(set_val)
                    set_val_quoted = set_val
                except:
                    set_val_quoted = f"'{set_val}'"
                
                try:
                    float(where_val)
                    where_val_quoted = where_val
                except:
                    where_val_quoted = f"'{where_val}'"
                
                # Reconstruct proper SQL
                return f"UPDATE {table} SET {set_col} = {set_val_quoted} WHERE {where_col} = {where_val_quoted};"
    
    return generated_sql


def fix_update_query_mongodb(generated_mongo, natural_language_query):
    """Fix malformed UPDATE MongoDB queries"""
    import re
    
    # Check if model generated garbage for UPDATE
    if 'update' in natural_language_query.lower():
        # If output doesn't look like proper MongoDB update
        if not re.search(r'\.update', generated_mongo, re.IGNORECASE):
            parsed = parse_update_query(natural_language_query)
            if parsed:
                table, set_col, set_val, where_col, where_val = parsed
                
                # Determine if value should be quoted
                try:
                    float(set_val)
                    set_val_formatted = set_val
                except:
                    set_val_formatted = f'"{set_val}"'
                
                try:
                    float(where_val)
                    where_val_formatted = where_val
                except:
                    where_val_formatted = f'"{where_val}"'
                
                # Reconstruct proper MongoDB
                return f"db.{table}.updateMany({{{where_col}: {where_val_formatted}}}, {{$set: {{{set_col}: {set_val_formatted}}}}});"
    
    return generated_mongo


class TexQLModel:
    """Unified model wrapper for SQL/MongoDB generation"""
    
    def __init__(self, model_path):
        """Initialize the model for inference"""
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(model_path)
            self.model = AutoModelForSeq2SeqLM.from_pretrained(model_path)
            self.model.to(self.device)
            self.model.eval()
            self.loaded = True
        except Exception as e:
            st.error(f"Error loading model: {str(e)}")
            self.loaded = False
    
    def generate_query(self, natural_language_query, target_type='sql', temperature=0.3, 
                      num_beams=10, repetition_penalty=1.2, length_penalty=0.8):
        """Generate SQL or MongoDB query from natural language
        
        Args:
            natural_language_query: The user's natural language query
            target_type: 'sql' or 'mongodb' to specify output format
            temperature: Sampling temperature (lower = more focused)
            num_beams: Number of beams for beam search
            repetition_penalty: Penalty for repeating tokens (>1.0 discourages repetition)
            length_penalty: Penalty for length (>1.0 encourages longer, <1.0 encourages shorter)
        """
        if not self.loaded:
            return "Model not loaded"
        
        input_text = f"translate to {target_type}: {natural_language_query}"
        
        inputs = self.tokenizer(
            input_text,
            return_tensors="pt",
            max_length=256,
            truncation=True
        ).to(self.device)
        
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_length=512,
                num_beams=num_beams,
                temperature=temperature,
                repetition_penalty=repetition_penalty,
                length_penalty=length_penalty,
                no_repeat_ngram_size=3,  # Prevent repeating 3-grams
                early_stopping=True,
                do_sample=False  # Use greedy/beam search (more deterministic)
            )
        
        generated_query = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # ✅ POST-PROCESSING: Fix hallucinated columns in CREATE queries
        if any(word in natural_language_query.lower() for word in ['create', 'add columns']):
            table_name, requested_columns = extract_columns_from_nl(natural_language_query)
            
            if table_name and requested_columns:
                if target_type == 'sql':
                    generated_query = fix_create_table_sql(generated_query, table_name, requested_columns)
                elif target_type == 'mongodb':
                    generated_query = fix_create_collection_mongo(generated_query, table_name, requested_columns)
        
        # ✅ POST-PROCESSING: Fix malformed UPDATE queries
        if 'update' in natural_language_query.lower() and 'set' in natural_language_query.lower():
            if target_type == 'sql':
                generated_query = fix_update_query_sql(generated_query, natural_language_query)
            elif target_type == 'mongodb':
                generated_query = fix_update_query_mongodb(generated_query, natural_language_query)
        
        # ✅ POST-PROCESSING: Fix wrong operation type (SELECT vs DELETE, etc.)
        if target_type == 'sql':
            generated_query = fix_sql_operation_type(generated_query, natural_language_query)
        elif target_type == 'mongodb':
            generated_query = fix_mongodb_operation_type(generated_query, natural_language_query)
        
        # ✅ POST-PROCESSING: Fix missing curly braces in MongoDB queries
        if target_type == 'mongodb':
            generated_query = fix_mongodb_missing_braces(generated_query)
        
        # ✅ POST-PROCESSING: Fix comparison operators (>, <, >=, <=)
        if target_type == 'sql':
            generated_query = fix_comparison_operator_sql(generated_query, natural_language_query)
        elif target_type == 'mongodb':
            generated_query = fix_comparison_operator_mongodb(generated_query, natural_language_query)
        
        return generated_query


@st.cache_resource
def load_model(model_path):
    """Load the unified NoNoQL model (cached)"""
    model = None
    
    if os.path.exists(model_path):
        model = TexQLModel(model_path)
    
    return model


def save_query_history(nl_query, sql_query, mongodb_query, max_history=500):
    """Save query to history with size limit"""
    if 'history' not in st.session_state:
        st.session_state.history = []
    
    st.session_state.history.append({
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'natural_language': nl_query,
        'sql': sql_query,
        'mongodb': mongodb_query
    })
    
    # Keep only the most recent entries
    if len(st.session_state.history) > max_history:
        st.session_state.history = st.session_state.history[-max_history:]

    persist_query_history(st.session_state.history)


def delete_history_entry(index):
    """Delete a specific history entry"""
    if 'history' in st.session_state and 0 <= index < len(st.session_state.history):
        st.session_state.history.pop(index)
        persist_query_history(st.session_state.history)


def load_query_history():
    """Load query history from disk"""
    try:
        if not os.path.exists(HISTORY_FILE_PATH):
            return []

        with open(HISTORY_FILE_PATH, "r", encoding="utf-8") as history_file:
            history = json.load(history_file)

        if isinstance(history, list):
            return history
        return []
    except Exception:
        return []


def persist_query_history(history):
    """Persist query history to disk"""
    os.makedirs(os.path.dirname(HISTORY_FILE_PATH), exist_ok=True)
    with open(HISTORY_FILE_PATH, "w", encoding="utf-8") as history_file:
        json.dump(history, history_file, indent=2)


def load_schema():
    """Load database schema from disk"""
    try:
        if not os.path.exists(SCHEMA_FILE_PATH):
            return DEFAULT_SCHEMA

        with open(SCHEMA_FILE_PATH, "r", encoding="utf-8") as schema_file:
            schema = schema_file.read()

        return schema if schema.strip() else DEFAULT_SCHEMA
    except Exception:
        return DEFAULT_SCHEMA


def persist_schema(schema):
    """Persist database schema to disk"""
    os.makedirs(os.path.dirname(SCHEMA_FILE_PATH), exist_ok=True)
    with open(SCHEMA_FILE_PATH, "w", encoding="utf-8") as schema_file:
        schema_file.write(schema)


def main():
    if 'history' not in st.session_state:
        st.session_state.history = load_query_history()
    
    if 'schema' not in st.session_state:
        st.session_state.schema = load_schema()
    
    if 'schema_edit_mode' not in st.session_state:
        st.session_state.schema_edit_mode = False

    # Sidebar
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # Model path
        st.subheader("Model Path")
        model_path = st.text_input(
            "NoNoQL Model Path",
            value="models",
            help="Path to the unified NoNoQL model (generates both SQL and MongoDB)"
        )
        
        # Generation parameters
        st.subheader("Generation Parameters")
        temperature = st.slider(
            "Temperature",
            min_value=0.1,
            max_value=1.0,
            value=0.3,  # ✅ Lower default = less hallucination
            step=0.1,
            help="Lower = more focused, Higher = more creative"
        )
        num_beams = st.slider(
            "Beam Search Width",
            min_value=1,
            max_value=10,
            value=10,  # ✅ Higher value = more accurate results
            help="Higher values improve accuracy (recommended: keep at 10)"
        )
        repetition_penalty = st.slider(
            "Repetition Penalty",
            min_value=1.0,
            max_value=2.0,
            value=1.2,  # ✅ Discourages adding extra unwanted columns
            step=0.1,
            help="Higher = less repetition (prevents hallucinating extra columns)"
        )
        length_penalty = st.slider(
            "Length Penalty",
            min_value=0.5,
            max_value=1.5,
            value=0.8,  # ✅ Prefer shorter outputs
            step=0.1,
            help="Lower = prefer shorter outputs, Higher = prefer longer outputs"
        )
        
        # Load models button
        if st.button("🔄 Load/Reload Models"):
            st.cache_resource.clear()
            st.rerun()
        
        # History management
        st.subheader("📚 History Settings")
        max_history_size = st.number_input(
            "Max History Entries",
            min_value=10,
            max_value=1000,
            value=500,
            step=10,
            help="Maximum number of queries to keep in history"
        )
        
        # Database schema info
        st.subheader("📊 Database Schema")
        
        # Toggle edit mode
        col1, col2 = st.columns([1, 3])
        with col1:
            if st.button("✏️ Edit" if not st.session_state.schema_edit_mode else "👁️ View"):
                st.session_state.schema_edit_mode = not st.session_state.schema_edit_mode
                st.rerun()
        with col2:
            if st.session_state.schema_edit_mode:
                st.info("✏️ Editing Mode")
            else:
                st.caption("View your database tables and columns")
        
        if st.session_state.schema_edit_mode:
            # Edit mode - text area
            edited_schema = st.text_area(
                "Edit Database Schema",
                value=st.session_state.schema,
                height=300,
                help="Define your database tables and columns. Use Markdown format."
            )
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("💾 Save Schema", use_container_width=True):
                    st.session_state.schema = edited_schema
                    persist_schema(edited_schema)
                    st.success("Schema saved!")
                    st.session_state.schema_edit_mode = False
                    st.rerun()
            
            with col2:
                if st.button("🔄 Reset to Default", use_container_width=True):
                    st.session_state.schema = DEFAULT_SCHEMA
                    persist_schema(DEFAULT_SCHEMA)
                    st.success("Schema reset to default!")
                    st.rerun()
        else:
            # View mode - expandable display
            with st.expander("View Available Tables", expanded=False):
                st.markdown(st.session_state.schema)
    
    # Load model
    with st.spinner("Loading model..."):
        model = load_model(model_path)
    
    # Model status
    if model and model.loaded:
        device_info = "🎮 GPU" if model.device == "cuda" else "💻 CPU"
        st.success(f"✅ Model Loaded ({device_info})")
        st.info("💡 This model generates both SQL and MongoDB queries")
    else:
        st.error("⚠️ Model Not Available - Please check the model path")
    
    # Query input
    st.subheader("🔤 Enter Your Query")
    
    # Example queries dropdown
    with st.expander("💡 Example Queries - Click to expand"):
        examples = [
            "Show all employees",
            "Find employees where salary is greater than 50000",
            "Get all departments with budget more than 100000",
            "Insert a new employee with name John Doe, email john@example.com, department Engineering",
            "Update employees set department to Sales where employee_id is 101",
            "Delete orders with total_amount less than 1000",
            "Count all products in Electronics category",
            "Show top 10 employees ordered by salary",
        ]
        
        selected_example = st.selectbox(
            "Choose an example query:",
            [""] + examples,
            index=0,
            format_func=lambda x: "Select an example..." if x == "" else x
        )
        
        if selected_example and st.button("📝 Use This Example", use_container_width=True):
            st.session_state.user_query = selected_example
            st.rerun()
    
    user_query = st.text_area(
        "or",
        value=st.session_state.get('user_query', ''),
        height=100,
        placeholder="write your query here..."
    )
    
    # Generate button
    if st.button("🚀 Generate Queries"):
        if not user_query.strip():
            st.warning("Please enter a query")
        elif not model or not model.loaded:
            st.error("Model is not loaded. Please check the model path and reload.")
        else:
            with st.spinner("Generating queries..."):
                # Generate both SQL and MongoDB from the same model
                sql_query = model.generate_query(
                    user_query,
                    target_type='sql',
                    temperature=temperature,
                    num_beams=num_beams,
                    repetition_penalty=repetition_penalty,
                    length_penalty=length_penalty
                )
                
                mongodb_query = model.generate_query(
                    user_query,
                    target_type='mongodb',
                    temperature=temperature,
                    num_beams=num_beams,
                    repetition_penalty=repetition_penalty,
                    length_penalty=length_penalty
                )
                
                # Save to history
                save_query_history(user_query, sql_query, mongodb_query, max_history_size)
                
                # Display results
                st.markdown("---")
                st.success("✅ Queries Generated Successfully!")
                
                # Input query
                st.markdown('<div class="query-box">', unsafe_allow_html=True)
                st.markdown("**📝 Your Query:**")
                st.code(user_query, language="text")
                st.markdown('</div>', unsafe_allow_html=True)
                
                # Results in columns
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("### 🗄️ SQL Query")
                    st.code(sql_query, language="sql")
                    
                    # Copy button
                    if st.button("📋 Copy SQL", key="copy_sql"):
                        st.session_state.clipboard = sql_query
                        st.success("Copied to clipboard!")
                
                with col2:
                    st.markdown("### 🍃 MongoDB Query")
                    st.code(mongodb_query, language="javascript")
                    
                    # Copy button
                    if st.button("📋 Copy MongoDB", key="copy_mongo"):
                        st.session_state.clipboard = mongodb_query
                        st.success("Copied to clipboard!")
    
    # Query history
    if 'history' in st.session_state and st.session_state.history:
        st.markdown("---")
        st.subheader("📚 Query History")
        
        # History management controls
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            search_term = st.text_input(
                "🔍 Search History",
                placeholder="Search in queries...",
                label_visibility="collapsed"
            )
        
        with col2:
            sort_order = st.selectbox(
                "Sort",
                ["Newest First", "Oldest First"],
                label_visibility="collapsed"
            )
        
        with col3:
            show_limit = st.number_input(
                "Show",
                min_value=5,
                max_value=100,
                value=10,
                step=5,
                label_visibility="collapsed"
            )
        
        # Action buttons
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🗑️ Clear All History"):
                st.session_state.history = []
                persist_query_history(st.session_state.history)
                st.rerun()
        
        with col2:
            if st.button("💾 Export History"):
                history_json = json.dumps(st.session_state.history, indent=2)
                st.download_button(
                    label="Download History (JSON)",
                    data=history_json,
                    file_name=f"nonoql_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )
        
        # Filter history
        filtered_history = st.session_state.history
        if search_term:
            search_lower = search_term.lower()
            filtered_history = [
                entry for entry in st.session_state.history
                if search_lower in entry['natural_language'].lower() or
                   search_lower in entry.get('sql', '').lower() or
                   search_lower in entry.get('mongodb', '').lower()
            ]
        
        # Sort history
        if sort_order == "Oldest First":
            display_history = filtered_history[:show_limit]
        else:
            display_history = list(reversed(filtered_history[-show_limit:]))
        
        # Display count
        st.markdown(f"**Showing {len(display_history)} of {len(filtered_history)} queries** (Total: {len(st.session_state.history)})")
        
        if not display_history:
            st.info("No queries found matching your search.")
        
        # Display history entries
        for display_idx, entry in enumerate(display_history):
            # Find actual index in original history for deletion
            actual_idx = st.session_state.history.index(entry)
            
            with st.expander(
                f"🕐 {entry['timestamp']} - {entry['natural_language'][:60]}...",
                expanded=False
            ):
                # Action buttons for this entry
                col1, col2, col3 = st.columns([3, 1, 1])
                
                with col1:
                    st.markdown(f"**Natural Language Query:**")
                    st.info(entry['natural_language'])
                
                with col2:
                    if st.button("🔄 Rerun", key=f"rerun_{actual_idx}"):
                        st.session_state.user_query = entry['natural_language']
                        st.rerun()
                
                with col3:
                    if st.button("🗑️ Delete", key=f"del_{actual_idx}"):
                        delete_history_entry(actual_idx)
                        st.rerun()
                
                # Display queries
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("**SQL Query:**")
                    if entry.get('sql'):
                        st.code(entry['sql'], language="sql")
                    else:
                        st.text("N/A")
                
                with col2:
                    st.markdown("**MongoDB Query:**")
                    if entry.get('mongodb'):
                        st.code(entry['mongodb'], language="javascript")
                    else:
                        st.text("N/A")
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666; padding: 2rem;'>
        <p>NoNoQL - Natural Language to Query Generator</p>
        <p>Powered by T5 Transformer Models | Built with Streamlit</p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
