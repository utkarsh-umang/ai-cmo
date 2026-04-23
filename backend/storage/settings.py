"""Key-value settings storage."""

from __future__ import annotations

from opencmo.storage._db import get_db


async def get_setting(key: str) -> str | None:
    db = await get_db()
    try:
        cursor = await db.execute("SELECT value FROM settings WHERE key = ?", (key,))
        row = await cursor.fetchone()
        return row[0] if row else None
    finally:
        await db.close()


async def set_setting(key: str, value: str) -> None:
    db = await get_db()
    try:
        await db.execute(
            "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
            (key, value),
        )
        await db.commit()
    finally:
        await db.close()


async def delete_setting(key: str) -> bool:
    db = await get_db()
    try:
        cursor = await db.execute("DELETE FROM settings WHERE key = ?", (key,))
        await db.commit()
        return cursor.rowcount > 0
    finally:
        await db.close()
