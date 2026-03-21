"""
孤儿图片清理工具 (Orphan Image Cleaner)

功能说明：
- 扫描选定目录及其子目录中的所有图片文件
- 删除没有对应 JSON 文件的孤儿图片（清理标注缺失的数据）
- 自动清理处理过程中产生的空文件夹
- 生成清理统计报告

使用场景：
- 数据集预处理和清洗
- 删除标注不完整的图片
- 整理文件夹结构
"""

import os
import tkinter as tk
from tkinter import filedialog, messagebox


def clean_data():
    root = tk.Tk()
    root.withdraw()

    target_path = filedialog.askdirectory(title="选择需要清理的文件夹")

    if not target_path:
        print("未选择文件夹，程序退出。")
        return

    image_extensions = ('.jpg', '.jpeg', '.JPG', '.JPEG')
    img_count = 0
    deleted_img_count = 0

    for root_dir, dirs, files in os.walk(target_path):
        file_set = {f.lower() for f in files}

        for file_name in files:
            name, ext = os.path.splitext(file_name)

            if ext.lower() in image_extensions:
                img_count += 1
                json_name = f"{name}.json".lower()

                if json_name not in file_set:
                    file_path = os.path.join(root_dir, file_name)
                    try:
                        os.remove(file_path)
                        deleted_img_count += 1
                    except Exception as e:
                        print(f"无法删除文件 {file_path}: {e}")

    deleted_folder_count = 0
    for root_dir, dirs, files in os.walk(target_path, topdown=False):
        if root_dir == target_path:
            continue

        if not os.listdir(root_dir):
            try:
                os.rmdir(root_dir)
                deleted_folder_count += 1
            except Exception:
                pass

    msg = f"任务完成！\n\n检查图片：{img_count} 张\n删除无标签图片：{deleted_img_count} 张\n清理空文件夹：{deleted_folder_count} 个"
    messagebox.showinfo("清理结果", msg)


if __name__ == "__main__":
    clean_data()
