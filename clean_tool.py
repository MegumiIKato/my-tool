import os
import tkinter as tk
from tkinter import filedialog, messagebox

def clean_data():
    # 初始化tkinter，并隐藏主窗口
    root = tk.Tk()
    root.withdraw()

    # 1. 弹出文件夹选择框
    target_path = filedialog.askdirectory(title="选择需要清理的文件夹")
    
    if not target_path:
        print("未选择文件夹，程序退出。")
        return

    image_extensions = ('.jpg', '.jpeg', '.JPG', '.JPEG')
    img_count = 0
    deleted_img_count = 0

    # 2. 第一阶段：删除没有json的jpg
    for root_dir, dirs, files in os.walk(target_path):
        # 建立当前文件夹下所有文件名的集合（转为小写），提高查找效率
        file_set = {f.lower() for f in files}
        
        for file_name in files:
            name, ext = os.path.splitext(file_name)
            
            # 检查是否是图片
            if ext.lower() in image_extensions:
                img_count += 1
                json_name = f"{name}.json".lower()
                
                # 如果对应的 json 不在集合中
                if json_name not in file_set:
                    file_path = os.path.join(root_dir, file_name)
                    try:
                        os.remove(file_path)
                        deleted_img_count += 1
                    except Exception as e:
                        print(f"无法删除文件 {file_path}: {e}")

    # 3. 第二阶段：清理空文件夹（自底向上）
    deleted_folder_count = 0
    for root_dir, dirs, files in os.walk(target_path, topdown=False):
        # 如果是根目录则跳过，不删除用户选择的本目录
        if root_dir == target_path:
            continue
            
        # 尝试删除文件夹，os.rmdir 只有文件夹为空时才会成功
        if not os.listdir(root_dir):
            try:
                os.rmdir(root_dir)
                deleted_folder_count += 1
            except Exception:
                pass # 忽略含有系统隐藏文件(如Thumbs.db)导致删除失败的情况

    # 4. 弹出完成提示
    msg = f"任务完成！\n\n检查图片：{img_count} 张\n删除无标签图片：{deleted_img_count} 张\n清理空文件夹：{deleted_folder_count} 个"
    messagebox.showinfo("清理结果", msg)

if __name__ == "__main__":
    clean_data()
