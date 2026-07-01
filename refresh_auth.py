"""Try to refresh Lemma auth token using the refresh token."""
import httpx
import json

refresh_token = "WUFeF/1v/5Agu8rkoXeA6QE2W1rNiE9hg5QlwkSWhPR2Q+BeXfeOU9/iUoBPQH9OauBqm3vkEMVXtUivv2/4IlNHpZ5CX5GhcZxFm92TWxmC5KOXaDLjwXyahUv5mKHXidu08c2CgunJI4I+4iQ61ZHiYVI7KXf353dG9/x9otq+eLPx3/7FcjQpZLPbdGtkACAMvSCmezkdPXDkfjhGojS2EAU7kOjiVpg94Nrxj2nxlDIf8Pz/19z20f8Z2m10PSZMMcjEv74rRO6AgewHamM/gEjs0JnBNTgIOlQNB5pBzK37Co9Cx23O5m3VcvhOrmYXRJvNsRyxIDbMLYgEitheELp2K3ca2V1G9afKCFweCnoVpD7Z9/3VLzpiB8IFX8/cmZqCTdyj6a3U.748776a3653cdb6ba5c6b43b5486b4525bb469491e0455f782bae792dba31ddf.V2"

# Try to call the Lemma auth refresh endpoint
url = "https://api.lemma.work/st/auth/refresh"
resp = httpx.post(url, json={"refresh_token": refresh_token})
print(f"Status: {resp.status_code}")
print(f"Response: {resp.text[:500]}")
