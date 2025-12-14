from ui import helpers
import re

print("--- Testing Multiple Diagram Errors ---")

# 1. Mindmap: Nested parens not caught?
# Error: Parse error on line 6: ...Garment Production (Cutting,Sewing,...))
mindmap_snippet = """mindmap
  root((Garment Factory))
     Garment Production (Cutting,Sewing,...)""" 
# Note: Indentation might vary. The previous regex assumed specific indentation structure?
# Let's test with various indentations.

# 2. ER Diagram: Inline comment fail
# Error: string type %% RawMaterial ... Expecting ... got '%'
er_snippet = """erDiagram
    Item {
        string type %% RawMaterial, FBB,
        int id
    }"""

# 3. Flowchart: Parse error ... code]
# Error: ...erial to Production (Barcode Scan)] ... Expecting 'SQE'...
flowchart_snippet = """flowchart TD
    A[Material to Production (Barcode Scan)]    """ 
# The capturing might fail if there's trailing whitespace or if ( ) inside [] isn't quoted? 
# Mermaid actually allows () inside [] without quotes usually, but let's see.

# 4. Sequence: Inactive participant + comment
# Error: Trying to inactivate an inactive participant (Odoo %% Deactivating...)
seq_snippet = """sequenceDiagram
    participant Odoo
    activate Odoo
    Odoo->>User: Done
    deactivate Odoo %% Deactivating Odoo for the activate statement above"""

def test_fixer(name, code):
    print(f"\n--- Testing {name} ---")
    print(f"Original:\n{code}")
    fixed = helpers.fix_mermaid_syntax(code)
    print(f"Fixed:\n{fixed}")
    if fixed == code:
        print("[NO CHANGE]")
    else:
        print("[FIXED]")
    return fixed

test_fixer("Mindmap", mindmap_snippet)
# Check output for 2nd line specifically
test_fixer("ER Diagram", er_snippet)
test_fixer("Flowchart", flowchart_snippet)
test_fixer("Sequence", seq_snippet)
