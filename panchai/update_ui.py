import os

html_path = r"C:\Users\chmur\Downloads\Hackathon\Gappy\Gappy\panchai\apps\panchai-app\index.html"
html2_path = r"C:\Users\chmur\Downloads\Hackathon\Gappy\Gappy\panchai\apps\panchai-app\html.html"

with open(html_path, 'r', encoding='utf-8') as f:
    html = f.read()

with open(html_path, 'w', encoding='utf-8') as f:
    f.write(html)
with open(html2_path, 'w', encoding='utf-8') as f:
    f.write(html)

print("UI synced: index.html -> html.html")
