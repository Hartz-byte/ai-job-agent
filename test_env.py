import sys
import os

print("Python Environment Test")
print("=" * 50)
print(f"Python Version: {sys.version}")
print(f"Current Working Directory: {os.getcwd()}")
print(f"Python Path: {sys.path}")

print("\nTesting imports...")
try:
    import docx
    print("✅ python-docx is installed")
except ImportError as e:
    print(f"❌ python-docx is not installed: {e}")

try:
    from src.llm import get_llm
    print("✅ Successfully imported get_llm from src.llm")
    
    llm = get_llm()
    response = llm.generate("Say 'Hello, World!'")
    print(f"✅ Got response from LLM: {response[:100]}...")
    
except Exception as e:
    print(f"❌ Error: {str(e)}")
    import traceback
    traceback.print_exc()
