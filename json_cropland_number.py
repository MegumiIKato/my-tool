import os
import json
import tkinter as tk
from tkinter import filedialog, messagebox

def count_cropland_labels(data):
    """递归统计JSON数据中label为'cropland'的出现次数"""
    count = 0
    if isinstance(data, dict):
        if 'label' in data and data['label'] == 'cropland':
            count += 1
        for value in data.values():
            count += count_cropland_labels(value)
    elif isinstance(data, list):
        for item in data:
            count += count_cropland_labels(item)
    return count

def count_cropland_in_folder(folder_path):
    """统计文件夹中所有JSON文件里label为'cropland'的总次数"""
    total_count = 0
    found_files = False

    for filename in os.listdir(folder_path):
        if filename.lower().endswith('.json'):
            found_files = True
            file_path = os.path.join(folder_path, filename)
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    try:
                        json_data = json.load(file)
                        file_count = count_cropland_labels(json_data)
                        total_count += file_count
                        print(f"文件 {filename} -> 出现 {file_count} 次")
                    except json.JSONDecodeError:
                        print(f"警告: 文件 {filename} 格式有误，已跳过")
            except Exception as e:
                print(f"无法读取文件 {filename}: {str(e)}")
    
    if not found_files:
        print("该文件夹内未找到任何 .json 文件")
    
    return total_count

def main():
    # 1. 初始化 tkinter，但不显示主窗口
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)  # 让弹窗保持在最前面

    print("--- 农田(cropland) 标签统计工具 ---")
    print("请在弹出的窗口中选择 JSON 文件夹...\n")

    # 2. 弹出文件夹选择框
    folder_selected = filedialog.askdirectory(title="选择包含 JSON 文件的文件夹")

    if not folder_selected:
        print("未选择文件夹，程序运行取消。")
    else:
        print(f"正在处理目录: {folder_selected}")
        print("-" * 40)
        
        total = count_cropland_in_folder(folder_selected)
        
        print("-" * 40)
        print(f"统计完成！")
        print(f"总计 'label: cropland' 出现总次数: {total}")
        
        # 弹出一个简单的结果提示框
        messagebox.showinfo("统计结果", f"处理完成！\n\n总计出现次数: {total}")

    # 3. 关键：防止执行完后窗口立即关闭
    print("\n" + "="*40)
    input("按回车键(Enter)即可退出程序...")
    root.destroy()

if __name__ == "__main__":
    main()
