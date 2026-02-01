import os
import json
import random
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox
from pathlib import Path

def select_folder():
    root = tk.Tk()
    root.withdraw() 
    # 强制弹窗显示在最前面
    root.attributes('-topmost', True)
    folder_selected = filedialog.askdirectory(title="选择源文件夹")
    root.destroy()
    return folder_selected

def get_image_json_pairs(root_path):
    """递归获取所有图片及其对应的json文件对"""
    valid_extensions = ('.jpg', '.JPG', '.jpeg', '.JPEG')
    folder_map = {} 

    for root, dirs, files in os.walk(root_path):
        # 排除存放结果的文件夹本身，避免循环读取
        if "照片检查+" in root:
            continue
            
        json_files = [f for f in files if f.lower().endswith('.json')]
        pairs = []
        for jf in json_files:
            base_name = os.path.splitext(jf)[0]
            img_name = None
            for ext in valid_extensions:
                if base_name + ext in files:
                    img_name = base_name + ext
                    break
            
            if img_name:
                pairs.append((img_name, jf))
        
        if pairs:
            folder_map[root] = pairs
            
    return folder_map

def dispersed_sample(folder_map, target_count=50):
    """从多个文件夹中尽量均匀分散地抽取"""
    selected_pairs = []
    folders = list(folder_map.keys())
    
    total_available = sum(len(v) for v in folder_map.values())
    if total_available <= target_count:
        for folder in folders:
            for pair in folder_map[folder]:
                selected_pairs.append((folder, pair))
        return selected_pairs

    # 模拟“轮询”抽取，保证分散度
    while len(selected_pairs) < target_count and folders:
        random.shuffle(folders)
        for folder in folders[:]:
            if folder_map[folder]:
                idx = random.randrange(len(folder_map[folder]))
                pair = folder_map[folder].pop(idx)
                selected_pairs.append((folder, pair))
                if len(selected_pairs) == target_count:
                    break
            else:
                folders.remove(folder)
        
    return selected_pairs

def main():
    source_dir = select_folder()
    if not source_dir:
        print("未选择文件夹，程序退出。")
        return

    print(f"正在扫描文件夹: {source_dir}")
    folder_map = get_image_json_pairs(source_dir)
    
    total_found = sum(len(v) for v in folder_map.values())
    print(f"共找到 {total_found} 组有效的图片-JSON对。")

    if total_found == 0:
        root = tk.Tk()
        root.withdraw()
        messagebox.showwarning("警告", "源文件夹内未找到有效的图片和同名JSON对！")
        root.destroy()
        return

    # 准备目标文件夹
    base_folder_name = os.path.basename(os.path.normpath(source_dir))
    output_folder_name = f"照片检查+{base_folder_name}"
    output_dir = os.path.join(source_dir, output_folder_name)
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # 抽取
    sampled_list = dispersed_sample(folder_map, 50)
    
    total_labels = 0
    print(f"\n开始拷贝到: {output_folder_name}")
    
    for i, (root_path, (img_name, json_name)) in enumerate(sampled_list):
        # 拷贝
        shutil.copy2(os.path.join(root_path, img_name), os.path.join(output_dir, img_name))
        json_src = os.path.join(root_path, json_name)
        json_dst = os.path.join(output_dir, json_name)
        shutil.copy2(json_src, json_dst)
        
        # 统计
        try:
            with open(json_dst, 'r', encoding='utf-8') as f:
                data = json.load(f)
                total_labels += len(data.get('shapes', []))
        except:
            pass

        # 进度条
        percent = (i + 1) / len(sampled_list) * 100
        print(f"\r进度: [{i+1}/{len(sampled_list)}] {percent:.1f}%", end="")

    print("\n\n处理完成！")
    
    # 结果弹窗
    root = tk.Tk()
    root.withdraw()
    root.attributes('-topmost', True)
    result_msg = (f"抽查任务完成！\n\n"
                  f"1. 目标文件夹: {output_folder_name}\n"
                  f"2. 已抽取图片: {len(sampled_list)} 张\n"
                  f"3. 标签总数 (Shapes): {total_labels}")
    messagebox.showinfo("统计结果", result_msg)
    root.destroy()

if __name__ == "__main__":
    main()
