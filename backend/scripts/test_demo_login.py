import os
from supabase import create_client

url = "https://wvwzfhbohtbqxpiypioo.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Ind2d3pmaGJvaHRicXhwaXlwaW9vIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODM1ODY1MDgsImV4cCI6MjA5OTE2MjUwOH0.8P7yGm8HPj7mfPo0Sh-zO6RDPmIuBcDckTBE7gJRB9Y"
sb = create_client(url, key)
res = sb.auth.sign_in_with_password({"email": "demo.patient4@omnifusion.demo", "password": "DemoPassword123!"})
print(res.user.email, "SUCCESS")
