import os
import re

root = "app"  # Relative to CWD (backend)
count = 0

print(f"Scanning directory: {os.path.abspath(root)}")

for dirpath, _, filenames in os.walk(root):
    # print(f"Checking {dirpath}...") 
    for f in filenames:
        if f.endswith(".py"):
            path = os.path.join(dirpath, f)
            if "kanban_archive.py" in f:
                print(f"Found target file: {path}")
                try:
                    with open(path, "r", encoding="utf-8") as file:
                        content = file.read()
                    print(f"Content length: {len(content)}")
                    match = re.search(r'from backend\.app', content)
                    print(f"Regex match: {match}")
                    
                    new_content = re.sub(r'(from|import)\s+backend\.app', r'\1 app', content)
                    if new_content != content:
                         print("Content changed!")
                         with open(path, "w", encoding="utf-8") as file:
                             file.write(new_content)
                         count += 1
                except Exception as e:
                    print(f"Error: {e}")

            else:
                 # Check other files silently
                try:
                    with open(path, "r", encoding="utf-8") as file:
                        content = file.read()
                    new_content = re.sub(r'(from|import)\s+backend\.app', r'\1 app', content)
                    if new_content != content:
                        print(f"Fixing {f}")
                        with open(path, "w", encoding="utf-8") as file:
                            file.write(new_content)
                        count += 1
                except:
                    pass

print(f"Fixed {count} files.")
