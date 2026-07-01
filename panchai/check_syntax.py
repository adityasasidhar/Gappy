import re
import subprocess

html_path = r"C:\Users\chmur\Downloads\Hackathon\Gappy\Gappy\panchai\apps\panchai-app\index.html"
with open(html_path, "r", encoding="utf-8") as f:
    content = f.read()

scripts = re.findall(r'<script>(.*?)</script>', content, re.DOTALL)
for i, script in enumerate(scripts):
    temp_path = f"temp_script_{i}.js"
    with open(temp_path, "w", encoding="utf-8") as f2:
        f2.write(script)
    
    print(f"Checking script block {i}...")
    try:
        subprocess.run(["node", "-c", temp_path], check=True, capture_output=True, text=True)
        print(f"Script block {i} OK.")
    except subprocess.CalledProcessError as e:
        print(f"Syntax error in script {i}:")
        print(e.stderr)

