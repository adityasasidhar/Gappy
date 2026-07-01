import sys

path = r"C:\Users\chmur\.gemini\antigravity-cli\brain\f73bbcd0-0816-4ad0-a1c4-ffe38cff8d9e\.system_generated\steps\255\content.md"

with open(path, "r", encoding="utf-8") as f:
    for i, line in enumerate(f):
        if "setPodId" in line:
            print(f"Line {i+1}: {line.strip()}")
