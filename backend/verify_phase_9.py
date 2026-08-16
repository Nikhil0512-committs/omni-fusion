from app.core.supabase_client import supabase

print("Phase 9 Verification: Supabase Tables")
print("-" * 50)

# Check upload_sessions
res = supabase.table('upload_sessions').select('*').limit(1).execute()
print("1. upload_sessions row:")
print(res.data)
print("-" * 50)

# Check predictions
res = supabase.table('predictions').select('*').limit(1).execute()
print("2. predictions row:")
print(res.data)
print("-" * 50)

# Check reports
res = supabase.table('reports').select('*').limit(1).execute()
print("3. reports row:")
print(res.data)
print("-" * 50)

if res.data:
    storage_path = res.data[0]['pdf_storage_path']
    # Get signed url
    url_res = supabase.storage.from_("reports").create_signed_url(storage_path, 3600)
    print("4. Sample Generated PDF URL:")
    print(url_res.get('signedURL'))
    
