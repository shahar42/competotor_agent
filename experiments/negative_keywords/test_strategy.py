import sys
import os
import json
from dataclasses import dataclass

# Add project root to python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from llm.client import GeminiClient

# Mocking a new extraction logic here to test the prompt
def extract_concepts_experimental(client, user_description):
    prompt = f"""
    You are an expert product analyst. Analyze the user's product idea and extract key information for searching.
    
    Crucial: Identify "Negative Keywords". These are terms that often appear in similar BUT WRONG contexts.
    For example:
    - If idea is "Cat Sleep Collar", negative keywords: ["dog", "bark", "training", "shock"] (to avoid dog collars or shock collars)
    - If idea is "Surfboard Lamp", negative keywords: ["wax", "leash", "fin", "repair"] (to avoid surfboard accessories)

    User Idea: "{user_description}"

    Return strictly valid JSON in this format:
    {{
        "core_function": "...",
        "search_keywords": ["term1", "term2", "term3"],
        "negative_keywords": ["neg1", "neg2", "neg3", "neg4"],
        "category": "..."
    }}
    """
    
    response = client.generate(prompt)
    
    # Simple cleanup
    clean = response.strip()
    if clean.startswith("```json"): clean = clean[7:]
    if clean.startswith("```"): clean = clean[3:]
    if clean.endswith("```"): clean = clean[:-3]
    
    try:
        return json.loads(clean)
    except Exception as e:
        return {"error": str(e), "raw": response}

def run_test():
    client = GeminiClient()
    
    test_cases = [
        "A smart collar for cats that tracks their sleep quality and health vitals.",
        "A table lamp made from a recycled surfboard.",
        "An app that helps people find pickup basketball games nearby."
    ]

    print("--- STARTING NEGATIVE KEYWORD EXPERIMENT ---\\n")

    for i, idea in enumerate(test_cases, 1):
        print(f"TEST CASE {i}: {idea}")
        print("-" * 50)
        
        result = extract_concepts_experimental(client, idea)
        
        if "error" in result:
            print(f"ERROR: {result['error']}")
        else:
            print(f"Category: {result.get('category')}")
            print(f"Search Keywords: {result.get('search_keywords')}")
            print(f"Negative Keywords: {result.get('negative_keywords')}")
            
            # Analysis of the result
            negatives = result.get('negative_keywords', [])
            print(f"\nAnalysis:")
            if not negatives:
                print("-> FAIL: No negative keywords generated.")
            else:
                print(f"-> generated {len(negatives)} negative terms.")
                
        print("\n" + "="*60 + "\n")

if __name__ == "__main__":
    run_test()
