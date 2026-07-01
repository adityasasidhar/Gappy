import sys
import re

path = r"C:\Users\chmur\.gemini\antigravity-cli\brain\f73bbcd0-0816-4ad0-a1c4-ffe38cff8d9e\.system_generated\steps\255\content.md"

with open(path, "r", encoding="utf-8") as f:
    content = f.read()
    
    match = re.search(r'list\(table,\s*options.*?\).*?}', content, re.DOTALL)
    if match:
        print(match.group(0))
