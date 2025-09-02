import sys
import os

# Add src directory to Python path
sys.path.insert(0, os.path.abspath('.'))

print("Testing imports...")
try:
    from src.llm import get_llm
    print("✅ Successfully imported get_llm")
    
    print("✅ Successfully imported LocalMistral")
    
    llm = get_llm()
    print("✅ Successfully created LLM instance")
    
    response = llm.generate("Say 'Hello, World!'")
    print("✅ Successfully got response from LLM:")
    print(response)
    
except Exception as e:
    print("❌ Error:", str(e))
    import traceback
    traceback.print_exc()
