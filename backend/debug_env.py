from dotenv import load_dotenv
import os

env_path = r"C:\Users\Admin\meshwork\meshwork\backend\.env"

print("ENV FILE EXISTS:", os.path.exists(env_path))

load_dotenv(env_path)

print("RAW VALUE:", repr(os.getenv("OPENAI_API_KEY")))
