from app.core.supabase_client import supabase

try:
    res = supabase.table("predictions").select("*").limit(1).execute()
    print("Columns:", res.data[0].keys() if res.data else "No data")
    print("Data:", res.data)
except Exception as e:
    import traceback
    traceback.print_exc()
