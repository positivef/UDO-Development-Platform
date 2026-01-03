import os
import re

root = r"c:\Users\user\Documents\GitHub\UDO-Development-Platform\backend\app"
count = 0

print(f"Scanning {root}...")

if not os.path.exists(root):
    print("ROOT DOES NOT EXIST!")

for dirpath, _, filenames in os.walk(root):
    for f in filenames:
        if f.endswith(".py"):
            path = os.path.join(dirpath, f)
            try:
                with open(path, "r", encoding="utf-8") as file:
                    content = file.read()

                # Regex replacement
                new_content = re.sub(r"(from|import)\s+backend\.app", r"\1 app", content)

                if new_content != content:
                    print(f"Fixing {f}")
                    with open(path, "w", encoding="utf-8") as file:
                        file.write(new_content)
                    count += 1
                # else:
                #     if "kanban_archive.py" in f:
                #         print(f"DEBUG: {f} content didn't change.")
                #         match = re.search(r'(from|import)\s+backend\.app', content)
                #         print(f"DEBUG match: {match}")

            except Exception as e:
                print(f"Error processing {f}: {e}")

print(f"Fixed {count} files.")
