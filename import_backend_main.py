import sys, os
# Ensure project root is in PYTHONPATH
project_root = os.path.abspath(os.path.dirname(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    import backend.main as m
    print('backend.main imported successfully')
except Exception as e:
    import traceback
    print('Import failed')
    traceback.print_exc()
