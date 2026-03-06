"""
Quick Training Test
Test training with just 10 samples to verify everything works
Run this before starting full training
"""

import torch
import pandas as pd
from train_local import TexQLTrainer

def main():
    print("="*60)
    print("Quick Training Test")
    print("="*60)
    print("\nThis will test training with 10 samples")
    print("Should take ~2-3 minutes")
    print("="*60)
    
    # Check if data exists
    try:
        train_df = pd.read_csv('data/train.csv')
        val_df = pd.read_csv('data/val.csv')
        
        # Take only 10 samples
        train_df = train_df.head(10)
        val_df = val_df.head(5)
        
        # Save mini dataset
        train_df.to_csv('data/train_mini.csv', index=False)
        val_df.to_csv('data/val_mini.csv', index=False)
        
        print(f"\n✅ Created mini dataset:")
        print(f"   Train: {len(train_df)} samples")
        print(f"   Val: {len(val_df)} samples")
        
    except FileNotFoundError:
        print("\n❌ Training data not found!")
        print("Run: python data_generation.py")
        return
    
    # Initialize trainer
    print("\n" + "="*60)
    print("Initializing Trainer")
    print("="*60)
    
    trainer = TexQLTrainer(
        target_type='sql',
        model_name='google/flan-t5-small'
    )
    
    # Load mini data
    trainer.train_df = pd.read_csv('data/train_mini.csv')
    trainer.val_df = pd.read_csv('data/val_mini.csv')
    trainer.test_df = val_df  # Use val as test
    
    print(f"\n✅ Mini dataset loaded")
    
    # Prepare and tokenize
    trainer.prepare_datasets()
    trainer.load_model()
    trainer.tokenize_datasets()
    
    # Setup training with just 2 epochs
    trainer.setup_training(
        output_dir='./models/test_training',
        num_epochs=2,
        batch_size=2
    )
    
    print("\n" + "="*60)
    print("Starting Test Training (2 epochs)")
    print("="*60)
    print("\nWatch for:")
    print("  ✅ Loss should decrease (not stay at 0.0)")
    print("  ✅ Learning rate should be > 0")
    print("  ✅ Grad norm should be a number (not NaN)")
    print("="*60)
    
    # Train
    try:
        trainer.train()
        
        print("\n" + "="*60)
        print("Test Training Complete!")
        print("="*60)
        
        # Test generation
        print("\n" + "="*60)
        print("Testing Generation")
        print("="*60)
        
        test_query = "Show all employees"
        result = trainer.generate_query(test_query)
        
        print(f"\nInput: {test_query}")
        print(f"Output: {result}")
        
        if result and len(result) > 0:
            print("\n✅ Model is working!")
            print("\nvYou can now run full training:")
            print("  python train_local.py --target sql --epochs 10")
        else:
            print("\n⚠️  Model generated empty output")
            print("This might be normal for only 2 epochs")
            print("Try full training anyway")
        
    except Exception as e:
        print(f"\n❌ Training failed: {e}")
        import traceback
        traceback.print_exc()
        
        print("\n💡 If you see 'CUDA out of memory':")
        print("  Try: --batch-size 1")
        
    # Cleanup
    import os
    import shutil
    if os.path.exists('models/test_training'):
        shutil.rmtree('models/test_training', ignore_errors=True)
        print("\n✅ Cleaned up test files")

if __name__ == "__main__":
    main()
