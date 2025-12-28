import os, sys
path = r"c:\\Users\\user\\Documents\\GitHub\\UDO-Development-Platform\\backend\\main.py"
with open(path, 'rb') as f:
    data = f.read()
clean = data.replace(b"\x00", b"")
with open(path, 'wb') as f:
    f.write(clean)
print('Cleaned main.py, removed null bytes')
