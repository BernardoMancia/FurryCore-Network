import os
from dotenv import load_dotenv

load_dotenv()
pwd = os.getenv('SMTP_PASS')
print(f"DEBUG_PWD_LEN: {len(pwd) if pwd else 0}")
print(f"DEBUG_PWD_RAW: |{pwd}|")
