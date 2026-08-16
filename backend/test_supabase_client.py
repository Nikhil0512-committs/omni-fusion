from app.core.supabase_client import supabase

try:
    res = supabase.auth.admin.create_user({
        "email": "demo.test2@omnifusion.demo",
        "password": "DemoPassword123!",
        "email_confirm": True
    })
    print(res)
except Exception as e:
    import traceback
    traceback.print_exc()

