
import sys
import os
import traceback

print("Current Path:", sys.path)
print("CWD:", os.getcwd())

print("--- Attempting to import services.helpers ---")
try:
    from services import helpers
    print("SUCCESS: Imported services.helpers")
except Exception:
    traceback.print_exc()

print("\n--- Attempting to import ui.tabs ---")
try:
    import ui.tabs
    print("SUCCESS: Imported ui.tabs")
except Exception:
    traceback.print_exc()
