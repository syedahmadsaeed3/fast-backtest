from dotenv import load_dotenv
import os


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))


DEBUG = int(os.environ.get("DEBUG", 0))

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

POLYGON_API_KEY = os.environ.get("POLYGON_API_KEY")
THETADATA_USER = os.environ.get("THETADATA_USER")
THETADATA_PASSWORD = os.environ.get("THETADATA_PASSWORD")
THETADATA_BASE_URL = os.environ.get("THETADATA_BASE_URL")

DATA_SERVICE = int(os.environ.get("DATA_SERVICE"))
