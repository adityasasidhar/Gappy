import json, os
config_path = os.path.expanduser(r"C:\Users\chmur\.lemma\config.json")
with open(config_path, "r", encoding="utf-8") as f:
    config = json.load(f)
for s in config.get("servers", {}):
    print(f"Server {s}: {list(config['servers'][s].keys())}")
    # print token info keys
    t_info = config['servers'][s].get("token_info", {})
    print(f"  token_info keys: {list(t_info.keys())}")
