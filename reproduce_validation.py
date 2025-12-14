from ui import helpers
import re

print("--- Testing Validation Logic ---")

# 1. Flowchart Error: Expecting 'SQE'... got 'PS'
flowchart_code = """flowchart TD
  start[Customer PO (from SAP/USA)] --> """

print("\n1. Flowchart Code:")
print(flowchart_code)
errors = helpers.validate_mermaid_syntax(flowchart_code)
print("Errors found:", errors)

# 2. ER Diagram Error: Expecting 'ATTRIBUTE_WORD', got 'ATTRIBUTE_KEY'
er_code = """erDiagram
    Packing_WCID FK        VARCHAR S"""

print("\n2. ER Code:")
print(er_code)
errors = helpers.validate_mermaid_syntax(er_code)
print("Errors found:", errors)

# 3. Mindmap Error: Expecting 'SPACELINE', 'NL', 'EOF', got 'NODE_ID'
# ...on, Finishing Lines)"        "Work Orde
mindmap_code = """mindmap
  root(("Garment Factory"))
    Branch1("Work Centers (Sewing, Decoration, Finishing Lines)")        "Work Orde"""

print("\n3. Mindmap Code:")
print(mindmap_code)
errors = helpers.validate_mermaid_syntax(mindmap_code)
print("Errors found:", errors)

# Test Regex isolation
print("\n--- Regex Testing ---")
line = '    Branch1("Work Centers (Sewing, Decoration, Finishing Lines)")        "Work Orde'
print(f"Testing line: '{line}'")
match = re.search(r'[\]\)\}][\t ]*\S', line)
print(f"Match found: {match}")
