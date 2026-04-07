"""
标签校验工具 (Label Validator)

功能说明：
- 递归扫描选定目录中的所有 Labelme JSON 文件
- 检查每个 JSON 文件中的 shapes.label 值是否在用户提供的有效标签字典中
- 生成 xlsx 格式的检查报告，列出所有无效标签及其所在文件

使用场景：
- 标注数据质量检查
- 批量验证标签合法性
- 发现并修复错误的标签名称
"""

import os
import json
import csv
from pathlib import Path
from openpyxl import Workbook


def load_label_dict(file_path: str) -> tuple[set[str] | None, str | None]:
    """加载标签字典文件
    
    支持格式: csv, txt, xlsx, xls
    第一列列名必须为 'label'
    
    参数:
        file_path: 字典文件路径
    
    返回:
        (标签集合, 错误信息) - 成功时 error 为 None
    """
    ext = os.path.splitext(file_path)[1].lower()
    
    labels = set()
    
    try:
        if ext == '.csv':
            labels = _load_csv(file_path)
        elif ext == '.txt':
            labels = _load_txt(file_path)
        elif ext in ('.xlsx', '.xls'):
            labels = _load_excel(file_path)
        else:
            return None, f"不支持的文件格式: {ext}，仅支持 csv/txt/xlsx/xls"
    except Exception as e:
        return None, f"文件读取失败: {str(e)}"
    
    if not labels:
        return None, "字典文件中未找到有效的标签值"
    
    return labels, None


def _load_csv(file_path: str) -> set[str]:
    """加载 CSV 文件"""
    labels = set()
    with open(file_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.reader(f)
        header = next(reader, None)
        if header is None or header[0].strip().lower() != 'label':
            raise ValueError("CSV 文件第一列列名必须为 'label'")
        for row in reader:
            if row and row[0].strip():
                labels.add(row[0].strip())
    return labels


def _load_txt(file_path: str) -> set[str]:
    """加载 TXT 文件，每行一个标签"""
    labels = set()
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                labels.add(line)
    return labels


def _load_excel(file_path: str) -> set[str]:
    """加载 Excel 文件"""
    try:
        import openpyxl
    except ImportError:
        raise ImportError("需要安装 openpyxl 库来读取 Excel 文件")
    
    labels = set()
    wb = openpyxl.load_workbook(file_path, data_only=True)
    ws = wb.active
    
    header = None
    for row in ws.iter_rows(values_only=True):
        if header is None:
            header = row[0]
            if str(header).strip().lower() != 'label':
                raise ValueError("Excel 文件第一列列名必须为 'label'")
            continue
        if row[0] is not None and str(row[0]).strip():
            labels.add(str(row[0]).strip())
    
    wb.close()
    return labels


def run_validator(target_dir: str, dict_path: str) -> tuple[str | None, str | None, dict]:
    """执行标签校验逻辑
    
    参数:
        target_dir: 要检查的文件夹路径
        dict_path: 标签字典文件路径
    
    返回:
        (output_path, error, stats)
        - output_path: 报告文件路径，成功时返回
        - error: 错误信息，无错误返回 None
        - stats: {'total_files': int, 'error_count': int, 'valid_count': int}
    """
    if not os.path.isdir(target_dir):
        return None, "目标文件夹不存在或不是有效目录", {}
    
    valid_labels, load_error = load_label_dict(dict_path)
    if load_error:
        return None, load_error, {}
    
    all_json_files = []
    for root, dirs, files in os.walk(target_dir):
        for file in files:
            if file.lower().endswith('.json'):
                all_json_files.append(os.path.join(root, file))
    
    total_files = len(all_json_files)
    if total_files == 0:
        return None, "目标文件夹内未找到 JSON 文件", {}
    
    error_list = []
    
    for file_path in all_json_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                shapes = data.get('shapes', [])
                
                file_errors = set()
                for shape in shapes:
                    label = str(shape.get('label', "")).strip()
                    if label and label not in valid_labels:
                        file_errors.add(label)
                
                for err_lab in file_errors:
                    rel_path = os.path.relpath(file_path, target_dir)
                    error_list.append([rel_path, err_lab, "不在字典中"])
                    
        except Exception as e:
            rel_path = os.path.relpath(file_path, target_dir)
            error_list.append([rel_path, "", f"文件读取失败: {str(e)}"])
    
    wb = Workbook()
    ws = wb.active
    ws.title = "检查报告"
    ws.append(["序号", "文件路径", "无效标签", "错误类型"])
    
    for idx, (file_path, label, error_type) in enumerate(error_list, 1):
        ws.append([idx, file_path, label, error_type])
    
    if not error_list:
        ws.append([1, "-", "-", "未发现错误"])
    
    output_path = os.path.join(target_dir, "label_check_report.xlsx")
    wb.save(output_path)
    
    stats = {
        'total_files': total_files,
        'error_count': len(error_list),
        'valid_count': total_files - len(error_list) if error_list else total_files
    }
    
    return output_path, None, stats


def export_template(output_dir: str, file_type: str = 'csv') -> str:
    """导出空白模板文件
    
    参数:
        output_dir: 输出目录
        file_type: 模板类型 ('csv' 或 'xlsx')
    
    返回:
        模板文件路径
    """
    if file_type == 'csv':
        template_path = os.path.join(output_dir, "label_template.csv")
        with open(template_path, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerow(['label'])
    else:
        from openpyxl import Workbook
        wb = Workbook()
        ws = wb.active
        ws.title = "标签字典"
        ws.append(['label'])
        template_path = os.path.join(output_dir, "label_template.xlsx")
        wb.save(template_path)
    
    return template_path


if __name__ == "__main__":
    import tkinter as tk
    from tkinter import filedialog, messagebox
    
    root = tk.Tk()
    root.withdraw()
    
    target_dir = filedialog.askdirectory(title="选择 Labelme JSON 所在文件夹")
    if not target_dir:
        print("未选择文件夹")
        exit()
    
    dict_file = filedialog.askopenfilename(
        title="选择标签字典文件",
        filetypes=[("字典文件", "*.csv *.txt *.xlsx *.xls")]
    )
    if not dict_file:
        print("未选择字典文件")
        exit()
    
    output_path, error, stats = run_validator(target_dir, dict_file)
    
    if error:
        messagebox.showerror("错误", error)
    else:
        messagebox.showinfo(
            "完成",
            f"检查完成！\n\n总文件数: {stats['total_files']}\n有效文件: {stats['valid_count']}\n存在问题: {stats['error_count']}\n\n报告已保存至: {output_path}"
        )
