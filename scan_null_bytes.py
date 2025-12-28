import pathlib, sys
root = pathlib.Path(r"c:/Users/user/Documents/GitHub/UDO-Development-Platform")
files_with_null = []
for py_file in root.rglob('*.py'):
    data = py_file.read_bytes()
    if b'\x00' in data:
        files_with_null.append(str(py_file))
print('Files containing null bytes:', len(files_with_null))
for f in files_with_null:
    print(f)
