import os, hashlib, secrets, mysql.connector
from mysql.connector import Error
from .db_config import DB_CONFIG

class DatabaseManager:
    def __init__(self, config=None):
        self.config = config or DB_CONFIG
        self.connection = None

    def connect(self):
        # Connect to the configured database first. If the database itself
        # does not exist yet, create it automatically on the configured port.
        try:
            self.connection = mysql.connector.connect(**self.config)
            return self.connection.is_connected()
        except Error as e:
            print(f"[DB] Initial connection failed: {e}")
            self.connection = None

        try:
            server_config = dict(self.config)
            db_name = server_config.pop("database", None)
            self.connection = mysql.connector.connect(**server_config)
            if not self.connection.is_connected():
                self.connection = None
                return False
            cur = self.connection.cursor()
            cur.execute(f"CREATE DATABASE IF NOT EXISTS `{db_name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            cur.close()
            self.connection.close()
            self.connection = mysql.connector.connect(**self.config)
            return self.connection.is_connected()
        except Error as e:
            print(f"[DB] Could not connect/create database: {e}")
            self.connection = None
            return False

    def disconnect(self):
        if self.connection and self.connection.is_connected():
            self.connection.close()
        self.connection = None

    def is_connected(self):
        return bool(self.connection and self.connection.is_connected())

    def _ensure_connection(self):
        return self.is_connected() or self.connect()

    def create_tables(self):
        if not self._ensure_connection(): return False
        try:
            cur=self.connection.cursor()
            cur.execute("""CREATE TABLE IF NOT EXISTS players(
                player_id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(50) NOT NULL UNIQUE,
                email VARCHAR(120) NULL,
                password_hash VARCHAR(255) NULL,
                high_score INT NOT NULL DEFAULT 0,
                games_played INT NOT NULL DEFAULT 0,
                selected_ship INT NOT NULL DEFAULT 0,
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            ) ENGINE=InnoDB""")
            # Upgrade older MAPUTI databases without destroying data.
            try: cur.execute("ALTER TABLE players ADD COLUMN password_hash VARCHAR(255) NULL")
            except Error: pass
            try: cur.execute("ALTER TABLE players ADD COLUMN selected_ship INT NOT NULL DEFAULT 0")
            except Error: pass
            cur.execute("""CREATE TABLE IF NOT EXISTS scores(
                score_id INT AUTO_INCREMENT PRIMARY KEY,
                player_id INT NOT NULL,
                score INT NOT NULL,
                played_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                CONSTRAINT fk_scores_player FOREIGN KEY(player_id) REFERENCES players(player_id) ON DELETE CASCADE
            ) ENGINE=InnoDB""")
            self.connection.commit(); cur.close(); return True
        except Error as e:
            print(f"[DB] create_tables failed: {e}"); return False

    @staticmethod
    def _hash_password(password, salt=None):
        salt = salt or secrets.token_hex(16)
        digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 120000).hex()
        return f"pbkdf2_sha256$120000${salt}${digest}"

    @staticmethod
    def _verify_password(password, stored):
        try:
            alg, rounds, salt, digest = stored.split("$", 3)
            check=hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), int(rounds)).hex()
            return secrets.compare_digest(check,digest)
        except Exception:
            return False

    def get_player(self, username=None, player_id=None):
        if not self._ensure_connection() or (username is None and player_id is None): return None
        try:
            cur=self.connection.cursor(dictionary=True)
            if player_id is not None: cur.execute("SELECT * FROM players WHERE player_id=%s",(player_id,))
            else: cur.execute("SELECT * FROM players WHERE username=%s",(username,))
            row=cur.fetchone(); cur.close(); return row
        except Error as e:
            print(f"[DB] get_player failed: {e}"); return None

    def register_player(self, username, password, email=None):
        if not self._ensure_connection(): return None, "Database unavailable."
        username=username.strip()
        if len(username)<3: return None, "Username must be at least 3 characters."
        if len(password)<6: return None, "Password must be at least 6 characters."
        if self.get_player(username=username): return None, "Username already exists."
        try:
            cur=self.connection.cursor()
            cur.execute("INSERT INTO players(username,email,password_hash) VALUES(%s,%s,%s)",
                        (username,email,self._hash_password(password)))
            self.connection.commit(); pid=cur.lastrowid; cur.close()
            return pid, "Account created."
        except Error as e:
            print(f"[DB] register_player failed: {e}"); return None, "Could not create account."

    def login_player(self, username, password):
        row=self.get_player(username=username)
        if not row: return None, "Account not found."
        if not row.get("password_hash"): return None, "This account has no password. Register a new account."
        if not self._verify_password(password,row["password_hash"]): return None, "Incorrect password."
        return row, "Login successful."


    def set_player_preference(self, player_id, key, value):
        if key != 'selected_ship' or not self._ensure_connection(): return False
        try:
            cur=self.connection.cursor()
            cur.execute("UPDATE players SET selected_ship=%s WHERE player_id=%s",(int(value),player_id))
            self.connection.commit(); cur.close(); return True
        except Error as e:
            print(f"[DB] preference update failed: {e}"); return False

    def save_score(self, player_id, score):
        if not self._ensure_connection(): return False
        try:
            cur=self.connection.cursor()
            cur.execute("INSERT INTO scores(player_id,score) VALUES(%s,%s)",(player_id,score))
            cur.execute("""UPDATE players SET games_played=games_played+1,
                           high_score=GREATEST(high_score,%s) WHERE player_id=%s""",(score,player_id))
            self.connection.commit(); cur.close(); return True
        except Error as e:
            print(f"[DB] save_score failed: {e}"); return False

    def get_leaderboard(self, limit=10):
        if not self._ensure_connection(): return []
        try:
            cur=self.connection.cursor(dictionary=True)
            cur.execute("SELECT username,high_score,games_played FROM players ORDER BY high_score DESC LIMIT %s",(limit,))
            rows=cur.fetchall(); cur.close(); return rows
        except Error: return []

    def get_player_scores(self, player_id, limit=10):
        if not self._ensure_connection(): return []
        try:
            cur=self.connection.cursor(dictionary=True)
            cur.execute("SELECT score,played_at FROM scores WHERE player_id=%s ORDER BY played_at DESC LIMIT %s",(player_id,limit))
            rows=cur.fetchall(); cur.close(); return rows
        except Error: return []
