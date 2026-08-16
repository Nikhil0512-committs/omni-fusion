import os
from supabase import create_client, Client

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
supabase: Client = create_client(url, key)

# Query profiles
res = supabase.table("profiles").select("*").execute()
print(f"Profiles count: {len(res.data)}")
for p in res.data:
    print(f"- {p['email']} (role: {p.get('role')})")

# Get demo.doctor1 id
doc_res = supabase.table("profiles").select("id").eq("email", "demo.doctor1@omnifusion.demo").execute()
if doc_res.data:
    doc_id = doc_res.data[0]['id']
    print(f"demo.doctor1 id: {doc_id}")
    links = supabase.table("doctor_patient_links").select("*").eq("doctor_id", doc_id).execute()
    print(f"Links for doctor1: {links.data}")
    
    # Check predictions for the first patient if any
    if links.data:
        pat_id = links.data[0]['patient_id']
        preds = supabase.table("predictions").select("*").eq("patient_id", pat_id).execute()
        print(f"Predictions for patient {pat_id}: {len(preds.data)}")
else:
    print("demo.doctor1 not found")

