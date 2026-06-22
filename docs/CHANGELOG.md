# 变更记录 (CHANGELOG)

本文件记录 TODO-List 桌面应用的所有功能迭代。格式遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)，使用 [语义化版本](https://semver.org/lang/zh-CN/) 进行版本号管理。

---

## [未发布 / 最新]

> 当前最新版本，按功能持续迭代。以下按迭代顺序列出。

---

## v1.4 — 导出清单功能

### 新增
- **导出 CSV 表格**：`src/storage.py` 新增 `export_to_csv(file_path)` 方法。  
  - 使用 UTF-8 + BOM 编码，保证 Excel 中文不乱码  
  - 输出列：序号、状态、内容、创建时间、最后更新时间
- **导出纯文本清单**：`src/storage.py` 新增 `export_to_text(file_path)` 方法。  
  - 人类可读格式，含标题、统计信息、时间戳  
  - 分「未完成」「已完成」两节展示
- **GUI 「导出清单」按钮**：`src/gui.py` 底部状态栏新增「导出清单」按钮（状态栏与「清除已完成」之间）  
  - 调用系统文件保存对话框，默认文件名带时间戳  
  - 支持按扩展名自动选择 CSV 或 TXT 导出格式  
  - 导出成功/失败通过 QMessageBox 提示

### 修改
- `src/gui.py` 补充导入：`QFileDialog`、`datetime`、`os`  
- `src/gui.py` 底部布局由「统计 + 清除」扩展为「统计 + 导出 + 清除」三列

### 验证
- ✅ `py_compile` 语法检查通过  
- ✅ 手工单元测试：CSV / TXT 导出格式正确  
- ✅ PyInstaller 重新打包为 onedir 模式 exe，启动正常

### 相关文件
- [src/storage.py](file:///d:/TODO-List/src/storage.py) — `export_to_csv()`、`export_to_text()`  
- [src/gui.py](file:///d:/TODO-List/src/gui.py) — 底部导出按钮与 `_handle_export()` 事件处理器

---

## v1.3 — 打包为 Windows exe

### 新增
- 使用 **PyInstaller** 将应用打包为可独立运行的桌面程序  
- onedir 模式产物：`dist\TodoList-onedir\TodoList\TodoList.exe`  
- 打包产物包含：Python 运行时、PyQt5 全部 DLL / 插件、SQLite 运行库

### 技术要点
| 项 | 值 |
|----|----|
| 打包命令 | `pyinstaller --noconfirm --clean --windowed --name TodoList --distpath dist\TodoList-onedir --workpath build --specpath build main.py` |
| 模式 | onedir（启动快、稳定，推荐） |
| 产物大小 | ~70 MB（解压后） |
| 分发方式 | 整个 `TodoList` 文件夹压缩分发 |

### 使用说明
1. 进入 `dist\TodoList-onedir\TodoList\`  
2. 双击 `TodoList.exe` 运行  
3. 勿单独移动 exe，需保留 `_internal` 目录

---

## v1.2 — 数据持久化升级为 SQLite

### 背景
v1.1 使用 JSON 文件 (`data/todos.json`) 存储任务数据，存在以下问题：
- 每次保存需要覆盖整份文件，任务量大时性能不佳
- 无法按字段高效查询与排序
- 无事务支持，极端情况下可能损坏数据
- 不便于后续扩展更复杂的查询功能

### 新增
- **SQLite 表结构**：`todos (id TEXT PK, text TEXT, done INTEGER, created_at REAL, updated_at REAL)`
- **索引**：`idx_done`、`idx_created_at`、`idx_done_created`，支持按状态 + 时间快速检索
- **新 API**：`add_todo()` / `update_todo()` / `update_done()` / `delete_todo()` / `clear_done()` / `count_stats()` / `query()`
- **兼容性 API**：`save(todos)` / `load()` 保留，便于上层 GUI 平滑迁移

### 修改
- `src/storage.py` 由 JSON 读写重写为 SQLite 持久化
- `src/gui.py` 调用层改为逐条变更模式（更高效，避免整体覆盖写）
- 数据文件：`data/todos.db`（首次运行自动建表）

### 数据库特点
- Python 标准库 `sqlite3` 模块，零额外依赖
- 自动建表与建索引，首次运行即就绪
- 所有写操作支持事务，保证数据一致性
- 可使用 DB Browser for SQLite 直接查看/备份/迁移

---

## v1.1 — 过滤、编辑、清除已完成

### 新增
- 顶部输入框 + 添加按钮（支持回车提交）
- 过滤按钮：全部 / 未完成 / 已完成
- 任务卡片式 UI，包含：圆形复选框、任务文本、删除按钮
- 双击任务文本进入编辑模式
- 底部状态栏：实时统计总条数、未完成数、已完成数
- 「清除已完成」按钮（带确认弹窗）

### GUI 样式
- 淡紫色标题
- 白色卡片 + 淡灰分隔线
- 已完成任务文本灰色、删除线
- Hover 动效：按钮边框变化、删除按钮高亮

---

## v1.0 — 初版 (JSON 存储)

### 功能
- 添加任务
- 标记完成/未完成
- 删除任务
- JSON 文件持久化（`data/todos.json`）

### 技术
- Python 3 + PyQt5
- 简单的单窗口 GUI

---

## 已验证的测试清单

| 功能 | 测试步骤 | 预期结果 |
|-----|---------|---------|
| 添加任务 | 输入 5 条任务 | 列表显示 5 条，总计数 = 5 |
| 标记完成 | 勾选 2 条 | 已完成 = 2，未完成 = 3 |
| 过滤切换 | 依次点击三个按钮 | 视图正确切换 |
| 编辑任务 | 双击某条，修改文本，回车 | 文本更新，updated_at 刷新 |
| 删除任务 | 删除 1 条 | 列表减少 1 条 |
| 导出 CSV | 导出后用记事本/Excel 打开 | 中文不乱码，包含 5 列 |
| 导出 TXT | 导出后用记事本打开 | 格式整洁，含统计信息与分节 |
| 清除已完成 | 点击「清除已完成」，确认 | 已完成项被删除，剩余任务数正确 |
| 持久化 | 关闭应用，重新打开 | 任务数据完整保留 |
| 打包后运行 | 双击 dist 目录的 TodoList.exe | 正常启动，功能一致 |

---

## 目录速览

```
TODO-List/
|-- main.py              # 启动入口
|-- requirements.txt     # 依赖：PyQt5
|-- src/
|   |-- models.py        # Todo 数据对象
|   |-- storage.py       # SQLite 持久化 + 导出
|   |-- gui.py           # PyQt5 主窗口
|-- data/
|   |-- todos.db         # SQLite 数据库（运行时创建）
|-- docs/
|   |-- README.md        # 项目说明文档
|   |-- CHANGELOG.md     # 本文件
|-- dist/TodoList-onedir/TodoList/TodoList.exe  # 打包产物
```
