import os, sys
root = r"c:\\Users\\user\\Documents\\GitHub\\UDO-Development-Platform"
for dirpath, _, filenames in os.walk(root):
    for f in filenames:
        path = os.path.join(dirpath, f)
        try:
            with open(path, 'rb') as fp:
                data = fp.read()
                if b'\x00' in data:
                    print(path)
        except Exception as e:
            # ignore binary files that can't be read as text
            pass
