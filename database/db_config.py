import os

DB_CONFIG = {
    "host": os.environ.get("MAPUTI_DB_HOST", "localhost"),
    "port": int(os.environ.get("MAPUTI_DB_PORT", "3307")),
    "user": os.environ.get("MAPUTI_DB_USER", "root"),
    "password": os.environ.get("MAPUTI_DB_PASSWORD", ""),
    "database": os.environ.get("MAPUTI_DB_NAME", "Space_Invaders_Andaya"),
}
