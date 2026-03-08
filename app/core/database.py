from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.engine.url import make_url
import os
import os.path
from dotenv import load_dotenv

_env_candidates = (
    os.getenv("DOTENV_FILE"),
    ".env.development",
    ".env",
)
for _env_file in _env_candidates:
    if _env_file and os.path.exists(_env_file):
        load_dotenv(dotenv_path=_env_file)
        break

def _running_in_docker() -> bool:
    return os.path.exists("/.dockerenv") or os.getenv("RUNNING_IN_DOCKER", "").lower() in {"1", "true", "yes", "y"}

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:admin@localhost:5432/heritedge")
if DATABASE_URL:
    try:
        url = make_url(DATABASE_URL)
        if not _running_in_docker() and (url.host in {"db", "heritedge-db"}):
            DATABASE_URL = str(url.set(host="localhost"))
    except Exception:
        pass

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
