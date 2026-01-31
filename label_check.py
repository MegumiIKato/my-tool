import json
import os
import csv
import tkinter as tk
from tkinter import filedialog
from tkinter import messagebox

# 7. 字典硬编码
# 根据要求，仅校验“代码”一栏
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
    # 5. 使用弹窗形式选择文件夹
    root = tk.Tk()
    root.withdraw()  # 隐藏主窗口
    
    target_dir = filedialog.askdirectory(title="请选择包含Labelme JSON文件的文件夹")
    
    if not target_dir:
        print("未选择文件夹，程序退出。")
        return

    error_list = []

    # 1. 读取所有文件夹内的json文件（递归嵌套）
    for subdir, dirs, files in os.walk(target_dir):
        for file in files:
            if file.lower().endswith('.json'):
                file_path = os.path.join(subdir, file)
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        
                        # 2. 标签名在“label”内
                        shapes = data.get('shapes', [])
                        invalid_labels_in_file = []
                        
                        for shape in shapes:
                            label = shape.get('label')
                            # 3. 校验标签名是否在字典代码中
                            if label not in VALID_CODES:
                                invalid_labels_in_file.append(label)
                        
                        # 如果有错误，记录到列表中
                        if invalid_labels_in_file:
                            unique_invalids = list(set(invalid_labels_in_file))
                            for err_label in unique_invalids:
                                # 4. 格式：文件路径与文件名、具体错误情况
                                error_list.append([
                                    file_path, 
                                    f"存在非字典项的 {err_label}"
                                ])
                                
                except Exception as e:
                    error_list.append([file_path, f"文件读取失败: {str(e)}"])

    # 4 & 5. 生成csv文件，命名“result.csv”在选择的文件夹内
    result_csv_path = os.path.join(target_dir, "result.csv")
    
    try:
        with open(result_csv_path, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerow(['文件路径', '错误情况'])
            writer.writerows(error_list)
        
        messagebox.showinfo("检查完成", f"结果已保存至：\n{result_csv_path}\n共发现 {len(error_list)} 处错误。")
    except Exception as e:
        messagebox.showerror("保存失败", f"无法生成CSV文件：{str(e)}")

if __name__ == "__main__":
    check_labelme_json()
