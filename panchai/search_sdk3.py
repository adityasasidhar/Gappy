import sys

path = r"C:\Users\chmur\.gemini\antigravity-cli\brain\f73bbcd0-0816-4ad0-a1c4-ffe38cff8d9e\.system_generated\steps\255\content.md"

with open(path, "r", encoding="utf-8") as f:
    lines = f.readlines()
    for i, line in enumerate(lines):
        if "runs.create" in line or "create(" in line:
            # this is too broad. Just find runs object
            pass

    import re
    # find class WorkflowRuns or runs {
    match = re.search(r'class WorkflowRuns.*?{.*?create\(.*?\).*?}', "".join(lines), re.DOTALL)
    if match:
        print(match.group(0)[:500])
