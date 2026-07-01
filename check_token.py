import base64, json, time

token = "eyJraWQiOiJkLTE3ODI3Mjc3NDU4NDQiLCJ0eXAiOiJKV1QiLCJ2ZXJzaW9uIjoiNSIsImFsZyI6IlJTMjU2In0.eyJpYXQiOjE3ODI5MTQ2ODYsImV4cCI6MTc4MjkxODI4Niwic3ViIjoiZjU5NTgwODgtZTg4ZS00NzBhLThmNzktZDUwYzg1YjlhNTk1IiwidElkIjoicHVibGljIiwicnN1YiI6ImY1OTU4MDg4LWU4OGUtNDcwYS04Zjc5LWQ1MGM4NWI5YTU5NSIsInNlc3Npb25IYW5kbGUiOiI5ODNhMGY3NS03YTFlLTRhZTktOTBlZS04ZmEyMTBhOWQzZjgiLCJyZWZyZXNoVG9rZW5IYXNoMSI6IjBiMWZlYTQyMzIyNjI2NzUzMmJmZmIwMmM3ZDllNTYyYzhjMWQ5ODlmY2IwZWM3NzIzNTFmMDM5OGVmMDg5ZGEiLCJwYXJlbnRSZWZyZXNoVG9rZW5IYXNoMSI6IjZhNjI0NWRkZTNkYjYyYzlmMzZmMjc2MDg2NzE1NjExMzNhZTViMTU1ZjVlNDRkN2E4ZDE1ZGY1OGE1ZDAxZmMiLCJhbnRpQ3NyZlRva2VuIjpudWxsLCJjbGllbnQiOiJsZW1tYS1jbGkiLCJpc3MiOiJodHRwczovL2FwaS5sZW1tYS53b3JrL3N0L2F1dGgifQ.X08lu02wwoY9N1Ou2zydghXUW-4xBH_W8hsszbVKHDE9mRvuQuaXrDpk7-3c-HXaaVzVdPfMGnWGswJQ0IsCF-q_BEFCWnOQQhudrzYB2CGCjkXgXm0kWCyn-fQ0G7KuFw31WNwfszHiInpwGMS-r168oW5tsuLII4QLebATQkZv4Hu_vooqc1kWFrr7SYolYloAoadI_7Ly5lngXWGf929xO3ty568LX1ubDW56y90l_RwhqSGAlY52QKU1nr4ZWOXkr1dpwVpsK1ILz6bGwSMVuJTQRvmiVYL7yHrvzeEOqzqcbqBRNwEok-0-AZDWu9ZUIZdajTLy1AUU_vx6Cw"

parts = token.split(".")
payload = parts[1]
padding = 4 - len(payload) % 4
if padding != 4:
    payload += "=" * padding
decoded = base64.urlsafe_b64decode(payload)
data = json.loads(decoded)

now = time.time()
exp = data["exp"]
iat = data["iat"]
print(f"Issued at: {iat} ({time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(iat))})")
print(f"Expires:   {exp} ({time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(exp))})")
print(f"Current:   {int(now)} ({time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(now))})")
print(f"Expired? {now > exp}")
