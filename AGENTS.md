# AGENTS.md - 代码库指南

## 项目概述
这是一个用于图像标注和标签处理的 Python 工具集（主要为 Labelme 格式）。每个脚本都是独立的工具，带有 tkinter GUI 对话框。

## 工具列表

| 文件名 | 功能说明 |
|--------|----------|
| `image_json_sampler.py` | 图片-JSON 抽样工具：从多文件夹均匀抽取样本并统计标签 |
| `label_validator.py` | 标签校验工具：检查 JSON 中的标签是否在有效字典中 |
| `orphan_image_cleaner.py` | 孤儿图片清理工具：删除无对应 JSON 的图片，清理空目录 |
| `cropland_label_counter.py` | 农田标签计数器：统计 cropland 标签出现次数 |
| `polygon_overlap_checker.py` | 多边形重叠检测：检测并标记重叠的多边形标注 |
| `convert/excel_to_string.py` | Excel 转字符串：将 Excel 列数据转为分号分隔的字符串 |

---

## 构建/检查/测试命令

### 运行脚本
```bash
python image_json_sampler.py
python label_validator.py
python orphan_image_cleaner.py
python cropland_label_counter.py
python polygon_overlap_checker.py
python convert/excel_to_string.py
```

### 构建可执行文件 (PyInstaller)
```bash
# 控制台程序
pyinstaller --onefile --console --name "工具名称" script.py

# 纯 GUI 程序（无控制台）
pyinstaller --onefile --noconsole --name "工具名称" script.py

# 具体示例：
pyinstaller --onefile --console --name "ImageJsonSampler" image_json_sampler.py
pyinstaller --onefile --noconsole --name "OrphanImageCleaner" orphan_image_cleaner.py
pyinstaller --onefile --console --name "LabelValidator" label_validator.py
pyinstaller --onefile --console --name "PolygonOverlapChecker" polygon_overlap_checker.py
```

### 安装依赖
```bash
pip install -r requirements.txt
# 或
pip install shapely tqdm pyinstaller pandas
```

### Python 版本
- 目标版本：Python 3.9+（工作流使用 3.10）
- 运行环境：Linux、macOS、Windows

---

## 代码风格指南

### Python 风格
- 遵循 **PEP 8** 风格指南
- 使用 4 空格缩进（不使用 Tab）
- 最大行长：120 字符

### 导入顺序
- 标准库导入在前，第三方库在后，本地模块最后
- 按类型分组导入，组之间用空行分隔
```python
import os
import json
import shutil

import tkinter as tk
from tkinter import filedialog, messagebox
from pathlib import Path

from shapely.geometry import Polygon
from shapely.strtree import STRtree
from tqdm import tqdm
```

### 命名规范
- **函数**：`snake_case`（如 `check_labelme_json`、`count_cropland_labels`）
- **变量**：`snake_case`（如 `all_json_files`、`target_dir`）
- **常量**：`UPPER_SNAKE_CASE`（如 `VALID_CODES`）

### 异常处理
- 文件 I/O 操作使用 try-except 块
- 尽量捕获具体异常类型
- 用户界面中使用 messagebox 显示错误信息
```python
try:
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
except json.JSONDecodeError:
    print(f"警告: 文件 {filename} 格式有误，已跳过")
except Exception as e:
    print(f"无法读取文件 {filename}: {str(e)}")
```

### 文件操作
- 文本文件始终使用 `encoding='utf-8'`
- 使用 `with` 语句处理文件
- 跨平台路径操作优先使用 `pathlib.Path`

### tkinter GUI 模式
- 初始化根窗口但隐藏：`root.withdraw()`
- 保持对话框在最前面：`root.attributes('-topmost', True)`
- 显示对话框后销毁根窗口避免内存泄漏

### 文档要求
- 每个工具文件开头必须有中文注释，说明功能和使用场景
- 函数文档保持简洁

### 进度指示器
- 已知总数时使用 `tqdm` 显示进度条
- 简单进度条使用 `sys.stdout.write()` 配合 `\r`

### 输出文件
- 中文兼容性使用带 BOM 的 CSV（`encoding='utf-8-sig'`）
- 在成功消息中包含结果文件路径

---

## 项目结构
```
/Users/megumikato/CodeProject/tool/
├── image_json_sampler.py      # 图片-JSON 抽样工具
├── label_validator.py         # 标签校验工具
├── orphan_image_cleaner.py    # 孤儿图片清理工具
├── cropland_label_counter.py  # 农田标签计数器
├── polygon_overlap_checker.py # 多边形重叠检测
├── convert/
│   └── excel_to_string.py     # Excel 转字符串转换器
├── requirements.txt           # Python 依赖
└── .github/workflows/         # EXE 构建的 CI/CD
```

---

## 在此代码库中工作

### 添加新工具
1. 创建新的 Python 文件，使用 `snake_case` 命名
2. 文件开头添加中文注释说明功能
3. 在 `.github/workflows/` 添加对应的 CI/CD 工作流
4. 本地测试通过后再提交

### 修改现有工具
- 保持与现有工作流的向后兼容
- 保持错误信息对用户友好
- 使用样本数据测试后再提交
