"""
Inference script for TexQL models
Use this script to generate queries from the command line
"""

import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import argparse
import json
import re


def extract_columns_from_nl(natural_language_query):
    """Extract table name and column names from natural language query"""
    nl = natural_language_query.lower().strip()
    
    # Extract table name
    table_match = re.search(r'(?:table|collection)\s+(?:named|called)?\s*(\w+)', nl)
    table_name = table_match.group(1) if table_match else None
    
    # Extract column names
    columns = []
    col_match = re.search(r'columns?\s+(?:as|named|like|called)?\s*([^,]+(?:,\s*[^,]+)*)', nl)
    if col_match:
        col_text = col_match.group(1)
        columns = re.split(r',|\s+and\s+', col_text)
        columns = [c.strip() for c in columns if c.strip()]
    
    if not columns:
        col_match = re.search(r'(?:add|with)\s+(?:columns?)?\s*([^,]+(?:,\s*[^,]+)*)', nl)
        if col_match:
            col_text = col_match.group(1)
            columns = re.split(r',|\s+and\s+', col_text)
            columns = [c.strip() for c in columns if c.strip()]
    
    return table_name, columns


def fix_create_table_sql(generated_sql, table_name, requested_columns):
    """Replace hallucinated columns with actual requested columns in CREATE TABLE"""
    if not table_name or not requested_columns:
        return generated_sql
    
    if not re.search(r'CREATE\s+TABLE', generated_sql, re.IGNORECASE):
        return generated_sql
    
    def infer_type(col_name):
        col_lower = col_name.lower()
        if 'id' in col_lower:
            return 'INT PRIMARY KEY'
        elif any(word in col_lower for word in ['name', 'title', 'description']):
            return 'VARCHAR(100)'
        elif 'email' in col_lower:
            return 'VARCHAR(100)'
        elif any(word in col_lower for word in ['phone', 'contact', 'mobile']):
            return 'VARCHAR(20)'
        elif any(word in col_lower for word in ['date', 'created', 'updated']):
            return 'DATE'
        elif any(word in col_lower for word in ['price', 'salary', 'amount']):
            return 'DECIMAL(10,2)'
        elif any(word in col_lower for word in ['age', 'quantity', 'count']):
            return 'INT'
        else:
            return 'VARCHAR(100)'
    
    col_defs = []
    for col in requested_columns:
        col_clean = col.strip()
        if col_clean:
            col_type = infer_type(col_clean)
            col_defs.append(f"{col_clean} {col_type}")
    
    new_sql = re.sub(
        r'(CREATE\s+TABLE\s+' + re.escape(table_name) + r'\s*\()[^)]+(\))',
        r'\1' + ', '.join(col_defs) + r'\2',
        generated_sql,
        flags=re.IGNORECASE
    )
    
    return new_sql


def fix_create_collection_mongo(generated_mongo, table_name, requested_columns):
    """Fix MongoDB createCollection to use correct collection name and sample document"""
    if not table_name:
        return generated_mongo
    
    if not any(word in generated_mongo.lower() for word in ['create', 'insert']):
        return generated_mongo
    
    doc_fields = []
    for col in requested_columns:
        col_clean = col.strip()
        if col_clean:
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
    
    if doc_fields:
        fixed_mongo = f"db.{table_name}.insertOne({{{', '.join(doc_fields)}}});"
    else:
        fixed_mongo = f"db.createCollection('{table_name}');"
    
    return fixed_mongo


class TexQLInference:
    """Standalone inference class for unified TexQL model"""
    
    def __init__(self, model_path):
        """
        Initialize the inference engine
        
        Args:
            model_path: Path to the trained model directory
        """
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
        print(f"Loading TexQL model from {model_path}...")
        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        self.model = AutoModelForSeq2SeqLM.from_pretrained(model_path)
        self.model.to(self.device)
        self.model.eval()
        print(f"Model loaded on {self.device}")
        print("This model can generate both SQL and MongoDB queries\n")
    
    def generate_query(
        self,
        natural_language_query,
        target_type='sql',
        max_length=512,
        num_beams=10,
        temperature=0.3,
        repetition_penalty=1.2,
        length_penalty=0.8
    ):
        """
        Generate SQL or MongoDB query from natural language
        
        Args:
            natural_language_query: Natural language input
            target_type: 'sql' or 'mongodb'
            max_length: Maximum length of generated query
            num_beams: Number of beams for beam search
            temperature: Sampling temperature (lower = more focused)
            repetition_penalty: Penalty for repeating tokens (>1.0 discourages repetition)
            length_penalty: Penalty for length (<1.0 encourages shorter outputs)
        
        Returns:
            Generated query string
        """
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
                max_length=max_length,
                num_beams=num_beams,
                temperature=temperature,
                repetition_penalty=repetition_penalty,
                length_penalty=length_penalty,
                no_repeat_ngram_size=3,
                early_stopping=True,
                do_sample=False  # Use beam search for more deterministic output
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
        
        return generated_query
    
    def batch_generate(self, queries, target_type='sql', **kwargs):
        """
        Generate queries for multiple inputs
        
        Args:
            queries: List of natural language queries
            target_type: 'sql' or 'mongodb'
            **kwargs: Generation parameters
        
        Returns:
            List of generated queries
        """
        results = []
        for query in queries:
            result = self.generate_query(query, target_type=target_type, **kwargs)
            results.append(result)
        return results


def main():
    """Command-line interface"""
    parser = argparse.ArgumentParser(description="TexQL Query Generator")
    
    parser.add_argument(
        "--model-path",
        type=str,
        required=True,
        help="Path to the trained model"
    )
    
    parser.add_argument(
        "--type",
        type=str,
        choices=['sql', 'mongodb', 'both'],
        default='sql',
        help="Query type to generate (sql, mongodb, or both)"
    )
    
    parser.add_argument(
        "--query",
        type=str,
        help="Natural language query to translate"
    )
    
    parser.add_argument(
        "--file",
        type=str,
        help="File containing queries (one per line)"
    )
    
    parser.add_argument(
        "--output",
        type=str,
        help="Output file for results (JSON format)"
    )
    
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.3,  # ✅ Lower default = less hallucination
        help="Sampling temperature (lower = more focused, higher = more creative)"
    )
    
    parser.add_argument(
        "--num-beams",
        type=int,
        default=10,  # ✅ Higher value = more accurate results
        help="Number of beams for beam search (higher = more accurate, recommended: 10)"
    )
    
    parser.add_argument(
        "--repetition-penalty",
        type=float,
        default=1.2,  # ✅ Discourages adding extra unwanted columns
        help="Repetition penalty (>1.0 discourages repetition)"
    )
    
    parser.add_argument(
        "--length-penalty",
        type=float,
        default=0.8,  # ✅ Prefer shorter outputs
        help="Length penalty (<1.0 = prefer shorter, >1.0 = prefer longer)"
    )
    
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Run in interactive mode"
    )
    
    args = parser.parse_args()
    
    # Load model
    inference_engine = TexQLInference(args.model_path)
    
    # Interactive mode
    if args.interactive:
        print(f"\n{'='*60}")
        if args.type == 'both':
            print(f"TexQL Interactive Mode - SQL & MongoDB")
        else:
            print(f"TexQL Interactive Mode - {args.type.upper()}")
        print(f"{'='*60}")
        print("Enter your queries (type 'exit' to quit)\n")
        
        while True:
            try:
                query = input("Natural Language Query: ").strip()
                
                if query.lower() in ['exit', 'quit', 'q']:
                    print("Goodbye!")
                    break
                
                if not query:
                    continue
                
                if args.type == 'both':
                    # Generate both SQL and MongoDB
                    print("\nGenerating SQL...")
                    sql_result = inference_engine.generate_query(
                        query,
                        target_type='sql',
                        temperature=args.temperature,
                        num_beams=args.num_beams,
                        repetition_penalty=args.repetition_penalty,
                        length_penalty=args.length_penalty
                    )
                    print(f"Generated SQL: {sql_result}")
                    
                    print("\nGenerating MongoDB...")
                    mongo_result = inference_engine.generate_query(
                        query,
                        target_type='mongodb',
                        temperature=args.temperature,
                        num_beams=args.num_beams,
                        repetition_penalty=args.repetition_penalty,
                        length_penalty=args.length_penalty
                    )
                    print(f"Generated MongoDB: {mongo_result}")
                else:
                    # Generate single type
                    result = inference_engine.generate_query(
                        query,
                        target_type=args.type,
                        temperature=args.temperature,
                        num_beams=args.num_beams,
                        repetition_penalty=args.repetition_penalty,
                        length_penalty=args.length_penalty
                    )
                
                print(f"\nGenerated {args.type.upper()}: {result}\n")
                print("-" * 60)
            
            except KeyboardInterrupt:
                print("\nGoodbye!")
                break
    
    # Single query mode
    elif args.query:
        if args.type == 'both':
            # Generate both
            sql_result = inference_engine.generate_query(
                args.query,
                target_type='sql',
                temperature=args.temperature,
                num_beams=args.num_beams,
                repetition_penalty=args.repetition_penalty,
                length_penalty=args.length_penalty
            )
            mongo_result = inference_engine.generate_query(
                args.query,
                target_type='mongodb',
                temperature=args.temperature,
                num_beams=args.num_beams,
                repetition_penalty=args.repetition_penalty,
                length_penalty=args.length_penalty
            )
            
            print(f"\nInput: {args.query}")
            print(f"SQL Output: {sql_result}")
            print(f"MongoDB Output: {mongo_result}\n")
            
            if args.output:
                output_data = {
                    "input": args.query,
                    "sql": sql_result,
                    "mongodb": mongo_result
                }
                with open(args.output, 'w') as f:
                    json.dump(output_data, f, indent=2)
                print(f"Result saved to {args.output}")
        else:
            # Generate single type
            result = inference_engine.generate_query(
                args.query,
                target_type=args.type,
                temperature=args.temperature,
                num_beams=args.num_beams,
                repetition_penalty=args.repetition_penalty,
                length_penalty=args.length_penalty
            )
            
            print(f"\nInput: {args.query}")
            print(f"Output: {result}\n")
            
            if args.output:
                output_data = {
                    "input": args.query,
                    "output": result,
                    "type": args.type
                }
                with open(args.output, 'w') as f:
                    json.dump(output_data, f, indent=2)
                print(f"Result saved to {args.output}")
    
    # Batch mode from file
    elif args.file:
        with open(args.file, 'r') as f:
            queries = [line.strip() for line in f if line.strip()]
        
        print(f"Processing {len(queries)} queries...")
        
        if args.type == 'both':
            # Generate both SQL and MongoDB for each query
            output_data = []
            for query in queries:
                sql_result = inference_engine.generate_query(
                    query,
                    target_type='sql',
                    temperature=args.temperature,
                    num_beams=args.num_beams
                )
                mongo_result = inference_engine.generate_query(
                    query,
                    target_type='mongodb',
                    temperature=args.temperature,
                    num_beams=args.num_beams
                )
                
                print(f"\nInput: {query}")
                print(f"SQL: {sql_result}")
                print(f"MongoDB: {mongo_result}")
                print("-" * 60)
                
                output_data.append({
                    "input": query,
                    "sql": sql_result,
                    "mongodb": mongo_result
                })
        else:
            # Generate single type for each query
            results = inference_engine.batch_generate(
                queries,
                target_type=args.type,
                temperature=args.temperature,
                num_beams=args.num_beams
            )
            
            output_data = []
            for query, result in zip(queries, results):
                print(f"\nInput: {query}")
                print(f"Output: {result}")
                print("-" * 60)
                
                output_data.append({
                    "input": query,
                    "output": result,
                    "type": args.type
                })
        
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(output_data, f, indent=2)
            print(f"\nResults saved to {args.output}")
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
