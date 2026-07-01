# -*- coding: utf-8 -*-
"""
数据模型模块
定义任务(Todo)数据结构及相关辅助方法。
"""

import time
import uuid


class Todo(object):
    """
    单个待办任务的数据模型。

    Attributes
    ----------
    id : str
        任务唯一标识符，使用 UUID4 自动生成。
    text : str
        任务内容文本。
    done : bool
        是否已完成标记，True 表示已完成，False 表示未完成。
    deleted : bool
        是否已逻辑删除标记，True 表示已删除，False 表示正常状态。
    created_at : float
        任务创建时间戳（Unix 时间戳，秒级）。
    updated_at : float
        任务最后更新时间戳（Unix 时间戳，秒级）。
    deleted_at : float
        任务逻辑删除时间戳（Unix 时间戳，秒级），未删除时为 None。
    """

    def __init__(self, text="", done=False, id=None, created_at=None, updated_at=None, deleted=False, deleted_at=None):
        """
        初始化任务对象。

        Parameters
        ----------
        text : str, optional
            任务内容文本，默认为空字符串。
        done : bool, optional
            是否已完成标记，默认为 False。
        id : str, optional
            任务唯一标识符，若不传入则自动生成 UUID4。
        created_at : float, optional
            创建时间戳，若不传入则使用当前时间。
        updated_at : float, optional
            最后更新时间戳，若不传入则使用当前时间。
        deleted : bool, optional
            是否已逻辑删除标记，默认为 False。
        deleted_at : float, optional
            逻辑删除时间戳，未删除时为 None。
        """
        now = time.time()
        self.id = id if id else str(uuid.uuid4())
        self.text = text.strip() if text else ""
        self.done = bool(done)
        self.deleted = bool(deleted)
        self.created_at = created_at if created_at else now
        self.updated_at = updated_at if updated_at else now
        self.deleted_at = deleted_at

    def mark_done(self, done=True):
        """
        标记任务为完成或未完成状态，并刷新更新时间。

        Parameters
        ----------
        done : bool, optional
            True 表示标记为完成，False 表示标记为未完成，默认 True。

        Returns
        -------
        None
        """
        self.done = bool(done)
        self.updated_at = time.time()

    def update_text(self, text):
        """
        更新任务内容文本，并刷新更新时间。

        Parameters
        ----------
        text : str
            新的任务内容，前后空白会被去除。

        Returns
        -------
        bool
            如果内容发生实质变化返回 True，否则返回 False。
        """
        new_text = (text or "").strip()
        if new_text != self.text:
            self.text = new_text
            self.updated_at = time.time()
            return True
        return False

    def mark_deleted(self, deleted=True):
        """
        标记任务为逻辑删除或撤销删除状态，并刷新更新时间。

        Parameters
        ----------
        deleted : bool, optional
            True 表示标记为删除，False 表示撤销删除，默认 True。

        Returns
        -------
        None
        """
        self.deleted = bool(deleted)
        if deleted:
            self.deleted_at = time.time()
        else:
            self.deleted_at = None
        self.updated_at = time.time()

    def to_dict(self):
        """
        将任务对象转换为字典，便于序列化为 JSON。

        Returns
        -------
        dict
            包含 id、text、done、deleted、created_at、updated_at、deleted_at 字段的字典。
        """
        return {
            "id": self.id,
            "text": self.text,
            "done": self.done,
            "deleted": self.deleted,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "deleted_at": self.deleted_at,
        }

    @classmethod
    def from_dict(cls, data):
        """
        从字典构造任务对象。

        Parameters
        ----------
        data : dict
            包含任务字段的字典，通常来自 JSON 反序列化。

        Returns
        -------
        Todo
            根据字典内容生成的任务对象。

        Notes
        -----
        对于缺失字段会使用默认值，保证向后兼容。
        """
        if not isinstance(data, dict):
            raise TypeError("from_dict 仅接受 dict 类型参数")
        return cls(
            text=data.get("text", ""),
            done=data.get("done", False),
            id=data.get("id"),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
            deleted=data.get("deleted", False),
            deleted_at=data.get("deleted_at"),
        )

    def __repr__(self):
        """返回任务对象的可读字符串表示，便于调试输出。"""
        return "Todo(id={0}, text={1!r}, done={2}, deleted={3})".format(self.id[:8], self.text, self.done, self.deleted)
