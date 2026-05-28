import sys
import os
from pathlib import Path

print(f"Current Working Directory: {os.getcwd()}")
print(f"File: {__file__}")

# Logic from dashboard_RCE_APP.py
SRC_DIR = Path(__file__).resolve().parent.parent.parent
print(f"Calculated SRC_DIR: {SRC_DIR}")
print(f"SRC_DIR exists: {SRC_DIR.exists()}")
if SRC_DIR.exists():
    print(f"Contents of SRC_DIR: {os.listdir(SRC_DIR)}")

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

print("\nsys.path:")
for p in sys.path:
    print(f"  {p}")

try:
    import tools
    print("\nSUCCESS: Imported 'tools'")
    print(f"tools location: {tools.__file__}")
except ImportError as e:
    print(f"\nFAILURE: Could not import 'tools': {e}")

try:
    import views
    print("SUCCESS: Imported 'views'")
    print(f"views location: {views.__file__}")
except ImportError as e:
    print(f"FAILURE: Could not import 'views': {e}")
