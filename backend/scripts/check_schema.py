import os
from supabase import create_client, Client
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
sb = create_client(url, key)
res = sb.table("predictions").select("*").limit(1).execute()
if res.data:
    print(res.data[0].keys())
else:
    print("No predictions")
