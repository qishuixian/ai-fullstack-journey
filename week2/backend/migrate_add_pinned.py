"""
数据库迁移脚本：为 sessions 表添加 pinned 字段
运行方式: python migrate_add_pinned.py
"""
import sqlite3
import os

def migrate():
    db_path = "chat.db"

    if not os.path.exists(db_path):
        print(f"数据库文件 {db_path} 不存在")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # 检查 pinned 字段是否已存在
        cursor.execute("PRAGMA table_info(sessions)")
        columns = [col[1] for col in cursor.fetchall()]

        if 'pinned' in columns:
            print("pinned 字段已存在，无需迁移")
        else:
            # 添加 pinned 字段
            cursor.execute("ALTER TABLE sessions ADD COLUMN pinned INTEGER DEFAULT 0")
            conn.commit()
            print("成功添加 pinned 字段")

    except Exception as e:
        print(f"迁移失败: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
