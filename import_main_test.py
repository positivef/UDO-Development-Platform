import traceback
try:
    import backend.main as m
    print('backend.main imported successfully')
except Exception as e:
    print('Import failed')
    traceback.print_exc()
