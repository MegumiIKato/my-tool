import os
import json
import random
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox
from pathlib import Path

def select_folder():
    root = tk.Tk()
    root.withdraw()  # 隐藏主窗口
    folder_selected = filedialog.askdirectory(title="选择源文件夹")
    root.destroy()
    return folder_selected

def get_image_json_pairs(root_path):
    """递归获取所有图片及其对应的json文件对"""
    valid_extensions = ('.jpg', '.JPG', '.jpeg', '.JPEG')
    folder_map = {} # 用于分散抽取：{文件夹路径: [文件名列表]}

    for root, dirs, files in os.walk(root_path):
        json_files = [f for f in files if f.lower().endswith('.json')]
        pairs = []
        for jf in json_files:
            base_name = os.path.splitext(jf)[0]
            # 检查是否存在对应图片
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
    
    # 如果总数不足
    total_available = sum(len(v) for v in folder_map.values())
    if total_available <= target_count:
        for folder in folders:
            for pair in folder_map[folder]:
                selected_pairs.append((folder, pair))
        return selected_pairs

    # 循环从每个文件夹抽一个，直到满50个
    while len(selected_pairs) < target_count:
        random.shuffle(folders)
        for folder in folders:
            if folder_map[folder]:
                idx = random.randrange(len(folder_map[folder]))
                pair = folder_map[folder].pop(idx)
                selected_pairs.append((folder, pair))
                if len(selected_pairs) == target_count:
                    break
        # 移除已抽空的文件夹
        folders = [f for f in folders if folder_map[f]]
        
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
        messagebox.showwarning("警告", "源文件夹内未找到有效的图片和同名JSON对！")
        return

    # 准备目标文件夹
    folder_name = "照片检查+" + os.path.basename(source_dir)
    output_dir = os.path.join(source_dir, folder_name)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # 抽取
    sampled_list = dispersed_sample(folder_map, 50)
    
    total_labels = 0
    print("\n开始拷贝和统计进度:")
    
    for i, (root, (img_name, json_name)) in enumerate(sampled_list):
        # 拷贝图片
        shutil.copy2(os.path.join(root, img_name), os.path.join(output_dir, img_name))
        # 拷贝并统计JSON
        json_src_path = os.path.join(root, json_name)
        json_dst_path = os.path.join(output_dir, json_name)
        shutil.copy2(json_src_path, json_dst_path)
        
        try:
            with open(json_dst_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                total_labels += len(data.get('shapes', []))
        except Exception as e:
            print(f"读取文件 {json_name} 出错: {e}")

        # 控制台进度显示
        percent = (i + 1) / len(sampled_list) * 100
        print(f"\r进度: [{i+1}/{len(sampled_list)}] {percent:.1f}%", end="")

    print("\n\n处理完成！")
    result_msg = f"抽查任务完成！\n\n1. 已抽取: {len(sampled_list)} 张照片\n2. 存储位置: {folder_name}\n3. 标签总数: {total_labels}"
    
    root = tk.Tk()
    root.withdraw()
    messagebox.showinfo("统计结果", result_msg)
    root.destroy()

if __name__ == "__main__":
    main()
