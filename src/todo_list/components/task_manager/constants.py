import os
from dotenv import load_dotenv
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
ALGORITHM = os.getenv("ALGORITHM", "HS256")                          # ✅ Default HS256
SECRET_KEY = os.getenv("SECRET_KEY", "fallback-secret-key-for-dev") # ✅ Default secret
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", 7))