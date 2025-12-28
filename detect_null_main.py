import os, sys
path = r"c:\\Users\\user\\Documents\\GitHub\\UDO-Development-Platform\\backend\\main.py"
with open(path, 'rb') as f:
    data = f.read()
null_positions = [i for i, b in enumerate(data) if b == 0]
print('null byte count:', len(null_positions))
if null_positions:
    print('first few positions:', null_positions[:20])
