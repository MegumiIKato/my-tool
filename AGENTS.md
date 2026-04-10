# Agent 指南 (AGENTS.md)

本文件为在此代码库中工作的 AI 代理提供开发规范和操作指南。

## 1. 项目概述

这是一个基于 Python 的图像标注数据（Labelme 格式）处理工具箱，当前提供 6 个工具，并在图形化界面中按“统计、清理、检查、抽样”四个大类进行归类展示：

| 分类 | 工具 | 文件 | 功能 | 状态 |
|------|------|------|------|------|
| 统计 | 文件计数与匹配统计 | `tools/image_count.py` | 统计图片/JSON配对数量 | ✅ 已完成 |
| 统计 | 标签出现次数统计 | `tools/label_counter.py` | 统计指定标签在每个 JSON 文件中的出现次数 | ✅ 已完成 |
| 清理 | 孤立文件清理 | `tools/orphan_image_cleaner.py` | 清理孤立的图片/JSON文件 | ✅ 已完成 |
| 检查 | 标签正确性检查 | `tools/label_validator.py` | 校验 JSON 中的标签是否合法 | ✅ 已完成 |
| 检查 | 多边形重叠检查 | `tools/polygon_overlap_checker.py` | 检测多边形标注重叠并导出问题副本与报告 | ✅ 已完成 |
| 抽样 | 检查抽样 | `tools/image_json_sampler.py` | 从数据集中抽样检查 | ✅ 已完成 |

---

### 统一图片格式

所有工具统一支持的图片格式：

```python
IMAGE_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.tif', '.tiff')
```

**注意：** 修改 `core/file_scanner.py` 中的 `IMAGE_EXTENSIONS` 会影响所有工具。

---

### 已实现功能详情

#### 统计类

##### 1. 文件计数与匹配统计

- 选择数据文件夹路径
- 最内层文件夹作为独立统计单元
- 自动识别图片格式：jpg, jpeg, png, tif, tiff
- 统计各后缀文件数量及总计
- 导出 Excel 结果文件（`文件计数统计结果.xlsx`）

##### 2. 标签出现次数统计

- 支持上传自定义标签列表
- 支持在 GUI 面板中手动输入一个或多个标签
- 支持格式：csv, txt, xlsx, xls
- 标签文件第一列列名必须为 `label`
- 手动输入支持换行、中文/英文逗号、中文/英文分号分隔多个标签
- 若同时上传标签文件和手动输入标签，优先使用文件内标签
- 提供空白模板下载功能
- 按上传文件中的原始顺序为每个标签生成一列
- 手动输入时按首次出现顺序去重后生成报告列
- 按 JSON 文件逐行统计各标签出现次数，未出现显示为 `0`
- 输出 xlsx 格式统计报告 `标签出现次数统计报告.xlsx`

#### 清理类

##### 3. 孤立文件清理

- 支持两种清理模式：删除孤立图片 / 删除孤立JSON
- 最内层文件夹内独立配对判断（跨文件夹不配对）
- **特殊配对检测**：同名多格式图片+JSON（如 `1.jpg` + `1.png` + `1.json`）
- 特殊配对不删除，在报告中列出详情供用户手动处理
- 清理前弹窗确认，弹窗需绑定主窗口、居中显示并保持统一样式
- 支持图片格式：jpg, jpeg, png, tif, tiff

#### 检查类

##### 4. 标签正确性检查

- 支持上传自定义标签列表
- 支持在 GUI 面板中手动输入一个或多个标签
- 支持格式：csv, txt, xlsx, xls
- 标签文件第一列列名必须为 `label`
- 手动输入支持换行、中文/英文逗号、中文/英文分号分隔多个标签
- 若同时上传标签文件和手动输入标签，优先使用文件内标签
- 提供空白模板下载功能
- “格式说明”弹窗需使用项目统一字体与默认界面样式，不使用额外等宽字体
- 输出 xlsx 格式检查报告 `标签校验报告.xlsx`
- 统计字段中 `error_count` 表示问题文件数，`error_item_count` 表示问题条目数

##### 5. 多边形重叠检查

- 支持递归扫描目录中的 Labelme JSON 文件
- 仅检查 `shape_type == 'polygon'` 且点数不少于 3 的标注
- 支持配置重叠面积阈值，默认值为 `0.1`
- 问题标签在导出副本中标记为 `[重叠] 原标签`
- 不修改原始文件，仅输出到 `重叠检查结果` 目录
- 保留原目录结构，并复制对应图片文件
- 生成 xlsx 格式检查报告 `多边形重叠检查报告.xlsx`
- GUI 中已集成为独立工具面板
- 默认会排除本次输出目录，避免把导出结果再次扫回源数据

#### 抽样类

##### 6. 检查抽样

- 从数据集中均匀分散抽取样本
- 可配置抽样数量
- 输出目录可自定义，默认在源目录创建 `抽样结果xxx` 文件夹
- 统计抽样结果中的标签（shapes）总数
- 抽样复制时保留源目录的相对结构，避免不同子目录中的同名文件互相覆盖

---

### 项目结构

```
/Users/megumikato/CodeProject/tool/
├── main.py                      # 主程序入口
├── requirements.txt             # 依赖
├── AGENTS.md                    # 本文档
├── gui/                         # GUI模块
│   ├── __init__.py
│   ├── main_window.py           # 主窗口 + 工具面板
│   └── theme.py                 # 主题配置 + 颜色常量
├── core/                        # 核心模块
│   ├── __init__.py
│   ├── file_scanner.py          # 文件扫描公共函数
│   └── labelme.py               # Labelme JSON处理
└── tools/                       # 工具脚本
    ├── image_count.py           # 文件计数工具
    ├── orphan_image_cleaner.py  # 孤立文件清理工具
    ├── label_counter.py         # 标签出现次数统计工具
    ├── label_validator.py       # 标签校验工具
    ├── polygon_overlap_checker.py  # 多边形重叠检查
    └── image_json_sampler.py    # 检查抽样工具
```

---

## 2. 环境配置

```bash
# 安装依赖
pip install -r requirements.txt

# 依赖列表
customtkinter  # 现代UI框架
shapely        # 几何运算
tqdm           # 进度条
pyinstaller    # 打包成exe
pandas         # 数据处理
openpyxl       # Excel操作
```

Python 版本：3.10+

---

## 3. 构建与测试命令

### 运行主程序

```bash
python main.py
```

### 打包成 EXE (使用 PyInstaller)

```bash
pyinstaller --noconfirm --clean --onefile --windowed --name "LabelMe工具箱" main.py
```

### GitHub Actions 手动打包

- 工作流文件：`.github/workflows/build-labelme-toolbox.yml`
- 触发方式：GitHub `Actions` 页面手动运行 `手动打包 LabelMe 工具箱`
- 运行环境：`windows-latest`
- 构建产物：`dist/LabelMe工具箱.exe`
- Artifact 名称：`LabelMe工具箱-windows-exe`
- 工作流已设置 `FORCE_JAVASCRIPT_ACTIONS_TO_NODE24: true` 以兼容 GitHub Actions Node 24 运行环境

### 代码检查

```bash
# 语法检查
python -m py_compile <文件>

# 模块导入测试
python -c "from gui.main_window import MainWindow"

# 核心模块测试
python -c "from core.file_scanner import scan_all_leaf_dirs; print('OK')"

# 工具模块导入测试
python -c "from tools.image_json_sampler import run_sampler; from tools.label_counter import run_label_counter; from tools.label_validator import run_validator; from tools.polygon_overlap_checker import run_polygon_overlap_check; print('OK')"
```

### TestData 验证

当前仓库可使用 `TestData/` 做基础功能验证：

- 文件计数：`81` 组图片/JSON 成功配对
- 标签校验：可通过自定义标签列表验证问题文件数与问题条目数口径
- 标签校验：可额外验证仅手动输入标签、文件与手动输入同时提供时文件优先的行为
- 标签出现次数统计：可通过自定义标签列表验证报告列顺序与每个 JSON 的标签计数结果
- 标签出现次数统计：可额外验证手动输入标签的分隔解析、去重顺序，以及文件优先逻辑
- 多边形重叠检查：当前数据集中可检出 `2` 个问题文件
- 抽样：可验证复制结果与 shapes 统计
- 孤立文件清理：建议复制 `TestData/` 后额外构造孤立图片、孤立 JSON、特殊配对进行验证，避免直接改动原始测试集

---

## 4. 代码风格规范

### 4.1 导入规范

```python
# 标准库
import os
import json
import sys
import threading
import time

# 第三方库
import customtkinter as ctk
from tkinter import filedialog, messagebox
from pathlib import Path
from shapely.geometry import Polygon
from openpyxl import Workbook

# 本地模块
from gui.theme import *
from core.file_scanner import IMAGE_EXTENSIONS, scan_all_leaf_dirs
from tools.image_count import run_count
```

导入顺序：标准库 → 第三方库 → 本地模块，每组之间空行分隔。

### 4.2 格式化

- 缩进：4 空格
- 行长度：推荐 < 120 字符
- 顶层代码与函数之间空 2 行
- 函数内逻辑块之间空 1 行

### 4.3 命名规范

| 类型 | 规范 | 示例 |
|------|------|------|
| 文件/模块 | 小写下划线 | `image_count.py` |
| 类 | 大驼峰 | `class MainWindow:` |
| 函数/方法 | 小写下划线 | `def scan_json_files(root_path):` |
| 变量 | 小写下划线 | `all_json_files = []` |
| 常量 | 全大写下划线 | `IMAGE_EXTENSIONS = (...)` |
| GUI控件 | 小写下划线 | `self.path_entry`, `self.btn_run` |

### 4.4 类型注解

推荐使用类型注解：

```python
def run_polygon_overlap_check(
    source_dir: str,
    threshold: float = 0.1,
    output_dir: str | None = None,
) -> tuple[str | None, str | None, dict]:
    """批量执行多边形重叠检查。"""
```

### 4.5 文档字符串

使用中文 docstring，放在函数/类内部开头：

```python
def function_name(param):
    """函数功能说明。
    
    参数:
        param: 参数说明
    
    返回:
        返回值说明
    """
```

### 4.6 错误处理

- 使用 `try/except` 捕获特定异常
- GUI 程序中异常静默处理或显示友好提示
- 文件操作必须使用 `with` 语句

```python
try:
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
except Exception as e:
    error_list.append([file_path, f"文件读取/解析失败: {str(e)}"])
```

### 4.7 GUI 代码规范 (CustomTkinter)

- 主题在 `gui/theme.py` 中统一配置
- 颜色常量使用大写命名（如 `COLOR_PRIMARY`）
- UI 布局在 `_create_xxx()` 方法中
- 业务逻辑使用私有方法（以 `_` 开头）
- 按钮文字颜色必须显式设置 `text_color="#FFFFFF"`
- 自定义弹窗统一使用主窗口内模态样式，优先复用 `create_modal_window()` 与 `create_modal_header()`
- 弹窗字体统一使用 `APP_FONT` / `APP_FONT_BOLD`，避免使用 `Courier New` 等单独指定字体

```python
class ImageCountPanel(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self._create_ui()
    
    def _create_ui(self):
        # UI 布局
        pass
    
    def _run_task(self):
        # 业务逻辑
        pass
```

### 4.8 主题文件 (theme.py)

颜色常量分组说明：

```python
# 主色调 - 按钮、链接、强调元素
COLOR_PRIMARY = "#2563EB"          # 主按钮背景色（蓝色）
COLOR_PRIMARY_HOVER = "#1D4ED8"    # 主按钮悬停色（深蓝）
COLOR_SUCCESS = "#10B981"          # 成功/完成按钮背景色（绿色）

# 背景色 - 页面、卡片、输入框
COLOR_BG_MAIN = "#F8FAFC"         # 主内容区域背景色
COLOR_BG_SIDEBAR = "#FFFFFF"      # 侧边栏背景色

# 边框色 - 分割线、输入框边框
COLOR_BORDER = "#E2E8F0"          # 边框默认色

# 文字颜色 - 标题、正文、提示
COLOR_TEXT_PRIMARY = "#1E293B"    # 主要文字颜色（深灰）
COLOR_TEXT_SECONDARY = "#64748B"  # 次要文字颜色（中灰）
COLOR_TEXT_MUTED = "#94A3B8"      # 弱化文字颜色（浅灰）

# 交互状态
COLOR_SIDEBAR_SELECTED = "#EFF6FF" # 侧边栏按钮选中背景色
```

字体配置补充说明：

- `gui/theme.py` 会按平台自动选择字体族
- Windows：`Microsoft YaHei UI`
- macOS：`PingFang SC`
- 其他平台：`Noto Sans CJK SC`
- 如遇英文下延字母（如 `g`、`p`、`y`）显示裁切，优先检查字体回退问题

### 4.9 路径处理

- 使用 `pathlib.Path` 处理路径（推荐）
- 跨平台兼容：使用 `os.path.join()` 或 `Path`
- 文件名比较使用 `.lower()` 处理大小写

### 4.10 注释规范

- 避免不必要的注释，代码自解释
- 复杂逻辑可添加行注释 `# 说明`
- 中文注释优先

---

## 5. 核心模块 (core/file_scanner.py)

### 公共常量

```python
IMAGE_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.tif', '.tiff')
```

### 公共函数

| 函数 | 功能 | 返回值 |
|------|------|--------|
| `is_image_file(filename)` | 判断是否为图片文件 | `bool` |
| `get_leaf_folders(root_path)` | 获取所有最内层文件夹 | `list[str]` |
| `scan_leaf_dir(leaf_dir)` | 扫描单个最内层文件夹配对情况 | `dict` |
| `scan_all_leaf_dirs(root_path)` | 扫描所有最内层文件夹汇总统计 | `dict` |
| `find_orphans_in_leaf(leaf_dir)` | 查找最内层文件夹中的孤立文件 | `dict` |
| `find_all_orphans(root_path)` | 扫描所有最内层文件夹的孤立文件 | `dict` |
| `scan_json_files(root_path, exclude_dirs=None)` | 递归扫描 JSON 并支持排除目录 | `Generator[Path, None, None]` |
| `scan_image_json_pairs(root_path, exclude_dirs=None)` | 递归扫描图片/JSON 配对并支持排除目录 | `dict[str, list[tuple[str, str]]]` |

### 返回数据结构

#### `scan_leaf_dir` / `scan_all_leaf_dirs`

```python
{
    'paired': int,              # 正常配对数
    'paired_names': set,        # 配对的文件名集合
    'orphan_image': int,        # 孤立图片数
    'orphan_json': int,         # 孤立JSON数
    'special_pairs': list,      # 特殊配对列表
    'image_counts': dict,       # 各格式图片数量
    'json_count': int           # JSON数量
}
```

#### `find_all_orphans`

```python
{
    'paired': int,
    'orphan_image': int,
    'orphan_json': int,
    'special_pairs': list,       # [{'folder': str, 'name': str, 'files': list}, ...]
    'orphan_image_paths': list,  # 孤立图片完整路径
    'orphan_json_paths': list,   # 孤立JSON完整路径
    'folder_count': int,
    'image_counts': dict,
    'total_json': int
}
```

### 特殊配对说明

**定义：** 同名多格式图片 + JSON（如 `1.jpg` + `1.png` + `1.json`）

**处理规则：**
- 不删除特殊配对中的任何文件
- 在扫描结果中列出详情（文件夹路径、文件名列表）
- 由用户在 GUI 中手动处理

### 配对逻辑

1. 最内层文件夹作为独立配对空间
2. 跨文件夹同名文件不参与配对
3. 配对基于文件名（不含扩展名）判断

---

## 6. 开发注意事项

1. **数据安全**：处理文件前注意备份，删除操作不可逆
2. **编码**：JSON 读写使用 `utf-8` 编码
3. **GUI 阻塞**：耗时操作使用 `threading.Thread` 避免阻塞 UI
4. **依赖管理**：新增依赖需更新 `requirements.txt`
5. **面板切换**：使用 `pack_forget()` 保留面板状态，避免重复创建
6. **图片格式**：修改 `core/file_scanner.py` 的 `IMAGE_EXTENSIONS` 会影响所有工具
7. **扫描排除策略**：新增递归扫描逻辑时，优先复用 `core/file_scanner.py` 中的公共扫描函数，并排除结果目录（如 `重叠检查结果`、抽样输出目录）
8. **使用 `pip install` 安装需要的库

---

## 7. Git 工作流

- 提交前确认代码可运行（`python -c "from gui.main_window import MainWindow"`）
- 提交信息使用中文描述修改内容
- 避免提交大型二进制文件或临时文件
- `.gitignore` 已包含 `__pycache__/`, `node_modules/`, `.vscode/`,`TestData/` 等

---

## 8. 常见任务模板

### 添加新工具面板

1. 在 `tools/` 目录确保工具脚本有 `run_xxx()` 函数供 GUI 调用
2. 在 `gui/main_window.py` 中创建工具面板类（如 `ImageCountPanel`）
3. 在侧边栏添加工具按钮和 `_on_tool_selected` 映射
4. 实现面板 UI：路径选择、参数配置、按钮、日志区域
5. 使用线程执行耗时任务，结果通过 `self.after()` 回传 UI

### 修改现有工具

1. 先阅读源码理解逻辑
2. 修改后手动测试功能
3. 如有 GUI，确保 UI 响应正常
4. 若涉及输出目录，确认不会把结果目录重新纳入后续扫描
5. 若涉及统计字段，区分“问题文件数”和“问题条目数”
6. 标签校验与标签出现次数统计中，GUI 负责决定最终标签来源（文件或手动输入）；`tools/label_validator.py` 与 `tools/label_counter.py` 的运行函数接收最终标签集合/列表，不直接处理优先级

### 多边形重叠检查工具说明

1. 工具入口函数为 `tools/polygon_overlap_checker.py` 中的 `run_polygon_overlap_check`
2. 当前标记策略为修改导出副本中的 `label`，格式：`[重叠] 原标签`
3. 不再使用 `flags` 标记重叠问题
4. 检查结果目录默认是源目录下的 `重叠检查结果`
5. 检查报告文件名为 `多边形重叠检查报告.xlsx`
6. GUI 面板位于 `gui/main_window.py` 中的 `PolygonOverlapPanel`

### 工具函数设计模式

```python
# tools/xxx.py - 纯业务逻辑，无 GUI 依赖
def run_xxx(param1, param2):
    """执行工具主逻辑
    
    参数:
        param1: 说明
        param2: 说明
    
    返回:
        result_path: 输出文件路径
        error: 错误信息，无错误返回 None
        stats: 统计数据字典
    """
    # 业务逻辑
    return result_path, error, stats


# gui/main_window.py - 工具面板类
class XxxPanel(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self._create_ui()
    
    def _create_ui(self):
        # 路径选择 + 参数配置 + 按钮 + 日志
        pass
    
    def _run_task(self):
        folder = self.path_selector.get()
        # 调用工具函数
        output_path, error, stats = run_xxx(folder, param)
        # 更新 UI
        self.after(0, lambda: self._on_complete(output_path, error, stats))
```

### 使用 core 模块的扫描函数

```python
# 推荐：从 core.file_scanner 导入公共函数
from core.file_scanner import scan_all_leaf_dirs, find_all_orphans, IMAGE_EXTENSIONS

# 扫描统计
stats = scan_all_leaf_dirs(target_dir)

# 孤立文件清理
orphans = find_all_orphans(target_dir)
files_to_delete = orphans['orphan_image_paths']  # 或 orphans['orphan_json_paths']
```
