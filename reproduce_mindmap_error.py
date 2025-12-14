from ui import helpers
import re

print("--- Testing Mindmap Nested Parentheses Logic ---")

# The problematic code snippet
mindmap_code = """mindmap
  root(("Garment Factory"))
    Process(Garment Production (Cutting,Sewing,...))
    OtherNode("Correct Node")"""

print("\nInput Code:")
print(mindmap_code)

# 1. Test Validator
errors = helpers.validate_mermaid_syntax(mindmap_code)
print("\nValidation Errors:", errors)

# 2. Test Regex Auto-Fix Logic
# We want to transform: Process(Garment Production (Cutting,Sewing,...))
# To: Process("Garment Production (Cutting,Sewing,...)")

print("\n--- Testing Regex Fixer ---")
lines = mindmap_code.split('\n')
fixed_lines = []
for line in lines:
    # Regex to find: ID ( Content with parens/commas ) where content is NOT quoted
    # Pattern:
    # 1. \S+ -> Node ID
    # 2. \( -> Opening paren
    # 3. ([^"]*[\(\),][^"]*) -> Content group: contains no quotes, but HAS ( ) or ,
    # 4. \) -> Closing paren
    
    # We use a pattern that matches the WHOLE node definition to verify structure
    # Match:  Prefix + ID + ( + Content + ) + Suffix
    
    # This regex attempts to capture the "Content" group
    match = re.search(r'^(\s*\S+)\(([^"]*[\(\),][^"]*)\)(\s*)$', line)
    if match:
        print(f"Match found on: '{line.strip()}'")
        # Reconstruct with quotes
        prefix = match.group(1)
        content = match.group(2)
        suffix = match.group(3)
        fixed_line = f'{prefix}("{content}"){suffix}'
        print(f"Fixed line: '{fixed_line.strip()}'")
        fixed_lines.append(fixed_line)
    else:
        fixed_lines.append(line)

print("\nFixed Code:")
print('\n'.join(fixed_lines))
