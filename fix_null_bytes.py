"""Clean null bytes from main.py"""
import os

filepath = 'backend/main.py'

with open(filepath, 'rb') as f:
    content = f.read()

print(f'File size: {len(content)} bytes')
null_count = content.count(b'\x00')
print(f'Null bytes found: {null_count}')

if null_count > 0:
    clean = content.replace(b'\x00', b'')
    with open(filepath, 'wb') as f:
        f.write(clean)
    print(f'Removed {null_count} null bytes!')
    print(f'New size: {len(clean)} bytes')
else:
    print('No null bytes found')
