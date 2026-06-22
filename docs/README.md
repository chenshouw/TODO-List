# TODO-List 桌面应用

一个简洁、美观、实用的桌面待办事项管理应用。基于 **Python 3 + PyQt5** 开发，数据持久化使用 **SQLite**，可通过 **PyInstaller** 打包为独立 exe。

---

## 功能特性

| 功能 | 说明 |
|-----|------|
| ✅ 添加任务 | 输入框回车或点按钮添加新任务 |
| ✅ 标记完成 | 左侧圆形复选框一键切换完成状态 |
| ✅ 编辑任务 | 双击任务文本进入编辑模式，回车提交 |
| ✅ 删除任务 | 每条任务右侧有删除按钮 |
| ✅ 过滤显示 | 全部 / 未完成 / 已完成，按状态快速切换 |
| ✅ 状态统计 | 底部实时显示总条数、未完成数、已完成数 |
| ✅ 清除已完成 | 一键清理所有已完成任务（带确认弹窗） |
| ✅ 一键导出清单 | 支持导出 CSV 表格或纯文本文件 |
| ✅ 本地数据持久化 | 数据保存到 SQLite 数据库，重启后不丢失 |

---

## 界面预览

- 标题栏：淡紫色 "我的待办清单"
- 顶部：任务输入框 + 添加按钮
- 中部：过滤切换按钮 + 任务列表（卡片式，可滚动）
- 底部：状态统计 + 导出清单 + 清除已完成

---

## 项目结构

```
TODO-List/
|-- main.py                    # 应用启动入口
|-- requirements.txt           # 依赖清单
|-- src/
|   |-- __init__.py            # 包声明
|   |-- models.py              # Todo 数据模型
|   |-- storage.py             # SQLite 持久化 + 导出
|   |-- gui.py                 # PyQt5 图形界面
|-- data/
|   |-- todos.db               # SQLite 数据库文件（运行时自动创建）
|-- docs/
|   |-- README.md              # 本说明文档
|   |-- CHANGELOG.md           # 变更记录
|-- build/                     # PyInstaller 构建临时目录（可忽略）
|-- dist/                      # 打包产物目录
    |-- TodoList-onedir/
        |-- TodoList/
            |-- TodoList.exe   # 主程序
            |-- _internal/     # Python 运行时与 PyQt5 依赖
            |-- data/          # 任务数据库目录
```

---

## 快速开始

### 方式一：直接运行源码（开发模式）

```bash
# 1. 安装依赖
pip install PyQt5

# 2. 启动应用
python main.py
```

### 方式二：使用打包好的 exe（Windows）

```
进入目录：dist\TodoList-onedir\TodoList\
双击运行：TodoList.exe
```

> ⚠️ 注意：onedir 模式下需保留 `_internal` 目录与 `TodoList.exe` 在同一目录，勿移动或删除其中的 DLL。

---

## 使用说明

| 操作 | 步骤 |
|-----|------|
| **新建任务** | 在顶部输入框输入任务内容 → 回车或点击「添加」 |
| **标记完成** | 点击任务左侧的圆形复选框，再次点击可取消 |
| **编辑任务** | 双击任务文本 → 进入编辑模式 → 修改后回车提交 |
| **删除任务** | 点击任务右侧的 ✕ 按钮 |
| **过滤显示** | 点击「全部 / 未完成 / 已完成」切换视图 |
| **导出清单** | 点击底部「导出清单」 → 选择保存位置与格式 |
| **清除已完成** | 点击底部「清除已完成」→ 确认后删除所有已完成项 |

### 导出格式

| 格式 | 扩展名 | 说明 |
|-----|--------|------|
| **CSV 表格** | `.csv` | UTF-8 + BOM 编码，**Excel 打开不乱码**。包含列：序号 / 状态 / 内容 / 创建时间 / 最后更新时间 |
| **纯文本** | `.txt` | 人类可读格式，分「未完成」「已完成」两节，带统计信息与时间戳 |

---

## 模块与 API 说明

### src.models.Todo

[models.py](file:///d:/TODO-List/src/models.py)

任务数据对象，字段：

- `id`：UUID 字符串，任务唯一标识
- `text`：任务内容文本
- `done`：布尔值，是否已完成
- `created_at`：创建时间戳（Unix 时间，秒级）
- `updated_at`：最后更新时间戳

核心方法：

| 方法 | 说明 |
|-----|------|
| `mark_done(done=True)` | 标记为完成或未完成，刷新 updated_at |
| `update_text(text)` | 更新任务文本，文本变化时返回 True |
| `to_dict()` | 转换为字典，便于序列化 |
| `Todo.from_dict(data)` | 从字典构造 Todo 对象（类方法） |

### src.storage.TodoStorage

[storage.py](file:///d:/TODO-List/src/storage.py)

**SQLite** 数据持久化管理器，默认数据库路径 `data/todos.db`。

#### 数据读写 API

| 方法 | 说明 |
|-----|------|
| `load()` | 读取全部任务列表（按创建时间倒序） |
| `add_todo(todo)` | 新增一条任务 |
| `update_todo(todo)` | 更新任务文本与更新时间 |
| `update_done(todo)` | 更新任务完成状态与更新时间 |
| `delete_todo(todo)` | 删除指定任务 |
| `clear_done()` | 清除所有已完成任务，返回删除条数 |
| `count_stats()` | 返回统计字典 `{'total', 'active', 'done'}` |
| `query(done, start_ts, end_ts)` | 按完成状态与日期区间查询（可组合使用） |
| `save(todos)` | 整表覆盖写入（兼容旧 JSON 接口） |

#### 导出 API

| 方法 | 说明 |
|-----|------|
| `export_to_csv(file_path)` | 导出 CSV 表格（UTF-8 + BOM） |
| `export_to_text(file_path)` | 导出人类可读的纯文本清单 |

### src.gui.TodoMainWindow

[gui.py](file:///d:/TODO-List/src/gui.py)

应用主窗口，负责构建 UI、处理用户交互、调用存储层。通过顶层函数 `run_app()` 启动 Qt 事件循环。

---

## 数据库结构

### todos 表

| 列名 | 类型 | 说明 |
|-----|------|------|
| `id` | TEXT | 主键，UUID 字符串 |
| `text` | TEXT | 任务内容 |
| `done` | INTEGER | 0 表示未完成，1 表示已完成 |
| `created_at` | REAL | 创建时间戳（Unix 时间，秒级） |
| `updated_at` | REAL | 最后更新时间戳 |

### 索引（提升查询性能）

| 索引名 | 列 | 用途 |
|-------|---|-----|
| `idx_done` | `done` | 按完成状态过滤 |
| `idx_created_at` | `created_at` | 按创建时间排序/区间查询 |
| `idx_done_created` | `done, created_at` | 复合索引，支持按状态 + 时间查询 |

如需直接查看数据库内容，可使用任意 SQLite 客户端（如 **DB Browser for SQLite**）打开 `data/todos.db`。

---

## 打包部署（Windows exe）

项目使用 **PyInstaller** 打包为桌面应用。

### 安装打包工具

```bash
pip install pyinstaller
```

### 打包命令（onedir 模式，推荐）

```bash
pyinstaller --noconfirm --clean --windowed ^
    --name TodoList ^
    --distpath dist\TodoList-onedir ^
    --workpath build ^
    --specpath build ^
    main.py
```

参数说明：

| 参数 | 作用 |
|-----|------|
| `--windowed` | 不显示黑色控制台窗口 |
| `--onefile` | 打包为单文件 exe（启动较慢） |
| `--onedir` | 默认模式，生成文件夹（启动快，稳定） |
| `--name` | 指定产物名称 |
| `--clean` | 构建前清理缓存 |
| `--noconfirm` | 无需交互确认 |

### 产物位置

```
dist\TodoList-onedir\TodoList\TodoList.exe
```

可将整个 `TodoList` 文件夹复制/压缩分发到其他 Windows 机器，无需安装 Python。

---

## 技术栈

| 类别 | 技术/版本 |
|-----|----------|
| **语言** | Python 3.7+（建议 3.10+） |
| **GUI 框架** | PyQt5 5.15+ |
| **数据持久化** | Python 内置 `sqlite3` 模块 + SQLite 3.x |
| **打包工具** | PyInstaller |
| **开发平台** | Windows 10/11 |

---

## 开发与测试

### 1. 代码语法检查

```bash
python -m py_compile src\models.py src\storage.py src\gui.py main.py
```

### 2. 运行应用

```bash
python main.py
```

### 3. 手动功能验证建议

1. 添加 5 条任务
2. 标记 2 条为已完成
3. 切换「未完成 / 已完成 / 全部」过滤
4. 编辑某条任务文本
5. 删除一条任务
6. 分别导出为 CSV 与 TXT，用 Excel / 记事本打开验证内容
7. 点击「清除已完成」，确认后检查剩余任务
8. 关闭应用后重新打开，验证数据持久化

---

## 常见问题

**Q：双击 exe 没反应？**  
A：确保 `TodoList.exe` 与 `_internal` 目录在同一文件夹下，勿单独移动 exe。

**Q：任务数据保存在哪里？**  
A：exe 所在目录的 `data\todos.db` 文件。

**Q：导出 CSV 后 Excel 打开出现乱码？**  
A：不会，导出使用 UTF-8 + BOM 编码，Excel 2016+ 可正确识别。

**Q：如何备份数据？**  
A：直接复制 `data\todos.db` 到安全位置即可。也可使用「导出清单」功能定期导出副本。

---

## 开发记录

详见 [CHANGELOG.md](file:///d:/TODO-List/docs/CHANGELOG.md)。

---

## License

MIT
