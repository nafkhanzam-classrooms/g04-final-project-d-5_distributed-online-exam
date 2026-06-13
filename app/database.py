from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# 1. Ubah URL koneksi menunjuk ke file lokal bernama "does_db.db"
# KONEKSI BARU KE MYSQL DOCKER
# Format: mysql+pymysql://<user>:<password>@<host>:<port>/<db_name>
# ---------------------------------------------------------
SQLALCHEMY_DATABASE_URL = "mysql+pymysql://does_user:does_password@db:3306/does_db"

# Hapus parameter "check_same_thread" karena itu hanya untuk SQLite
# TAMBAHKAN CONNECT_ARGS INI:
engine = create_engine(SQLALCHEMY_DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Dependency untuk mendapatkan session DB
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()