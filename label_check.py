import json
import os
import csv
import sys
import tkinter as tk
from tkinter import filedialog, messagebox

# 7. 字典硬编码
VALID_CODES = {
    "0101", "0102", "0103", "0201", "0202", "0203", "0204", "0301", "0302", "0305", "0307",
    "0401", "0403", "0404", "0303", "0304", "0306", "0402", "0603", "1105", "1106", "1108",
    "05H1", "0508", "0601", "0602", "0701", "0702", "08H1", "08H2", "08H2A", "0809", "0810",
    "0810A", "09", "1001", "1002", "1003", "1004", "1005", "1006", "1007", "1008", "1009",
    "1101", "1102", "1103", "1104", "1104A", "1107", "1107A", "1109", "1110", "1201", "1202",
    "1203", "1204", "1205", "1206", "1207", "1208", "TTQ", "GFBQ", "MXJZ", "DP", "MD",
    "LJTM", "JYZ", "JX"
}

def check_labelme_json():
    root = tk.Tk()
    root.withdraw()
    
    # 5. 弹窗选择文件夹
    target_dir = filedialog.askdirectory(title="请选择包含Labelme JSON文件的文件夹")
    
    if not target_dir:
        print("未选择文件夹，程序退出。")
        return

    print(f"已选择目录: {target_dir}")
    print("正在扫描文件，请稍候...")

    # 先统计总文件数，用于显示进度
    all_json_files = []
    for subdir, dirs, files in os.walk(target_dir):
        for file in files:
            if file.lower().endswith('.json'):
                all_json_files.append(os.path.join(subdir, file))

    total_files = len(all_json_files)
    if total_files == 0:
        print("在该目录下未找到任何 JSON 文件。")
        messagebox.showwarning("统计结束", "未发现任何 JSON 文件。")
        return

    print(f"共找到 {total_files} 个 JSON 文件，开始检查...")

    error_list = []
    
    # 开始遍历并显示进度
    for index, file_path in enumerate(all_json_files, start=1):
        filename = os.path.basename(file_path)
        # 在控制台刷新当前进度
        sys.stdout.write(f"\r进度: [{index}/{total_files}] 正在检查: {filename[:30]}...")
        sys.stdout.flush()
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                shapes = data.get('shapes', [])
                
                for shape in shapes:
                    label = shape.get('label')
                    if label not in VALID_CODES:
                        error_list.append([file_path, f"存在非字典项的 {label}"])
        except Exception as e:
            error_list.append([file_path, f"文件读取失败: {str(e)}"])

    print("\n\n检查完毕，正在生成 CSV 报告...")

    # 4 & 5. 生成结果文件
    result_csv_path = os.path.join(target_dir, "result.csv")
    try:
        with open(result_csv_path, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerow(['文件路径', '错误情况'])
            writer.writerows(error_list)
        
        print(f"最终结果已保存至: {result_csv_path}")
        messagebox.showinfo("检查完成", f"结果已保存至：\n{result_csv_path}\n共发现 {len(error_list)} 处标签错误。")
    except Exception as e:
        print(f"生成的 CSV 文件失败: {str(e)}")
        messagebox.showerror("错误", f"无法生成 CSV 文件：{str(e)}")

if __name__ == "__main__":
    check_labelme_json()
