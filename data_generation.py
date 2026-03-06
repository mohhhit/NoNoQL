"""
Synthetic Data Generation for NL-to-SQL/MongoDB Query Translation
This script generates paired natural language queries with their corresponding
SQL and MongoDB statements for CRUD operations.
"""

import json
import random
from typing import List, Dict
import pandas as pd
from faker import Faker

fake = Faker()

# Database schema for an Industry/Company context
TABLES = {
    "employees": {
        "columns": ["employee_id", "name", "email", "department", "salary", "hire_date", "age"],
        "types": {"employee_id": "int", "name": "str", "email": "str", "department": "str", "salary": "float", "hire_date": "date", "age": "int"}
    },
    "departments": {
        "columns": ["department_id", "department_name", "manager_id", "budget", "location"],
        "types": {"department_id": "int", "department_name": "str", "manager_id": "int", "budget": "float", "location": "str"}
    },
    "projects": {
        "columns": ["project_id", "project_name", "start_date", "end_date", "budget", "status"],
        "types": {"project_id": "int", "project_name": "str", "start_date": "date", "end_date": "date", "budget": "float", "status": "str"}
    },
    "orders": {
        "columns": ["order_id", "customer_name", "product_name", "quantity", "order_date", "total_amount"],
        "types": {"order_id": "int", "customer_name": "str", "product_name": "str", "quantity": "int", "order_date": "date", "total_amount": "float"}
    },
    "products": {
        "columns": ["product_id", "product_name", "category", "price", "stock_quantity", "supplier"],
        "types": {"product_id": "int", "product_name": "str", "category": "str", "price": "float", "stock_quantity": "int", "supplier": "str"}
    }
}

# Collection names for MongoDB (similar to table names)
COLLECTIONS = list(TABLES.keys())


class QueryGenerator:
    """Generate NL queries with corresponding SQL and MongoDB statements"""
    
    def __init__(self):
        self.departments = ["Engineering", "Sales", "Marketing", "HR", "Finance", "Operations"]
        self.statuses = ["Active", "Completed", "Pending", "Cancelled"]
        self.categories = ["Electronics", "Furniture", "Office Supplies", "Software", "Hardware"]
        
    def generate_select_queries(self, num_samples: int = 100) -> List[Dict]:
        """Generate SELECT/FIND queries"""
        queries = []
        templates = [
            # Simple SELECT queries
            {
                "nl": "Show all {table}",
                "sql": "SELECT * FROM {table};",
                "mongodb": "db.{table}.find({{}})"
            },
            {
                "nl": "Get all {column} from {table}",
                "sql": "SELECT {column} FROM {table};",
                "mongodb": "db.{table}.find({{}}, {{{column}: 1}})"
            },
            {
                "nl": "Find {table} where {column} is {value}",
                "sql": "SELECT * FROM {table} WHERE {column} = '{value}';",
                "mongodb": "db.{table}.find({{{column}: '{value}'}})"
            },
            {
                "nl": "Show {table} with {column} greater than {number}",
                "sql": "SELECT * FROM {table} WHERE {column} > {number};",
                "mongodb": "db.{table}.find({{{column}: {{$gt: {number}}}}})"
            },
            {
                "nl": "Get top {limit} {table} ordered by {column}",
                "sql": "SELECT * FROM {table} ORDER BY {column} DESC LIMIT {limit};",
                "mongodb": "db.{table}.find({{}}).sort({{{column}: -1}}).limit({limit})"
            },
            {
                "nl": "Count all {table}",
                "sql": "SELECT COUNT(*) FROM {table};",
                "mongodb": "db.{table}.countDocuments({{}})"
            },
            {
                "nl": "Find {table} where {column} contains {search_term}",
                "sql": "SELECT * FROM {table} WHERE {column} LIKE '%{search_term}%';",
                "mongodb": "db.{table}.find({{{column}: {{$regex: '{search_term}', $options: 'i'}}}})"
            },
            {
                "nl": "Show average {numeric_column} from {table}",
                "sql": "SELECT AVG({numeric_column}) FROM {table};",
                "mongodb": "db.{table}.aggregate([{{$group: {{_id: null, avg: {{$avg: '${numeric_column}'}}}}}}])"
            }
        ]
        
        for _ in range(num_samples):
            template = random.choice(templates)
            table = random.choice(list(TABLES.keys()))
            columns = TABLES[table]["columns"]
            
            # Get numeric and string columns
            numeric_cols = [c for c in columns if TABLES[table]["types"][c] in ["int", "float"]]
            string_cols = [c for c in columns if TABLES[table]["types"][c] == "str"]
            
            column = random.choice(columns)
            numeric_column = random.choice(numeric_cols) if numeric_cols else column
            
            # Fill template placeholders
            params = {
                "table": table,
                "column": column,
                "numeric_column": numeric_column,
                "value": self._get_sample_value(table, column),
                "number": random.randint(1000, 100000),
                "limit": random.randint(5, 50),
                "search_term": fake.word()
            }
            
            query = {
                "natural_language": template["nl"].format(**params),
                "sql": template["sql"].format(**params),
                "mongodb": template["mongodb"].format(**params),
                "operation": "READ"
            }
            queries.append(query)
        
        return queries
    
    def generate_insert_queries(self, num_samples: int = 100) -> List[Dict]:
        """Generate INSERT queries"""
        queries = []
        
        for _ in range(num_samples):
            table = random.choice(list(TABLES.keys()))
            columns = TABLES[table]["columns"]
            
            # Generate sample values
            values = {}
            for col in columns:
                values[col] = self._get_sample_value(table, col)
            
            # Create natural language
            nl = f"Insert a new {table[:-1]} with " + ", ".join([f"{col} as {values[col]}" for col in columns[:3]])
            
            # Create SQL
            cols_str = ", ".join(columns)
            vals_str = ", ".join([f"'{v}'" if isinstance(v, str) else str(v) for v in values.values()])
            sql = f"INSERT INTO {table} ({cols_str}) VALUES ({vals_str});"
            
            # Create MongoDB
            mongodb_doc = json.dumps(values, indent=2)
            mongodb = f"db.{table}.insertOne({mongodb_doc})"
            
            query = {
                "natural_language": nl,
                "sql": sql,
                "mongodb": mongodb,
                "operation": "CREATE"
            }
            queries.append(query)
        
        return queries
    
    def generate_update_queries(self, num_samples: int = 100) -> List[Dict]:
        """Generate UPDATE queries"""
        queries = []
        templates = [
            {
                "nl": "Update {table} set {update_column} to {new_value} where {condition_column} is {condition_value}",
                "sql": "UPDATE {table} SET {update_column} = '{new_value}' WHERE {condition_column} = '{condition_value}';",
                "mongodb": "db.{table}.updateMany({{{condition_column}: '{condition_value}'}}, {{$set: {{{update_column}: '{new_value}'}}}})"
            },
            {
                "nl": "Change {update_column} to {new_value} for all {table}",
                "sql": "UPDATE {table} SET {update_column} = '{new_value}';",
                "mongodb": "db.{table}.updateMany({{}}, {{$set: {{{update_column}: '{new_value}'}}}})"
            },
            {
                "nl": "Increase {numeric_column} by {increment} in {table} where {condition_column} equals {condition_value}",
                "sql": "UPDATE {table} SET {numeric_column} = {numeric_column} + {increment} WHERE {condition_column} = '{condition_value}';",
                "mongodb": "db.{table}.updateMany({{{condition_column}: '{condition_value}'}}, {{$inc: {{{numeric_column}: {increment}}}}})"
            }
        ]
        
        for _ in range(num_samples):
            template = random.choice(templates)
            table = random.choice(list(TABLES.keys()))
            columns = TABLES[table]["columns"]
            
            numeric_cols = [c for c in columns if TABLES[table]["types"][c] in ["int", "float"]]
            
            update_column = random.choice(columns)
            condition_column = random.choice(columns)
            numeric_column = random.choice(numeric_cols) if numeric_cols else update_column
            
            params = {
                "table": table,
                "update_column": update_column,
                "condition_column": condition_column,
                "numeric_column": numeric_column,
                "new_value": self._get_sample_value(table, update_column),
                "condition_value": self._get_sample_value(table, condition_column),
                "increment": random.randint(100, 5000)
            }
            
            query = {
                "natural_language": template["nl"].format(**params),
                "sql": template["sql"].format(**params),
                "mongodb": template["mongodb"].format(**params),
                "operation": "UPDATE"
            }
            queries.append(query)
        
        return queries
    
    def generate_delete_queries(self, num_samples: int = 100) -> List[Dict]:
        """Generate DELETE queries"""
        queries = []
        templates = [
            {
                "nl": "Delete all {table}",
                "sql": "DELETE FROM {table};",
                "mongodb": "db.{table}.deleteMany({{}})"
            },
            {
                "nl": "Remove {table} where {column} is {value}",
                "sql": "DELETE FROM {table} WHERE {column} = '{value}';",
                "mongodb": "db.{table}.deleteMany({{{column}: '{value}'}})"
            },
            {
                "nl": "Delete {table} with {numeric_column} less than {number}",
                "sql": "DELETE FROM {table} WHERE {numeric_column} < {number};",
                "mongodb": "db.{table}.deleteMany({{{numeric_column}: {{$lt: {number}}}}})"
            }
        ]
        
        for _ in range(num_samples):
            template = random.choice(templates)
            table = random.choice(list(TABLES.keys()))
            columns = TABLES[table]["columns"]
            
            numeric_cols = [c for c in columns if TABLES[table]["types"][c] in ["int", "float"]]
            column = random.choice(columns)
            numeric_column = random.choice(numeric_cols) if numeric_cols else column
            
            params = {
                "table": table,
                "column": column,
                "numeric_column": numeric_column,
                "value": self._get_sample_value(table, column),
                "number": random.randint(1000, 50000)
            }
            
            query = {
                "natural_language": template["nl"].format(**params),
                "sql": template["sql"].format(**params),
                "mongodb": template["mongodb"].format(**params),
                "operation": "DELETE"
            }
            queries.append(query)
        
        return queries
    
    def _get_sample_value(self, table: str, column: str):
        """Generate sample values based on column type"""
        col_type = TABLES[table]["types"][column]
        
        if col_type == "int":
            return random.randint(1, 10000)
        elif col_type == "float":
            return round(random.uniform(1000, 100000), 2)
        elif col_type == "date":
            return fake.date_between(start_date='-5y', end_date='today').strftime('%Y-%m-%d')
        elif col_type == "str":
            if "name" in column.lower():
                return fake.name()
            elif "email" in column.lower():
                return fake.email()
            elif "department" in column.lower():
                return random.choice(self.departments)
            elif "status" in column.lower():
                return random.choice(self.statuses)
            elif "category" in column.lower():
                return random.choice(self.categories)
            elif "location" in column.lower():
                return fake.city()
            elif "supplier" in column.lower():
                return fake.company()
            else:
                return fake.word()
        return "value"


def generate_dataset(total_samples: int = 5000):
    """Generate complete dataset with all CRUD operations"""
    generator = QueryGenerator()
    
    # Generate balanced dataset
    samples_per_operation = total_samples // 4
    
    print(f"Generating {samples_per_operation} SELECT queries...")
    select_queries = generator.generate_select_queries(samples_per_operation)
    
    print(f"Generating {samples_per_operation} INSERT queries...")
    insert_queries = generator.generate_insert_queries(samples_per_operation)
    
    print(f"Generating {samples_per_operation} UPDATE queries...")
    update_queries = generator.generate_update_queries(samples_per_operation)
    
    print(f"Generating {samples_per_operation} DELETE queries...")
    delete_queries = generator.generate_delete_queries(samples_per_operation)
    
    # Combine all queries
    all_queries = select_queries + insert_queries + update_queries + delete_queries
    random.shuffle(all_queries)
    
    # Create DataFrame
    df = pd.DataFrame(all_queries)
    
    print(f"\nGenerated {len(df)} total queries")
    print(f"Operations distribution:\n{df['operation'].value_counts()}")
    
    return df


def save_dataset(df: pd.DataFrame, output_dir: str = "data"):
    """Save dataset in multiple formats"""
    import os
    os.makedirs(output_dir, exist_ok=True)
    
    # Save as CSV
    csv_path = os.path.join(output_dir, "training_data.csv")
    df.to_csv(csv_path, index=False)
    print(f"Saved CSV to {csv_path}")
    
    # Save as JSON
    json_path = os.path.join(output_dir, "training_data.json")
    df.to_json(json_path, orient="records", indent=2)
    print(f"Saved JSON to {json_path}")
    
    # Split into train/val/test
    train_size = int(0.8 * len(df))
    val_size = int(0.1 * len(df))
    
    train_df = df[:train_size]
    val_df = df[train_size:train_size + val_size]
    test_df = df[train_size + val_size:]
    
    train_df.to_csv(os.path.join(output_dir, "train.csv"), index=False)
    val_df.to_csv(os.path.join(output_dir, "val.csv"), index=False)
    test_df.to_csv(os.path.join(output_dir, "test.csv"), index=False)
    
    print(f"\nDataset split:")
    print(f"Train: {len(train_df)} samples")
    print(f"Validation: {len(val_df)} samples")
    print(f"Test: {len(test_df)} samples")


if __name__ == "__main__":
    # Generate dataset
    df = generate_dataset(total_samples=5000)
    
    # Save dataset
    save_dataset(df)
    
    # Display sample
    print("\n=== Sample Queries ===")
    for idx, row in df.head(3).iterrows():
        print(f"\n{idx + 1}. Natural Language: {row['natural_language']}")
        print(f"   SQL: {row['sql']}")
        print(f"   MongoDB: {row['mongodb']}")
        print(f"   Operation: {row['operation']}")
