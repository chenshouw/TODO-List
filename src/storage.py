# -*- coding: utf-8 -*-
"""
数据持久化模块（SQLite）
负责将任务列表读写到本地 SQLite 数据库，支持按日期与完成状态建立索引，
保证重启后数据不丢失。

数据库表结构
------------
``todos`` 表字段：
- id         (TEXT, PRIMARY KEY)   UUID 字符串，作为任务唯一标识
- text       (TEXT, NOT NULL)      任务内容文本
- done       (INTEGER, NOT NULL)   完成状态，0 表示未完成，1 表示已完成
- deleted    (INTEGER, NOT NULL)   逻辑删除状态，0 表示正常，1 表示已逻辑删除
- created_at (REAL, NOT NULL)      创建时间，unix 时间戳（秒级）
- updated_at (REAL, NOT NULL)      最后更新时间，unix 时间戳（秒级）
- deleted_at (REAL)                逻辑删除时间，unix 时间戳（秒级）

建立的索引
----------
- ``idx_done``         针对 ``done`` 列，便于按完成状态过滤
- ``idx_created_at``   针对 ``created_at`` 列，便于按创建时间排序 / 过滤
- ``idx_done_created`` 针对 ``(done, created_at)`` 复合索引，便于同时按
  完成状态 + 日期进行高效查询
"""

import os
import sqlite3
import sys

from .models import Todo


# ---------------------------------------------------------------------------
# 工具函数
# ---------------------------------------------------------------------------

def get_default_data_path():
    """
    获取默认的任务数据库文件路径。

    在开发模式下将文件放置在项目根目录的 data 子目录中；
    在打包后的可执行文件目录中使用同一路径规则。

    Returns
    -------
    str
        数据库文件的绝对路径，例如 ``<project>/data/todos.db``。
    """
    if getattr(sys, "frozen", False):
        base_dir = os.path.dirname(sys.executable)
    else:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(base_dir, "data")
    if not os.path.isdir(data_dir):
        os.makedirs(data_dir, exist_ok=True)
    return os.path.join(data_dir, "todos.db")


def _row_to_todo(row):
    """
    将数据库查询结果（字典或元组）转换为 Todo 对象。

    Parameters
    ----------
    row : dict or sqlite3.Row
        包含字段：id, text, done, deleted, created_at, updated_at, deleted_at。

    Returns
    -------
    Todo
        任务对象。
    """
    return Todo(
        text=row["text"],
        done=bool(row["done"]),
        id=row["id"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        deleted=bool(row["deleted"]),
        deleted_at=row["deleted_at"],
    )


# ---------------------------------------------------------------------------
# TodoStorage
# ---------------------------------------------------------------------------

class TodoStorage(object):
    """
    任务数据存储管理器（基于 SQLite）。

    提供对任务的增删改查与过滤查询，支持按日期和完成状态建立索引，
    读写过程包含基本错误处理，避免单次异常导致整个应用崩溃。

    Attributes
    ----------
    db_path : str
        SQLite 数据库文件的绝对路径。
    """

    # 建表与索引的 SQL 常量，在构造函数中首次连接时执行
    _CREATE_TABLE_SQL = """
        CREATE TABLE IF NOT EXISTS todos (
            id         TEXT PRIMARY KEY,
            text       TEXT NOT NULL,
            done       INTEGER NOT NULL DEFAULT 0,
            deleted    INTEGER NOT NULL DEFAULT 0,
            created_at REAL NOT NULL,
            updated_at REAL NOT NULL,
            deleted_at REAL
        );
    """

    _CREATE_INDEX_SQLS = [
        "CREATE INDEX IF NOT EXISTS idx_done         ON todos(done);",
        "CREATE INDEX IF NOT EXISTS idx_created_at   ON todos(created_at);",
        "CREATE INDEX IF NOT EXISTS idx_done_created ON todos(done, created_at);",
    ]

    def __init__(self, db_path=None):
        """
        初始化数据存储管理器。

        会在给定路径下自动创建 ``todos`` 表以及必要的索引。

        Parameters
        ----------
        db_path : str, optional
            指定数据库文件路径，如不指定则使用 :func:`get_default_data_path` 返回的路径。
        """
        self.db_path = db_path if db_path else get_default_data_path()
        self._ensure_database()

    # ------------------------------------------------------------------
    # 初始化 / 连接
    # ------------------------------------------------------------------

    def _ensure_database(self):
        """
        创建数据库文件所在目录，初始化表结构与索引。
        """
        dir_name = os.path.dirname(self.db_path)
        if dir_name and not os.path.isdir(dir_name):
            os.makedirs(dir_name, exist_ok=True)
        with self._connect() as conn:
            # 检查并添加 deleted 和 deleted_at 列（用于升级现有数据库）
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(todos)")
            columns = [row[1] for row in cursor.fetchall()]
            
            if 'deleted' not in columns:
                conn.execute("ALTER TABLE todos ADD COLUMN deleted INTEGER NOT NULL DEFAULT 0")
            if 'deleted_at' not in columns:
                conn.execute("ALTER TABLE todos ADD COLUMN deleted_at REAL")
            
            # 建表和索引
            conn.execute(self._CREATE_TABLE_SQL)
            for sql in self._CREATE_INDEX_SQLS:
                conn.execute(sql)

    def _connect(self):
        """
        创建并返回一个新的 SQLite 连接。

        返回的连接会将 ``row_factory`` 设置为 ``sqlite3.Row``，
        便于通过字段名读取记录。

        Returns
        -------
        sqlite3.Connection
            配置好的数据库连接对象。
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    # ------------------------------------------------------------------
    # 增删改查
    # ------------------------------------------------------------------

    def load(self):
        """
        从数据库加载任务列表（排除已逻辑删除的），按创建时间倒序排序。

        Returns
        -------
        list of Todo
            读取到的任务对象列表；若表为空或读取失败则返回空列表。
        """
        try:
            with self._connect() as conn:
                rows = conn.execute(
                    "SELECT id, text, done, deleted, created_at, updated_at, deleted_at "
                    "FROM todos WHERE deleted = 0 ORDER BY created_at DESC"
                ).fetchall()
            return [_row_to_todo(r) for r in rows]
        except sqlite3.Error as exc:
            print("读取任务数据库失败：{0}".format(exc))
            return []

    def query(self, done=None, start_ts=None, end_ts=None):
        """
        按完成状态与日期时间范围查询任务（排除已逻辑删除的）。

        这是索引（``idx_done`` / ``idx_created_at`` / ``idx_done_created``）
        真正发挥作用的查询入口，外部调用者可用它做各种筛选展示。

        Parameters
        ----------
        done : bool, optional
            若为 True 则只查已完成，False 只查未完成，None 不做该条件限制。
        start_ts : float, optional
            起始 unix 时间戳（秒级），包含该时刻。
        end_ts : float, optional
            结束 unix 时间戳（秒级），包含该时刻。

        Returns
        -------
        list of Todo
            满足条件的任务对象列表，按创建时间倒序排列。
        """
        clauses = ["deleted = 0"]
        params = []
        if done is not None:
            clauses.append("done = ?")
            params.append(1 if done else 0)
        if start_ts is not None:
            clauses.append("created_at >= ?")
            params.append(float(start_ts))
        if end_ts is not None:
            clauses.append("created_at <= ?")
            params.append(float(end_ts))

        sql = (
            "SELECT id, text, done, deleted, created_at, updated_at, deleted_at FROM todos "
            "WHERE " + " AND ".join(clauses) + " ORDER BY created_at DESC"
        )
        try:
            with self._connect() as conn:
                rows = conn.execute(sql, params).fetchall()
            return [_row_to_todo(r) for r in rows]
        except sqlite3.Error as exc:
            print("查询任务失败：{0}".format(exc))
            return []

    def add_todo(self, todo):
        """
        新增一条任务到数据库。

        Parameters
        ----------
        todo : Todo
            要新增的任务对象。若其 ``id`` 未指定会由 :class:`Todo` 自身自动生成。

        Returns
        -------
        bool
            成功返回 True，失败返回 False。
        """
        try:
            with self._connect() as conn:
                conn.execute(
                    "INSERT INTO todos (id, text, done, deleted, created_at, updated_at, deleted_at) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (
                        todo.id,
                        todo.text,
                        1 if todo.done else 0,
                        1 if todo.deleted else 0,
                        todo.created_at,
                        todo.updated_at,
                        todo.deleted_at,
                    ),
                )
            return True
        except sqlite3.Error as exc:
            print("新增任务失败：{0}".format(exc))
            return False

    def update_todo(self, todo):
        """
        更新任务的文本内容与 ``updated_at`` 字段。

        Parameters
        ----------
        todo : Todo
            已修改过内容的任务对象，必须包含有效的 ``id``。

        Returns
        -------
        bool
            成功返回 True，失败返回 False。
        """
        try:
            with self._connect() as conn:
                conn.execute(
                    "UPDATE todos SET text = ?, updated_at = ? WHERE id = ?",
                    (todo.text, todo.updated_at, todo.id),
                )
            return True
        except sqlite3.Error as exc:
            print("更新任务失败：{0}".format(exc))
            return False

    def update_done(self, todo):
        """
        更新任务的完成状态与 ``updated_at`` 字段。

        Parameters
        ----------
        todo : Todo
            包含新完成状态的任务对象，必须包含有效的 ``id``。

        Returns
        -------
        bool
            成功返回 True，失败返回 False。
        """
        try:
            with self._connect() as conn:
                conn.execute(
                    "UPDATE todos SET done = ?, updated_at = ? WHERE id = ?",
                    (1 if todo.done else 0, todo.updated_at, todo.id),
                )
            return True
        except sqlite3.Error as exc:
            print("更新任务完成状态失败：{0}".format(exc))
            return False

    def delete_todo(self, todo):
        """
        对任务进行逻辑删除（不是物理删除）。

        Parameters
        ----------
        todo : Todo
            要删除的任务对象（以 ``id`` 作为删除依据）。

        Returns
        -------
        bool
            成功返回 True，失败返回 False。
        """
        try:
            now = __import__('time').time()
            with self._connect() as conn:
                conn.execute(
                    "UPDATE todos SET deleted = 1, deleted_at = ?, updated_at = ? WHERE id = ?",
                    (now, now, todo.id),
                )
            return True
        except sqlite3.Error as exc:
            print("逻辑删除任务失败：{0}".format(exc))
            return False

    def hard_delete_todo(self, todo):
        """
        对任务进行物理删除（从数据库中永久移除）。

        Parameters
        ----------
        todo : Todo
            要物理删除的任务对象（以 ``id`` 作为删除依据）。

        Returns
        -------
        bool
            成功返回 True，失败返回 False。
        """
        try:
            with self._connect() as conn:
                conn.execute("DELETE FROM todos WHERE id = ?", (todo.id,))
            return True
        except sqlite3.Error as exc:
            print("物理删除任务失败：{0}".format(exc))
            return False

    def clear_done(self, before_ts=None):
        """
        对已完成的任务进行逻辑删除，可选指定日期时间。

        Parameters
        ----------
        before_ts : float, optional
            若指定，则只清除该时间戳之前创建的已完成任务。
            若不指定，则清除所有已完成任务。

        Returns
        -------
        int
            实际逻辑删除的任务条数；若出错则返回 0。
        """
        try:
            now = __import__('time').time()
            with self._connect() as conn:
                if before_ts is not None:
                    cur = conn.execute(
                        "UPDATE todos SET deleted = 1, deleted_at = ?, updated_at = ? "
                        "WHERE done = 1 AND created_at <= ?",
                        (now, now, before_ts),
                    )
                else:
                    cur = conn.execute(
                        "UPDATE todos SET deleted = 1, deleted_at = ?, updated_at = ? "
                        "WHERE done = 1",
                        (now, now),
                    )
                return cur.rowcount if cur.rowcount else 0
        except sqlite3.Error as exc:
            print("逻辑清除已完成任务失败：{0}".format(exc))
            return 0

    def hard_clear_done(self, before_ts=None):
        """
        对已完成的任务进行物理删除（永久移除），可选指定日期时间。

        Parameters
        ----------
        before_ts : float, optional
            若指定，则只物理删除该时间戳之前创建的已完成任务。
            若不指定，则物理删除所有已完成任务。

        Returns
        -------
        int
            实际物理删除的任务条数；若出错则返回 0。
        """
        try:
            with self._connect() as conn:
                if before_ts is not None:
                    cur = conn.execute(
                        "DELETE FROM todos WHERE done = 1 AND created_at <= ?",
                        (before_ts,),
                    )
                else:
                    cur = conn.execute(
                        "DELETE FROM todos WHERE done = 1"
                    )
                return cur.rowcount if cur.rowcount else 0
        except sqlite3.Error as exc:
            print("物理清除已完成任务失败：{0}".format(exc))
            return 0

    # ------------------------------------------------------------------
    # 统计信息
    # ------------------------------------------------------------------

    def count_stats(self):
        """
        返回任务整体统计信息（排除已逻辑删除的）：总数 / 未完成数 / 已完成数。

        Returns
        -------
        dict
            形如 ``{"total": N, "active": M, "done": K}`` 的字典。
        """
        try:
            with self._connect() as conn:
                row = conn.execute(
                    "SELECT "
                    "COUNT(*) AS total, "
                    "SUM(CASE WHEN done = 0 THEN 1 ELSE 0 END) AS active, "
                    "SUM(CASE WHEN done = 1 THEN 1 ELSE 0 END) AS done "
                    "FROM todos WHERE deleted = 0"
                ).fetchone()
            total = row["total"] if row else 0
            active = row["active"] if row and row["active"] is not None else 0
            done = row["done"] if row and row["done"] is not None else 0
            return {"total": total, "active": active, "done": done}
        except sqlite3.Error as exc:
            print("查询任务统计失败：{0}".format(exc))
            return {"total": 0, "active": 0, "done": 0}

    def count_done_before(self, before_ts):
        """
        统计指定时间之前创建的已完成任务数量。

        Parameters
        ----------
        before_ts : float
            指定的时间戳。

        Returns
        -------
        int
            指定时间前的已完成任务数（排除已逻辑删除的）。
        """
        try:
            with self._connect() as conn:
                row = conn.execute(
                    "SELECT COUNT(*) AS cnt FROM todos WHERE done = 1 AND deleted = 0 AND created_at <= ?",
                    (before_ts,),
                ).fetchone()
            return row["cnt"] if row and row["cnt"] is not None else 0
        except sqlite3.Error as exc:
            print("查询任务统计失败：{0}".format(exc))
            return 0

    # ------------------------------------------------------------------
    # 导出功能
    # ------------------------------------------------------------------

    def export_to_csv(self, file_path):
        """
        将当前所有任务导出为 CSV 文件（排除已逻辑删除的）。

        CSV 列顺序与表头：序号, 状态, 内容, 创建时间, 最后更新时间。
        默认使用 UTF-8 + BOM 编码，保证 Excel 打开不乱码。

        Parameters
        ----------
        file_path : str
            导出文件的绝对或相对路径。

        Returns
        -------
        int
            成功导出的任务行数（不含表头行）；失败时返回 0。
        """
        import csv
        import datetime

        todos = self.load()
        if not todos:
            try:
                # 空数据仍然写表头，让用户知道导出成功
                with open(file_path, "w", encoding="utf-8-sig", newline="") as fp:
                    writer = csv.writer(fp)
                    writer.writerow(["序号", "状态", "内容", "创建时间", "最后更新时间"])
                return 0
            except OSError as exc:
                print("写入 CSV 失败：{0}".format(exc))
                return 0
        try:
            with open(file_path, "w", encoding="utf-8-sig", newline="") as fp:
                writer = csv.writer(fp)
                writer.writerow(["序号", "状态", "内容", "创建时间", "最后更新时间"])
                for idx, todo in enumerate(todos, 1):
                    status = "已完成" if todo.done else "未完成"
                    created = datetime.datetime.fromtimestamp(todo.created_at).strftime("%Y-%m-%d %H:%M:%S")
                    updated = datetime.datetime.fromtimestamp(todo.updated_at).strftime("%Y-%m-%d %H:%M:%S")
                    writer.writerow([idx, status, todo.text, created, updated])
            return len(todos)
        except OSError as exc:
            print("写入 CSV 失败：{0}".format(exc))
            return 0

    def export_to_text(self, file_path):
        """
        将当前所有任务导出为纯文本清单（排除已逻辑删除的），采用更直观的人类可读格式。

        文本包含整体统计信息以及每条任务的状态标记与时间信息。

        Parameters
        ----------
        file_path : str
            导出文件的绝对或相对路径。

        Returns
        -------
        int
            成功导出的任务行数；失败时返回 0。
        """
        import datetime

        todos = self.load()
        stats = self.count_stats()
        try:
            with open(file_path, "w", encoding="utf-8") as fp:
                # 标题
                now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                fp.write("我的待办清单\n")
                fp.write("导出时间：{0}\n".format(now))
                fp.write("共 {0} 项 · 未完成 {1} · 已完成 {2}\n".format(
                    stats["total"], stats["active"], stats["done"]))
                fp.write("-" * 40 + "\n\n")

                if not todos:
                    fp.write("（暂无任务）\n")
                    return 0

                # 未完成部分
                active_items = [t for t in todos if not t.done]
                done_items = [t for t in todos if t.done]
                if active_items:
                    fp.write("【未完成】\n")
                    for idx, todo in enumerate(active_items, 1):
                        t = datetime.datetime.fromtimestamp(todo.created_at).strftime("%Y-%m-%d %H:%M")
                        fp.write("  {0}. {1}  ({2})\n".format(idx, todo.text, t))
                    fp.write("\n")

                if done_items:
                    fp.write("【已完成】\n")
                    for idx, todo in enumerate(done_items, 1):
                        t = datetime.datetime.fromtimestamp(todo.updated_at).strftime("%Y-%m-%d %H:%M")
                        fp.write("  {0}. [v] {1}  ({2})\n".format(idx, todo.text, t))
                    fp.write("\n")

            return len(todos)
        except OSError as exc:
            print("写入文本文件失败：{0}".format(exc))
            return 0

    # ------------------------------------------------------------------
    # 向后兼容的 save 方法（外部若仍有直接调用 save 也能工作）
    # ------------------------------------------------------------------

    def save(self, todos):
        """
        与旧版 JSON 存储接口保持兼容：将传入的任务列表整体写入数据库。

        实现方式是先清空表，再逐条插入新数据。对于普通应用规模而言性能足够；
        如果有大规模数据场景，应直接使用增删改查单条接口。

        Parameters
        ----------
        todos : list of Todo
            要持久化的任务对象列表。

        Returns
        -------
        bool
            保存成功返回 True，失败返回 False。

        Raises
        ------
        TypeError
            当 ``todos`` 不是列表时抛出。
        """
        if not isinstance(todos, list):
            raise TypeError("save 方法需要接收 Todo 列表参数")
        try:
            with self._connect() as conn:
                conn.execute("DELETE FROM todos")
                for todo in todos:
                    conn.execute(
                        "INSERT INTO todos (id, text, done, deleted, created_at, updated_at, deleted_at) "
                        "VALUES (?, ?, ?, ?, ?, ?, ?)",
                        (
                            todo.id,
                            todo.text,
                            1 if todo.done else 0,
                            1 if todo.deleted else 0,
                            todo.created_at,
                            todo.updated_at,
                            todo.deleted_at,
                        ),
                    )
            return True
        except sqlite3.Error as exc:
            print("保存任务数据库失败：{0}".format(exc))
            return False
