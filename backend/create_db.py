"""
Create Admin Dashboard Database

Creates the admin database and tables used by the RÜKO Admin Dashboard.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

import psycopg2
from dotenv import load_dotenv
from psycopg2 import sql

load_dotenv()


@dataclass(frozen=True)
class PgConfig:
    host: str
    port: int
    user: str
    password: str
    admin_db: str = "ruko_admin"
    maintenance_db: str = "postgres"


def get_config() -> PgConfig:
    return PgConfig(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=int(os.getenv("POSTGRES_PORT", "5432")),
        user=os.getenv("POSTGRES_USER", "postgres"),
        password=os.getenv("POSTGRES_PASSWORD", ""),
        admin_db=os.getenv("POSTGRES_DB", "ruko_admin"),
        maintenance_db=os.getenv("POSTGRES_MAINTENANCE_DB", "postgres"),
    )


def connect(cfg: PgConfig, *, dbname: str):
    return psycopg2.connect(
        host=cfg.host,
        port=cfg.port,
        dbname=dbname,
        user=cfg.user,
        password=cfg.password,
        connect_timeout=int(os.getenv("POSTGRES_CONNECT_TIMEOUT", "5")),
        application_name=os.getenv("POSTGRES_APP_NAME", "ruko-admin-create-db"),
    )


def ensure_database(cfg: PgConfig) -> None:
    conn = connect(cfg, dbname=cfg.maintenance_db)
    try:
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (cfg.admin_db,))
            exists = cur.fetchone() is not None
            if exists:
                print(f"Database already exists: {cfg.admin_db}")
                return
            cur.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(cfg.admin_db)))
            print(f"Created database: {cfg.admin_db}")
    finally:
        conn.close()


def ensure_tables(cfg: PgConfig) -> None:
    conn = connect(cfg, dbname=cfg.admin_db)
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    ms_user_id VARCHAR(255) UNIQUE NOT NULL,
                    display_name VARCHAR(255),
                    email VARCHAR(255),
                    first_seen TIMESTAMP DEFAULT NOW(),
                    last_active TIMESTAMP DEFAULT NOW()
                )
                """
            )
            print("Created table: users")

            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS conversations (
                    id SERIAL PRIMARY KEY,
                    thread_id VARCHAR(500) NOT NULL,
                    user_id INTEGER REFERENCES users(id),
                    started_at TIMESTAMP DEFAULT NOW(),
                    last_message_at TIMESTAMP DEFAULT NOW(),
                    message_count INTEGER DEFAULT 0,
                    UNIQUE(thread_id)
                )
                """
            )
            print("Created table: conversations")

            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS messages (
                    id SERIAL PRIMARY KEY,
                    conversation_id INTEGER REFERENCES conversations(id) ON DELETE CASCADE,
                    role VARCHAR(20) NOT NULL,
                    content TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT NOW(),
                    response_time_ms INTEGER,
                    tools_used TEXT[],
                    sql_query TEXT,
                    sql_results_count INTEGER,
                    error TEXT
                )
                """
            )
            print("Created table: messages")

            cur.execute("CREATE INDEX IF NOT EXISTS idx_messages_conversation ON messages(conversation_id)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_messages_timestamp ON messages(timestamp)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_conversations_user ON conversations(user_id)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_users_ms_id ON users(ms_user_id)")
            print("Created indexes")

        conn.commit()
    finally:
        conn.close()


def main() -> None:
    cfg = get_config()
    print("Setting up Admin Dashboard Database...")
    print(f"Host: {cfg.host}:{cfg.port}")
    print(f"Admin DB: {cfg.admin_db}")
    ensure_database(cfg)
    ensure_tables(cfg)
    print("Done.")


if __name__ == "__main__":
    main()
