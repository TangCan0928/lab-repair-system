# -*- coding: utf-8 -*-
"""
数据库模块：负责 SQLite 建表、工单 CRUD 与统计查询。
所有 SQL 集中在这里，便于维护与测试。
"""
import sqlite3
import os
from datetime import datetime

DB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
DB_PATH = os.path.join(DB_DIR, "repair.db")

# 工单状态常量
STATUS_PENDING = "待处理"
STATUS_PROCESSING = "处理中"
STATUS_DONE = "已完成"
VALID_STATUSES = [STATUS_PENDING, STATUS_PROCESSING, STATUS_DONE]

# 故障类别（与 AI 分析引擎保持一致）
CATEGORIES = [
    "电脑主机故障",
    "显示设备故障",
    "开发板/硬件故障",
    "网络故障",
    "外设故障",
    "其他",
]

URGENCY_LEVELS = ["高", "中", "低"]


def get_conn():
    """获取数据库连接，启用外键与 Row 工厂。"""
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """初始化数据表（不存在则创建）。"""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS workorders (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            ticket_no     TEXT    NOT NULL UNIQUE,
            reporter      TEXT    NOT NULL,
            device_name   TEXT    NOT NULL,
            location      TEXT    NOT NULL,
            description   TEXT    NOT NULL,
            contact       TEXT    NOT NULL,
            category      TEXT    DEFAULT '其他',
            urgency       TEXT    DEFAULT '中',
            summary       TEXT    DEFAULT '',
            suggestion    TEXT    DEFAULT '',
            matched_kb    TEXT    DEFAULT '',
            need_manual   INTEGER DEFAULT 0,
            status        TEXT    DEFAULT '待处理',
            result        TEXT    DEFAULT '',
            created_at    TEXT    NOT NULL,
            updated_at    TEXT    NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()


def next_ticket_no(conn=None):
    """生成工单编号：WO + 日期 + 三位序号，例如 WO20260923-007。"""
    own = False
    if conn is None:
        conn = get_conn()
        own = True
    today = datetime.now().strftime("%Y%m%d")
    prefix = f"WO{today}-"
    cur = conn.execute(
        "SELECT COUNT(*) AS n FROM workorders WHERE ticket_no LIKE ?",
        (prefix + "%",),
    )
    n = cur.fetchone()["n"] + 1
    if own:
        conn.close()
    return f"{prefix}{n:03d}"


def create_workorder(reporter, device_name, location, description, contact,
                     category="其他", urgency="中", summary="", suggestion="",
                     matched_kb="", need_manual=0):
    """新增一条工单，返回新工单 id 与 ticket_no。"""
    init_db()
    conn = get_conn()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ticket_no = next_ticket_no(conn)
    conn.execute(
        """
        INSERT INTO workorders
            (ticket_no, reporter, device_name, location, description, contact,
             category, urgency, summary, suggestion, matched_kb, need_manual,
             status, result, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (ticket_no, reporter, device_name, location, description, contact,
         category, urgency, summary, suggestion, matched_kb, need_manual,
         STATUS_PENDING, "", now, now),
    )
    conn.commit()
    new_id = conn.execute("SELECT last_insert_rowid() AS id").fetchone()["id"]
    conn.close()
    return new_id, ticket_no


def list_workorders(category=None, status=None, keyword=None):
    """按条件查询工单列表，按提交时间倒序。"""
    init_db()
    conn = get_conn()
    sql = "SELECT * FROM workorders WHERE 1=1"
    args = []
    if category and category != "全部":
        sql += " AND category = ?"
        args.append(category)
    if status and status != "全部":
        sql += " AND status = ?"
        args.append(status)
    if keyword:
        sql += " AND (reporter LIKE ? OR device_name LIKE ? OR description LIKE ? OR ticket_no LIKE ?)"
        kw = f"%{keyword}%"
        args.extend([kw, kw, kw, kw])
    sql += " ORDER BY created_at DESC, id DESC"
    rows = conn.execute(sql, args).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_workorder(wo_id):
    """按 id 查询单条工单。"""
    init_db()
    conn = get_conn()
    row = conn.execute("SELECT * FROM workorders WHERE id = ?", (wo_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def update_status(wo_id, status, result=""):
    """更新工单状态与处理结果。"""
    init_db()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = get_conn()
    conn.execute(
        "UPDATE workorders SET status = ?, result = ?, updated_at = ? WHERE id = ?",
        (status, result, now, wo_id),
    )
    conn.commit()
    conn.close()


def stats():
    """统计：总数、按类别计数、按状态计数。"""
    init_db()
    conn = get_conn()
    total = conn.execute("SELECT COUNT(*) AS n FROM workorders").fetchone()["n"]
    by_category = {
        r["category"]: r["n"]
        for r in conn.execute(
            "SELECT category, COUNT(*) AS n FROM workorders GROUP BY category"
        )
    }
    by_status = {
        r["status"]: r["n"]
        for r in conn.execute(
            "SELECT status, COUNT(*) AS n FROM workorders GROUP BY status"
        )
    }
    by_urgency = {
        r["urgency"]: r["n"]
        for r in conn.execute(
            "SELECT urgency, COUNT(*) AS n FROM workorders GROUP BY urgency"
        )
    }
    conn.close()
    return {
        "total": total,
        "by_category": by_category,
        "by_status": by_status,
        "by_urgency": by_urgency,
    }


def delete_workorder(wo_id):
    """删除一条工单（便于测试清理）。"""
    init_db()
    conn = get_conn()
    conn.execute("DELETE FROM workorders WHERE id = ?", (wo_id,))
    conn.commit()
    conn.close()


if __name__ == "__main__":
    # 直接运行时初始化数据库并打印统计
    init_db()
    print("数据库初始化完成：", DB_PATH)
    print("当前统计：", stats())
