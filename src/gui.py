# -*- coding: utf-8 -*-
"""
图形界面模块
使用 PyQt5 构建 TODO-List 桌面控件，提供简洁美观的交互界面。
"""

from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIcon, QKeySequence, QFont
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QListWidget,
    QListWidgetItem,
    QCheckBox,
    QLabel,
    QFrame,
    QButtonGroup,
    QScrollArea,
    QMessageBox,
    QFileDialog,
    QSizePolicy,
)
import datetime
import os

from .models import Todo
from .storage import TodoStorage

# 过滤模式常量，用于控制任务列表展示范围
FILTER_ALL = "all"
FILTER_ACTIVE = "active"
FILTER_DONE = "done"

# 分组模式常量，用于控制任务列表分组方式
GROUP_NONE = "none"
GROUP_BY_DATE = "by_date"
GROUP_BY_MONTH = "by_month"


class TodoItemWidget(QFrame):
    """
    单条任务的可视化控件。

    包含一个复选框、任务文本标签和删除按钮。支持双击文本进入编辑模式。
    """

    def __init__(self, todo, on_toggle=None, on_delete=None, on_update=None, parent=None):
        """
        初始化单条任务控件。

        Parameters
        ----------
        todo : Todo
            任务对象，用于渲染当前控件的状态。
        on_toggle : callable, optional
            复选框状态切换时的回调，签名为 ``on_toggle(todo)``。
        on_delete : callable, optional
            删除按钮点击时的回调，签名为 ``on_delete(todo)``。
        on_update : callable, optional
            任务文本编辑完成后的回调，签名为 ``on_update(todo, new_text)``。
        parent : QWidget, optional
            父对象，用于 Qt 对象树管理。
        """
        super(TodoItemWidget, self).__init__(parent)
        self.todo = todo
        self.on_toggle = on_toggle
        self.on_delete = on_delete
        self.on_update = on_update

        self.setFrameShape(QFrame.NoFrame)
        self.setStyleSheet(
            """
            TodoItemWidget {
                background-color: #ffffff;
                border-bottom: 1px solid #ececec;
            }
            TodoItemWidget:hover {
                background-color: #f7f7fb;
            }
            """
        )

        root_layout = QHBoxLayout(self)
        root_layout.setContentsMargins(14, 10, 14, 10)
        root_layout.setSpacing(10)

        # 复选框：标记任务完成状态
        self.checkbox = QCheckBox()
        self.checkbox.setChecked(todo.done)
        self.checkbox.setCursor(Qt.PointingHandCursor)
        self.checkbox.stateChanged.connect(self._handle_toggle)
        root_layout.addWidget(self.checkbox, 0)

        # 任务文本标签，双击可进入编辑模式
        self.text_label = QLabel(todo.text)
        self.text_label.setWordWrap(True)
        self.text_label.setTextInteractionFlags(Qt.NoTextInteraction)
        self.text_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self._apply_text_style()
        root_layout.addWidget(self.text_label, 1)

        # 编辑输入框：默认隐藏，双击标签后显示
        self.text_edit = QLineEdit(todo.text)
        self.text_edit.setPlaceholderText("请输入任务内容...")
        self.text_edit.hide()
        self.text_edit.editingFinished.connect(self._handle_edit_finished)
        root_layout.addWidget(self.text_edit, 1)

        # 删除按钮
        self.delete_btn = QPushButton("✕")
        self.delete_btn.setToolTip("删除该任务")
        self.delete_btn.setCursor(Qt.PointingHandCursor)
        self.delete_btn.setFixedSize(QSize(28, 28))
        self.delete_btn.setStyleSheet(
            """
            QPushButton {
                color: #c0392b;
                background-color: transparent;
                border: none;
                font-size: 14px;
                border-radius: 14px;
            }
            QPushButton:hover {
                background-color: #fdecea;
                color: #e74c3c;
            }
            """
        )
        self.delete_btn.clicked.connect(self._handle_delete)
        root_layout.addWidget(self.delete_btn, 0)

    def _apply_text_style(self):
        """
        根据任务完成状态应用文本样式：已完成的任务使用灰色和删除线。
        """
        if self.todo.done:
            self.text_label.setStyleSheet("color: #9aa0a6; text-decoration: line-through;")
        else:
            self.text_label.setStyleSheet("color: #2c3e50; font-size: 14px;")

    def _handle_toggle(self, state):
        """
        处理复选框状态变化事件，将完成状态同步到任务对象并刷新样式。

        Parameters
        ----------
        state : int
            Qt 复选框状态常量，``Qt.Checked`` 表示选中。
        """
        self.todo.mark_done(state == Qt.Checked)
        self._apply_text_style()
        if self.on_toggle:
            self.on_toggle(self.todo)

    def _handle_delete(self):
        """
        处理删除按钮点击事件，通过回调删除对应任务。
        """
        if self.on_delete:
            self.on_delete(self.todo)

    def enter_edit_mode(self):
        """
        进入编辑模式，隐藏文本标签并显示输入框，同时将焦点切换到输入框。
        """
        self.text_label.hide()
        self.text_edit.setText(self.todo.text)
        self.text_edit.show()
        self.text_edit.setFocus()
        self.text_edit.selectAll()

    def _handle_edit_finished(self):
        """
        处理编辑完成事件（回车或失去焦点），更新任务内容后退出编辑模式。
        """
        new_text = self.text_edit.text().strip()
        if new_text and new_text != self.todo.text:
            self.todo.update_text(new_text)
            self.text_label.setText(new_text)
            if self.on_update:
                self.on_update(self.todo, new_text)
        self.text_edit.hide()
        self.text_label.show()

    def mouseDoubleClickEvent(self, event):
        """
        双击控件时进入编辑模式，双击其他位置（如按钮）由子控件自己处理。

        Parameters
        ----------
        event : QMouseEvent
            Qt 鼠标事件对象。
        """
        if event.button() == Qt.LeftButton:
            self.enter_edit_mode()
        super(TodoItemWidget, self).mouseDoubleClickEvent(event)


class GroupHeaderWidget(QFrame):
    """
    分组标题控件，用于在任务列表中显示日期或月份分组。

    显示分组名称（如"今天"、"昨天"、"2026年6月"）和该组的任务数量。
    """

    def __init__(self, title, count, parent=None):
        """
        初始化分组标题控件。

        Parameters
        ----------
        title : str
            分组显示标题，如"今天"、"2026年6月"。
        count : int
            该分组下的任务数量。
        parent : QWidget, optional
            父对象，用于 Qt 对象树管理。
        """
        super(GroupHeaderWidget, self).__init__(parent)
        self.setFrameShape(QFrame.NoFrame)
        self.setStyleSheet(
            """
            GroupHeaderWidget {
                background-color: transparent;
            }
            """
        )

        root_layout = QHBoxLayout(self)
        root_layout.setContentsMargins(14, 6, 14, 4)
        root_layout.setSpacing(10)

        self.title_label = QLabel(title)
        self.title_label.setStyleSheet(
            "color: #5e60ce; font-size: 13px; font-weight: 600;"
        )
        root_layout.addWidget(self.title_label, 1)

        self.count_label = QLabel("({0})".format(count))
        self.count_label.setStyleSheet(
            "color: #9ca3af; font-size: 12px;"
        )
        root_layout.addWidget(self.count_label, 0)


class TodoMainWindow(QMainWindow):
    """
    TODO-List 主窗口。

    负责构建整体布局、管理任务列表的渲染和用户交互，并通过 TodoStorage
    持久化任务数据。
    """

    def __init__(self, storage=None):
        """
        初始化主窗口，包括 UI 构建、样式设置和初始数据加载。

        Parameters
        ----------
        storage : TodoStorage, optional
            数据存储实例，如不提供将使用默认路径创建新实例。
        """
        super(TodoMainWindow, self).__init__()
        self.storage = storage if storage else TodoStorage()
        self.todos = []
        self.current_filter = FILTER_ALL
        self.current_group = GROUP_NONE

        self.setWindowTitle("我的待办清单")
        self.resize(480, 620)
        self.setMinimumSize(QSize(380, 460))

        self._build_ui()
        self._apply_style()
        self._load_todos()
        self._refresh_list()

    # ------------------------------------------------------------------
    # UI 构建
    # ------------------------------------------------------------------

    def _build_ui(self):
        """
        构建并组装窗口中的所有控件。

        布局结构如下：
        - 顶部：输入框 + 添加按钮
        - 中部：过滤切换按钮组
        - 主体：任务列表（可滚动）
        - 底部：状态统计 + 清除已完成按钮
        """
        central = QWidget()
        self.setCentralWidget(central)

        layout = QVBoxLayout(central)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(14)

        # 标题
        self.title_label = QLabel("我的待办清单")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        self.title_label.setFont(title_font)
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setStyleSheet("color: #5e60ce; margin: 4px 0;")
        layout.addWidget(self.title_label)

        # 输入区
        input_container = QHBoxLayout()
        input_container.setSpacing(10)

        self.input_edit = QLineEdit()
        self.input_edit.setPlaceholderText("输入新任务后按回车或点击添加...")
        self.input_edit.returnPressed.connect(self._handle_add_todo)
        input_container.addWidget(self.input_edit, 1)

        self.add_btn = QPushButton("添加")
        self.add_btn.setCursor(Qt.PointingHandCursor)
        self.add_btn.setFixedHeight(36)
        self.add_btn.clicked.connect(self._handle_add_todo)
        input_container.addWidget(self.add_btn, 0)

        layout.addLayout(input_container)

        # 过滤切换
        filter_container = QHBoxLayout()
        filter_container.setSpacing(6)

        self.filter_group = QButtonGroup(self)
        self.filter_group.setExclusive(True)

        self.btn_all = self._create_filter_button("全部", FILTER_ALL, True)
        self.btn_active = self._create_filter_button("未完成", FILTER_ACTIVE, False)
        self.btn_done = self._create_filter_button("已完成", FILTER_DONE, False)

        filter_container.addWidget(self.btn_all)
        filter_container.addWidget(self.btn_active)
        filter_container.addWidget(self.btn_done)

        filter_container.addStretch(1)

        # 分组切换按钮
        self.group_group = QButtonGroup(self)
        self.group_group.setExclusive(True)

        self.btn_group_none = self._create_group_button("不分", GROUP_NONE, True)
        self.btn_group_date = self._create_group_button("按日期", GROUP_BY_DATE, False)
        self.btn_group_month = self._create_group_button("按月份", GROUP_BY_MONTH, False)

        filter_container.addWidget(self.btn_group_none)
        filter_container.addWidget(self.btn_group_date)
        filter_container.addWidget(self.btn_group_month)

        layout.addLayout(filter_container)

        # 任务列表
        self.list_widget = QListWidget()
        self.list_widget.setFrameShape(QFrame.NoFrame)
        self.list_widget.setStyleSheet(
            """
            QListWidget {
                background-color: #ffffff;
                border-radius: 10px;
                padding: 4px;
            }
            QListWidget::item {
                padding: 0px;
                margin: 0px;
            }
            QScrollBar:vertical {
                background: transparent;
                width: 8px;
            }
            QScrollBar::handle:vertical {
                background: #c7c9d1;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical:hover {
                background: #8a8f9b;
            }
            """
        )
        layout.addWidget(self.list_widget, 1)

        # 底部：状态统计 + 导出按钮 + 清除按钮
        bottom_container = QHBoxLayout()

        self.status_label = QLabel("共 0 项")
        self.status_label.setStyleSheet("color: #6b7280; font-size: 12px;")
        bottom_container.addWidget(self.status_label, 1)

        # 导出清单按钮
        self.export_btn = QPushButton("导出清单")
        self.export_btn.setCursor(Qt.PointingHandCursor)
        self.export_btn.setStyleSheet(
            """
            QPushButton {
                color: #5e60ce;
                background-color: transparent;
                border: 1px solid #c7c9d1;
                border-radius: 6px;
                padding: 4px 12px;
                font-size: 12px;
            }
            QPushButton:hover {
                color: #3f429c;
                border-color: #5e60ce;
                background-color: #eef0fa;
            }
            """
        )
        self.export_btn.clicked.connect(self._handle_export)
        bottom_container.addWidget(self.export_btn, 0)

        self.clear_done_btn = QPushButton("清除已完成")
        self.clear_done_btn.setCursor(Qt.PointingHandCursor)
        self.clear_done_btn.setStyleSheet(
            """
            QPushButton {
                color: #6b7280;
                background-color: transparent;
                border: 1px solid #d1d5db;
                border-radius: 6px;
                padding: 4px 12px;
                font-size: 12px;
            }
            QPushButton:hover {
                color: #e74c3c;
                border-color: #f5b7b1;
                background-color: #fef5f3;
            }
            """
        )
        self.clear_done_btn.clicked.connect(self._handle_clear_done)
        bottom_container.addWidget(self.clear_done_btn, 0)

        layout.addLayout(bottom_container)

    def _create_filter_button(self, text, mode, checked=False):
        """
        创建过滤切换按钮，并加入到按钮组中。

        Parameters
        ----------
        text : str
            按钮显示文本。
        mode : str
            对应过滤模式常量。
        checked : bool, optional
            初始是否选中。

        Returns
        -------
        QPushButton
            创建完成的按钮实例。
        """
        btn = QPushButton(text)
        btn.setCheckable(True)
        btn.setChecked(checked)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setProperty("filter_mode", mode)
        btn.setMinimumHeight(30)
        btn.clicked.connect(lambda _=False, m=mode: self._handle_filter_changed(m))
        self.filter_group.addButton(btn)
        return btn

    def _create_group_button(self, text, mode, checked=False):
        """
        创建分组切换按钮，并加入到按钮组中。

        Parameters
        ----------
        text : str
            按钮显示文本。
        mode : str
            对应分组模式常量。
        checked : bool, optional
            初始是否选中。

        Returns
        -------
        QPushButton
            创建完成的按钮实例。
        """
        btn = QPushButton(text)
        btn.setCheckable(True)
        btn.setChecked(checked)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setProperty("group_mode", mode)
        btn.setMinimumHeight(30)
        btn.clicked.connect(lambda _=False, m=mode: self._handle_group_changed(m))
        self.group_group.addButton(btn)
        return btn

    def _apply_style(self):
        """
        应用全局样式表，为窗口、输入框、按钮等设置统一的现代外观。
        """
        self.setStyleSheet(
            """
            QMainWindow, QWidget {
                background-color: #f4f5fb;
            }
            QLineEdit {
                background-color: #ffffff;
                border: 1px solid #d1d5db;
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 14px;
                color: #2c3e50;
                selection-background-color: #c7d2fe;
            }
            QLineEdit:focus {
                border: 1px solid #5e60ce;
            }
            QPushButton {
                background-color: #5e60ce;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 6px 18px;
                font-size: 13px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #4c4fb5;
            }
            QPushButton:pressed {
                background-color: #3f429c;
            }
            QPushButton:checked {
                background-color: #5e60ce;
                color: white;
            }
            QPushButton[filter_mode="all"]:checked,
            QPushButton[filter_mode="active"]:checked,
            QPushButton[filter_mode="done"]:checked {
                background-color: #5e60ce;
                color: white;
                border: 1px solid #5e60ce;
            }
            QPushButton[filter_mode="all"],
            QPushButton[filter_mode="active"],
            QPushButton[filter_mode="done"] {
                background-color: #ffffff;
                color: #374151;
                border: 1px solid #d1d5db;
                padding: 4px 14px;
                border-radius: 14px;
                font-size: 12px;
            }
            QPushButton[filter_mode="all"]:hover,
            QPushButton[filter_mode="active"]:hover,
            QPushButton[filter_mode="done"]:hover {
                border-color: #5e60ce;
                color: #5e60ce;
            }
            QPushButton[group_mode="none"]:checked,
            QPushButton[group_mode="by_date"]:checked,
            QPushButton[group_mode="by_month"]:checked {
                background-color: #10b981;
                color: white;
                border: 1px solid #10b981;
            }
            QPushButton[group_mode="none"],
            QPushButton[group_mode="by_date"],
            QPushButton[group_mode="by_month"] {
                background-color: #ffffff;
                color: #374151;
                border: 1px solid #d1d5db;
                padding: 4px 12px;
                border-radius: 14px;
                font-size: 12px;
            }
            QPushButton[group_mode="none"]:hover,
            QPushButton[group_mode="by_date"]:hover,
            QPushButton[group_mode="by_month"]:hover {
                border-color: #10b981;
                color: #10b981;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border-radius: 9px;
                border: 2px solid #c7c9d1;
                background: white;
            }
            QCheckBox::indicator:hover {
                border-color: #5e60ce;
            }
            QCheckBox::indicator:checked {
                background: #5e60ce;
                border: 2px solid #5e60ce;
                image: none;
            }
            QCheckBox::indicator:checked::after {
                /* 使用样式中的勾选标记由 Qt 绘制 */
            }
            """
        )

    # ------------------------------------------------------------------
    # 数据与列表管理
    # ------------------------------------------------------------------

    def _load_todos(self):
        """
        从持久化存储中读取任务列表。

        Notes
        -----
        读取失败时不会抛出异常，而是以空列表继续运行，保证应用可用性。
        """
        self.todos = self.storage.load()

    def _persist(self):
        """
        将当前任务列表保存到持久化存储。
        """
        self.storage.save(self.todos)

    def _filtered_todos(self):
        """
        根据当前过滤模式返回需要显示的任务列表。

        使用 SQLite 存储层的 ``query`` 接口进行高效查询，
        借助 ``idx_done_created`` 复合索引提高过滤 + 排序性能。

        Returns
        -------
        list of Todo
            经过过滤后的任务对象列表。
        """
        if self.current_filter == FILTER_ACTIVE:
            return self.storage.query(done=False)
        if self.current_filter == FILTER_DONE:
            return self.storage.query(done=True)
        return self.storage.load()

    def _get_date_key(self, timestamp, mode):
        """
        根据时间戳和分组模式生成分组键。

        Parameters
        ----------
        timestamp : float
            Unix 时间戳。
        mode : str
            分组模式，应为 ``GROUP_BY_DATE`` 或 ``GROUP_BY_MONTH``。

        Returns
        -------
        tuple
            (key, title) 元组，key 用于分组排序，title 用于显示。
        """
        dt = datetime.datetime.fromtimestamp(timestamp)
        today = datetime.date.today()
        todo_date = dt.date()

        if mode == GROUP_BY_DATE:
            delta = (today - todo_date).days
            if delta == 0:
                return (0, "今天")
            elif delta == 1:
                return (1, "昨天")
            elif delta == 2:
                return (2, "前天")
            elif delta < 7:
                week_days = ["周日", "周一", "周二", "周三", "周四", "周五", "周六"]
                return (delta, week_days[todo_date.weekday()])
            else:
                return (100 + todo_date.toordinal(), "{0}年{1}月{2}日".format(
                    dt.year, dt.month, dt.day
                ))
        elif mode == GROUP_BY_MONTH:
            return (dt.year * 100 + dt.month, "{0}年{1}月".format(dt.year, dt.month))
        return (0, "")

    def _group_todos(self, todos):
        """
        根据当前分组模式对任务列表进行分组。

        Parameters
        ----------
        todos : list of Todo
            待分组的任务列表。

        Returns
        -------
        list of tuples
            每个元素为 (title, key, todo_list)，按时间倒序排列。
        """
        if self.current_group == GROUP_NONE:
            return [("", 0, todos)]

        groups = {}
        for todo in todos:
            key, title = self._get_date_key(todo.created_at, self.current_group)
            if key not in groups:
                groups[key] = {"title": title, "todos": []}
            groups[key]["todos"].append(todo)

        sorted_groups = sorted(groups.items(), key=lambda x: x[0])
        return [(g["title"], k, g["todos"]) for k, g in sorted_groups]

    def _refresh_list(self):
        """
        根据当前过滤模式和分组模式刷新列表视图，并更新底部统计信息。

        Notes
        -----
        该方法会先清空列表再重新构建，对于小规模数据已经足够高效；
        如果未来需要支持大规模任务，可以改为增量更新。
        """
        self.list_widget.clear()
        visible = self._filtered_todos()

        if not visible:
            empty_item = QListWidgetItem(self.list_widget)
            empty_label = QLabel(self._empty_hint_text())
            empty_label.setAlignment(Qt.AlignCenter)
            empty_label.setStyleSheet("color: #9ca3af; padding: 30px 0; font-size: 13px;")
            empty_item.setSizeHint(empty_label.sizeHint())
            self.list_widget.addItem(empty_item)
            self.list_widget.setItemWidget(empty_item, empty_label)
            self._update_status_label()
            return

        grouped = self._group_todos(visible)
        for title, _, todo_list in grouped:
            if title:
                header_item = QListWidgetItem(self.list_widget)
                header_widget = GroupHeaderWidget(title, len(todo_list))
                header_item.setSizeHint(header_widget.sizeHint())
                self.list_widget.addItem(header_item)
                self.list_widget.setItemWidget(header_item, header_widget)

            for todo in todo_list:
                item = QListWidgetItem(self.list_widget)
                widget = TodoItemWidget(
                    todo,
                    on_toggle=self._handle_todo_toggled,
                    on_delete=self._handle_todo_deleted,
                    on_update=self._handle_todo_updated,
                )
                item.setSizeHint(widget.sizeHint())
                self.list_widget.addItem(item)
                self.list_widget.setItemWidget(item, widget)

        self._update_status_label()

    def _empty_hint_text(self):
        """
        根据当前过滤模式返回空列表时的提示文案。

        Returns
        -------
        str
            空状态提示文本。
        """
        if self.current_filter == FILTER_ACTIVE:
            return "太棒了，当前没有未完成的任务！"
        if self.current_filter == FILTER_DONE:
            return "还没有已完成的任务。"
        return "暂无任务，在上方输入框添加你的第一项吧！"

    def _update_status_label(self):
        """
        计算并更新底部状态栏的统计信息文本。

        使用 SQLite 聚合函数直接统计，避免在 UI 线程做 list 遍历。
        """
        stats = self.storage.count_stats()
        total = stats["total"]
        active = stats["active"]
        done = stats["done"]
        self.status_label.setText("共 {0} 项 · 未完成 {1} · 已完成 {2}".format(total, active, done))

    # ------------------------------------------------------------------
    # 事件处理
    # ------------------------------------------------------------------

    def _handle_add_todo(self):
        """
        处理添加任务事件：获取输入内容并添加到任务列表，持久化到 SQLite。

        输入为空字符串或仅包含空白时会被忽略并弹出提示。
        """
        text = self.input_edit.text().strip()
        if not text:
            self.input_edit.setFocus()
            return
        new_todo = Todo(text=text)
        # 持久化到数据库，成功后再加入内存列表，避免出现“数据库失败但内存有”的不一致
        if self.storage.add_todo(new_todo):
            self.todos.insert(0, new_todo)
        self.input_edit.clear()
        self._refresh_list()

    def _handle_todo_toggled(self, todo):
        """
        任务完成状态切换时的回调：更新数据库中该任务的完成状态并刷新列表。

        Parameters
        ----------
        todo : Todo
            状态被改变的任务对象。
        """
        self.storage.update_done(todo)
        self._refresh_list()

    def _handle_todo_deleted(self, todo):
        """
        任务删除时的回调：从数据库与内存列表中移除对应任务。

        Parameters
        ----------
        todo : Todo
            要删除的任务对象。
        """
        self.storage.delete_todo(todo)
        try:
            self.todos.remove(todo)
        except ValueError:
            pass
        self._refresh_list()

    def _handle_todo_updated(self, todo, new_text):
        """
        任务内容更新后的回调：更新数据库中该任务的文本内容。

        Parameters
        ----------
        todo : Todo
            被更新的任务对象。
        new_text : str
            更新后的任务文本内容。
        """
        self.storage.update_todo(todo)

    def _handle_filter_changed(self, mode):
        """
        过滤模式切换时的回调，刷新列表显示。

        Parameters
        ----------
        mode : str
            新的过滤模式，应为 ``FILTER_ALL`` / ``FILTER_ACTIVE`` / ``FILTER_DONE`` 之一。

        Notes
        -----
        实际数据查询借助 SQLite 的 ``idx_done_created`` 复合索引完成。
        """
        self.current_filter = mode
        self._refresh_list()

    def _handle_group_changed(self, mode):
        """
        分组模式切换时的回调，刷新列表显示。

        Parameters
        ----------
        mode : str
            新的分组模式，应为 ``GROUP_NONE`` / ``GROUP_BY_DATE`` / ``GROUP_BY_MONTH`` 之一。
        """
        self.current_group = mode
        self._refresh_list()

    def _handle_export(self):
        """
        处理「导出清单」按钮事件：弹出文件保存对话框，
        让用户选择导出格式（CSV 或 TXT）并导出所有任务。
        """
        stats = self.storage.count_stats()
        if stats["total"] == 0:
            QMessageBox.information(self, "提示", "当前没有任务可导出。")
            return
        # 默认文件名：待办清单_YYYYMMDD_HHMMSS
        default_name = "待办清单_{0}".format(datetime.datetime.now().strftime("%Y%m%d_%H%M%S"))
        default_dir = os.path.join(os.path.expanduser("~"), "Documents")
        if not os.path.isdir(default_dir):
            default_dir = os.path.expanduser("~")
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "导出待办清单",
            os.path.join(default_dir, default_name + ".csv"),
            "CSV 表格 (*.csv);;文本文件 (*.txt);;所有文件 (*.*)",
        )
        if not file_path:
            return
        # 根据扩展名选择导出方式；无扩展名默认使用 CSV
        ext = os.path.splitext(file_path)[1].lower()
        if ext == ".csv":
            count = self.storage.export_to_csv(file_path)
            fmt = "CSV 表格"
        elif ext == ".txt":
            count = self.storage.export_to_text(file_path)
            fmt = "文本文件"
        else:
            # 未指定扩展名或不支持：默认追加 .csv 并按 CSV 导出
            file_path = file_path + ".csv"
            count = self.storage.export_to_csv(file_path)
            fmt = "CSV 表格"
        if count > 0:
            QMessageBox.information(
                self, "导出成功", "已成功导出 {0} 项 ({1})：\n\n{2}".format(count, fmt, file_path)
            )
        elif count == 0 and os.path.isfile(file_path):
            # 清单为空但已成功写出空文件（仅表头/提示）
            QMessageBox.information(self, "导出成功", "当前清单为空，已导出 {0}：\n\n{1}".format(fmt, file_path))
        else:
            QMessageBox.warning(self, "导出失败", "导出文件时出现问题，请检查路径是否有权限写入。")

    def _handle_clear_done(self):
        """
        清除所有已完成的任务，在真正删除前会进行确认弹窗提示。
        """
        stats = self.storage.count_stats()
        done_count = stats["done"]
        if done_count == 0:
            QMessageBox.information(self, "提示", "当前没有已完成的任务可清除。")
            return
        reply = QMessageBox.question(
            self,
            "确认清除",
            "确定要清除 {0} 项已完成任务？此操作不可撤销。".format(done_count),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            self.storage.clear_done()
            self.todos = [t for t in self.todos if not t.done]
            self._refresh_list()


def run_app():
    """
    启动 TODO-List 应用程序的顶层入口。

    该函数会创建 QApplication 与主窗口，并进入事件循环。
    在脚本直接运行或被外部调用时都可直接使用。

    Returns
    -------
    int
        Qt 应用退出码，通常 ``0`` 表示正常退出。
    """
    import sys

    app = QApplication(sys.argv)
    # 设置字体以获得更好的中文字体表现
    font = app.font()
    font.setPointSize(10)
    app.setFont(font)
    window = TodoMainWindow()
    window.show()
    return app.exec_()
