import pathlib, sys
root = pathlib.Path(r"c:/Users/user/Documents/GitHub/UDO-Development-Platform")
null_files = []
for py in root.rglob('*.py'):
    data = py.read_bytes()
    if b'\x00' in data:
        null_files.append((py, data.count(b'\x00')))
print('Found', len(null_files), 'files with null bytes')
for f, cnt in null_files:
    print(f, cnt)
