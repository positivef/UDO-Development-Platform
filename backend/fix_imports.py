import os

root = r"c:\Users\user\Documents\GitHub\UDO-Development-Platform\backend\app"
count = 0

print(f"Scanning {root}...")

for dirpath, _, filenames in os.walk(root):
    for f in filenames:
        if f.endswith(".py"):
            path = os.path.join(dirpath, f)
            try:
                with open(path, "r", encoding="utf-8") as file:
                    content = file.read()

                new_content = content.replace("from backend.app", "from app")
                new_content = new_content.replace("import backend.app", "import app")

                if new_content != content:
                    print(f"Fixing {f}")
                    with open(path, "w", encoding="utf-8") as file:
                        file.write(new_content)
                    count += 1
            except Exception as e:
                print(f"Error processing {f}: {e}")

print(f"Fixed {count} files.")
