import os
from supabase import create_client

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
sb = create_client(url, key)
users_res = sb.auth.admin.list_users()
users = users_res if isinstance(users_res, list) else getattr(users_res, 'users', [])
print(f"Total users: {len(users)}")
for u in users:
    p_res = sb.table("profiles").select("*").eq("id", u.id).execute()
    if not p_res.data:
        print(f"User {u.email} ({u.id}) has NO profile.")
    else:
        print(f"User {u.email} ({u.id}) has profile.")
