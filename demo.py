"""
Demo script to test the trained TexQL model
Run this to verify your trained model is working correctly
"""

import os
import sys
from inference import TexQLInference

def print_separator(char="=", length=70):
    print(char * length)

def print_result(nl_query, sql_query, mongo_query):
    """Print query results in a formatted way"""
    print(f"\n📝 Natural Language:")
    print(f"   {nl_query}")
    print(f"\n💾 SQL Query:")
    print(f"   {sql_query}")
    print(f"\n🍃 MongoDB Query:")
    print(f"   {mongo_query}")
    print()

def main():
    print_separator()
    print("🔍 TexQL Model Demo")
    print_separator()
    
    # Check if model exists
    model_path = "models"
    if not os.path.exists(model_path):
        print(f"\n❌ Error: Model not found at '{model_path}'")
        print("\nPlease train the model first:")
        print("1. Generate data: python data_generation.py")
        print("2. Train on Colab: Upload training_colab_balanced.ipynb")
        print("3. Download trained model to 'models/' directory")
        print_separator()
        return
    
    # Load model
    print("\n🔄 Loading trained model...")
    try:
        model = TexQLInference(model_path)
    except Exception as e:
        print(f"\n❌ Error loading model: {e}")
        print_separator()
        return
    
    print("✅ Model loaded successfully!")
    
    # Test queries - covering all CRUD operations
    test_queries = [
        # READ operations
        "Show me all employees",
        "Get employees in the sales department",
        "Find employee with ID 101",
        
        # CREATE operations
        "Create a table named Students with columns as ID, name, email, age",
        "Add a new employee named John with email john@example.com",
        
        # UPDATE operations
        "Update the salary of employee ID 105 to 75000",
        "Change the department to Marketing for employee named Alice",
        
        # DELETE operations
        "Delete employee with ID 203",
        "Remove all employees from IT department"
    ]
    
    print_separator()
    print("📊 Testing Model with Sample Queries")
    print_separator()
    
    # Run inference on each query
    for i, query in enumerate(test_queries, 1):
        print(f"\n🔹 Test {i}/{len(test_queries)}")
        print_separator("-")
        
        try:
            # Generate both SQL and MongoDB
            sql_query = model.generate_query(query, target_type='sql')
            mongo_query = model.generate_query(query, target_type='mongodb')
            
            print_result(query, sql_query, mongo_query)
            
        except Exception as e:
            print(f"❌ Error generating query: {e}\n")
            continue
    
    print_separator()
    print("✅ Demo completed successfully!")
    print_separator()
    print("\n💡 Next steps:")
    print("1. Run the Streamlit app: python -m streamlit run app.py")
    print("2. Use CLI tool: python inference.py --query 'your query here'")
    print("3. Test with your own queries!")
    print_separator()

if __name__ == "__main__":
    main()
