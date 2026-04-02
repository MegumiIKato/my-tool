"""
标签校验工具 (Label Validator)

功能说明：
- 递归扫描选定目录中的所有 Labelme JSON 文件
- 检查每个 JSON 文件中的 shapes.label 值是否在预定义的有效标签字典中
- 生成 CSV 格式的检查报告，列出所有无效标签及其所在文件
- 支持的有效标签包括：地物分类码（如 0101、0201 等）、特殊码（如 TTQ、GFBQ 等）

使用场景：
- 标注数据质量检查
- 批量验证标签合法性
- 发现并修复错误的标签名称
"""

import json
import os
import csv
import sys
import tkinter as tk
from tkinter import filedialog, messagebox

VALID_CODES = {
    "0101", "0103", "0201", "0202", "0204", "0301", "0302", "0305", "0307", "0404",
    "05H1", "0601", "0701", "0702", "08H2", "1001", "1003", "1005", "1006", "1008",
    "1101", "1102", "1104", "1104A", "1105", "1106", "1107", "1109", "1202",
    "1207", "TTQ", "GFBQ", "MXJZ", "DP", "MD", "LJTM", "JYZ", "JX", "1007", "09", "0303"
}


def check_labelme_json():
    root = tk.Tk()
    root.withdraw()

    target_dir = filedialog.askdirectory(title="选择Labelme JSON所在文件夹")

    if not target_dir:
        print("未选择任何文件夹，程序退出。")
        return

    print(f"[{'='*50}]")
    print(f"目标目录: {target_dir}")
    print("正在扫描文件...")

    all_json_files = []
    for subdir, dirs, files in os.walk(target_dir):
        for file in files:
            if file.lower().endswith('.json'):
                all_json_files.append(os.path.join(subdir, file))

    total_files = len(all_json_files)
    if total_files == 0:
        print("错误：未找到JSON文件！")
        messagebox.showwarning("提示", "所选文件夹内没有找到JSON文件。")
        return

    print(f"共找到 {total_files} 个文件，准备开始检查...")

    error_list = []

    for index, file_path in enumerate(all_json_files, start=1):
        rel_path = os.path.relpath(file_path, target_dir)
        percent = (index / total_files) * 100
        sys.stdout.write(f"\r进度: [{index}/{total_files}] {percent:.1f}% 正在检查: {rel_path[:40]}...")
        sys.stdout.flush()

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                shapes = data.get('shapes', [])

                file_errors = set()
                for shape in shapes:
                    label = str(shape.get('label', "")).strip()
                    if label not in VALID_CODES:
                        file_errors.add(label)

                for err_lab in file_errors:
                    error_list.append([file_path, f"存在非字典项的 {err_lab}"])

        except Exception as e:
            error_list.append([file_path, f"文件读取/解析失败: {str(e)}"])

    print("\n\n检查完成！正在生成报告...")

    result_csv_path = os.path.join(target_dir, "result.csv")
    try:
        with open(result_csv_path, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerow(['文件路径与文件名', '具体错误情况'])
            if error_list:
                writer.writerows(error_list)
            else:
                writer.writerow(['-', '未发现错误。'])

        print(f"报告已生成: {result_csv_path}")
        print(f"本次检查发现错误总数: {len(error_list)}")
        print(f"[{'='*50}]")

        messagebox.showinfo("任务完成", f"统计结束！\n发现错误：{len(error_list)} 处\n结果已保存至：result.csv")

    except Exception as e:
        print(f"导出CSV失败: {e}")
        messagebox.showerror("错误", "无法写入result.csv文件，请检查文件是否被占用。")


if __name__ == "__main__":
    check_labelme_json()
