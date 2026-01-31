import os
import json
import tkinter as tk
from tkinter import filedialog, messagebox
from collections import Counter

def count_labels_recursive(data, counter):
    """递归统计JSON数据中所有'label'键对应的值"""
    if isinstance(data, dict):
        if 'label' in data:
            label_value = str(data['label'])
            counter[label_value] += 1
        for value in data.values():
            count_labels_recursive(value, counter)
    elif isinstance(data, list):
        for item in data:
            count_labels_recursive(item, counter)

def process_folder(folder_path):
    """遍历文件夹并汇总所有标签计数"""
    total_counter = Counter()
    found_files = False

    for filename in os.listdir(folder_path):
        if filename.lower().endswith('.json'):
            found_files = True
            file_path = os.path.join(folder_path, filename)
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    try:
                        json_data = json.load(file)
                        count_labels_recursive(json_data, total_counter)
                    except json.JSONDecodeError:
                        print(f"警告: 文件 {filename} 格式有误，已跳过")
            except Exception as e:
                print(f"无法读取文件 {filename}: {str(e)}")
    
    return total_counter, found_files

def main():
    # 1. 初始化 tkinter
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)

    print("--- 标签(Labels) 全量统计工具 ---")
    print("请在弹出的窗口中选择包含 JSON 的文件夹...\n")

    folder_selected = filedialog.askdirectory(title="选择包含 JSON 文件的文件夹")
    if not folder_selected:
        print("未选择文件夹，程序运行取消。")
        return

    print(f"正在处理目录: {folder_selected}")
    print("-" * 40)
    
    counts, found_files = process_folder(folder_selected)
    
    print("-" * 40)
    if not found_files:
        print("该文件夹内未找到任何 .json 文件。")
        messagebox.showwarning("结果", "文件夹内未找到 JSON 文件")
    else:
        # 排序并打印结果
        result_text = "标签统计结果:\n"
        if not counts:
            result_text += "未在 JSON 文件中找到 'label' 键。"
        else:
            # 按次数从高到低排序
            for label, count in counts.most_common():
                line = f"{label}: {count}"
                print(line)
                result_text += line + "\n"
        
        print("-" * 40)
        print("统计完成！")
        
        # 弹出结果框
        messagebox.showinfo("统计结果", result_text)

    print("\n" + "="*40)
    input("按回车键(Enter)即可退出程序...")
    root.destroy()

if __name__ == "__main__":
    main()
