import json, os
config_path = os.path.expanduser(r"C:\Users\chmur\.lemma\config.json")
with open(config_path, "r", encoding="utf-8") as f:
    config = json.load(f)
print(config.get("servers", {}).get("cloud", {}).get("base_url"))
