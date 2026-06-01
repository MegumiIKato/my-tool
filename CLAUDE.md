# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

Labelme 工具箱 — 基于 Python + CustomTkinter 的桌面 GUI 应用，用于批量处理 Labelme 标注数据。提供 6 个工具，按"统计、清理、检查、抽样"四类组织。

## 架构

三层分离架构：

```
gui/        → 展示层：CustomTkinter 面板，每个工具一个 *Panel 类
tools/      → 业务层：每个工具一个文件，入口函数统一返回 (output_path, error, stats)
core/       → 领域层：文件扫描、配对逻辑、Labelme JSON 读写，无 GUI 依赖
```

**关键依赖链**：`gui/main_window.py` → `tools/*.py` → `core/file_scanner.py` + `core/labelme.py`

- `core/__init__.py` 使用 `from .module import *` 重新导出所有内容
- `gui/__init__.py` 导出 `MainWindow` 和主题常量
- `tools/` 目录没有 `__init__.py`，依赖项目根目录在 `sys.path` 上

## 常用命令

```bash
# 安装依赖
pip install -r requirements.txt

# 运行主程序
python main.py

# 打包为 Windows EXE（CI 使用的完整命令）
pyinstaller --noconfirm --clean --onefile --windowed --name "LabelMe工具箱" --icon assets/app_icon.ico --add-data "assets;assets" main.py

# 语法检查（无测试框架，用此验证导入）
python -m py_compile main.py
python -c "from gui.main_window import MainWindow"
python -c "from core.file_scanner import scan_all_leaf_dirs; print('OK')"
python -c "from tools.image_json_sampler import run_sampler; from tools.label_counter import run_label_counter; from tools.label_validator import run_validator; from tools.polygon_overlap_checker import run_polygon_overlap_check; print('OK')"
```

无测试框架、无 linter 配置。CI 仅手动触发 (`workflow_dispatch`)，打包为 Windows EXE。

## 关键约定

### 工具函数签名

所有工具入口函数遵循统一模式：

```python
def run_xxx(param1, param2) -> tuple[str | None, str | None, dict]:
    """返回: (输出路径, 错误信息, 统计数据)"""
```

### GUI 线程模式

所有耗时操作在后台线程执行，通过 `self.after(0, callback)` 回传 UI 线程：

```python
def _run_task(self):
    threading.Thread(target=self._do_work, daemon=True).start()

def _do_work(self):
    result, error, stats = run_xxx(...)
    self.after(0, lambda: self._on_complete(result, error, stats))
```

### 面板缓存

`MainWindow.tool_panels` 字典缓存已创建的面板实例，切换工具时 `.pack_forget()` 隐藏当前面板、`.pack()` 显示目标面板，避免重复创建。

### 标签工具的输入约定

标签校验 (`label_validator.py`) 和标签统计 (`label_counter.py`)：
- 支持上传标签文件（csv/txt/xlsx/xls，第一列列名必须为 `label`）
- 支持 GUI 手动输入（换行、中英文逗号、分号分隔）
- 文件与手动输入同时提供时，**文件优先**
- GUI 层负责决定最终标签来源，工具函数只接收最终标签集合

### 扫描排除策略

递归扫描 JSON 文件时，需排除工具自身的输出目录（如 `重叠检查结果`、`抽样结果`）。使用 `core/file_scanner.py` 的 `scan_json_files(root_path, exclude_dirs)` 或 `scan_image_json_pairs(root_path, exclude_dirs)`。

## 需要注意的问题

### 路径处理

- `gui/main_window.py` 中的 `get_asset_path()` 同时处理开发环境和 PyInstaller 打包环境（`sys._MEIPASS`）的资源路径
- 打开结果文件夹时需区分平台：Windows 用 `os.startfile`，macOS 用 `subprocess.run(["open", ...])`

### 主题

- 颜色常量定义在 `gui/theme.py`，使用大写命名（`COLOR_PRIMARY` 等）
- 字体按平台自动选择：Windows → Microsoft YaHei UI，macOS → PingFang SC，Linux → Noto Sans CJK SC
- 如遇英文下延字母（g、p、y）显示裁切，检查字体回退问题
