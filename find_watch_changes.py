with open(r"C:\Users\chmur\.gemini\antigravity-cli\brain\f73bbcd0-0816-4ad0-a1c4-ffe38cff8d9e\.system_generated\steps\255\content.md", "r", encoding="utf-8") as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if "timeoutms" in line.lower() or "resolveconfig" in line.lower():
        print(f"Line {i+1}: {line.strip()}")
