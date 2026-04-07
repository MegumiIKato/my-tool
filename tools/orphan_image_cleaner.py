"""
孤立文件清理工具 (Orphan Image Cleaner)

功能说明：
- 扫描选定目录及其子目录中的所有文件
- 支持两种清理模式：删除孤立图片或删除孤立JSON
- 自动清理处理过程中产生的空文件夹
- 检测并报告特殊配对（同名多格式图片+JSON）

使用场景：
- 数据集预处理和清洗
- 删除标注不完整的图片或缺失图片的标注
- 整理文件夹结构
"""

import os
from pathlib import Path

from core.file_scanner import (
    IMAGE_EXTENSIONS,
    find_all_orphans, scan_all_leaf_dirs
)


def _cleanup_affected_empty_dirs(target_dir: str, files_to_delete: list[str]) -> None:
    """只清理本次删除影响到的空目录链。"""
    target_path = Path(target_dir).resolve()
    candidate_dirs = {Path(file_path).resolve().parent for file_path in files_to_delete}

    for directory in sorted(candidate_dirs, key=lambda item: len(item.parts), reverse=True):
        current_dir = directory
        while current_dir != target_path:
            try:
                current_dir.relative_to(target_path)
            except ValueError:
                break

            try:
                current_dir.rmdir()
            except OSError:
                break

            current_dir = current_dir.parent


def run_scan(target_dir: str) -> tuple[dict | None, str | None]:
    """执行扫描逻辑
    
    参数:
        target_dir: 目标目录路径
    
    返回:
        (stats, None) - 成功
        (None, error) - 失败
    """
    if not os.path.isdir(target_dir):
        return None, "目标文件夹不存在或不是有效目录"
    
    stats = scan_all_leaf_dirs(target_dir)
    return stats, None


def run_clean(target_dir: str, mode: str) -> tuple[dict | None, str | None]:
    """执行清理逻辑
    
    参数:
        target_dir: 目标目录路径
        mode: 'image' 删除孤立图片, 'json' 删除孤立JSON
    
    返回:
        (stats, None) - 成功
        (None, error) - 失败
    """
    if not os.path.isdir(target_dir):
        return None, "目标文件夹不存在或不是有效目录"
    
    if mode not in ('image', 'json'):
        return None, "无效的清理模式"
    
    orphan_result = find_all_orphans(target_dir)
    
    if mode == 'image':
        files_to_delete = orphan_result['orphan_image_paths']
    else:
        files_to_delete = orphan_result['orphan_json_paths']
    
    deleted_count = 0
    failed_files = []
    for file_path in files_to_delete:
        try:
            os.remove(file_path)
            deleted_count += 1
        except Exception as exc:
            failed_files.append({
                'path': file_path,
                'reason': str(exc),
            })

    _cleanup_affected_empty_dirs(target_dir, files_to_delete)
    
    stats = scan_all_leaf_dirs(target_dir)
    stats['deleted'] = deleted_count
    stats['failed'] = failed_files
    
    return stats, None


if __name__ == "__main__":
    import tkinter as tk
    from tkinter import filedialog, messagebox
    
    root = tk.Tk()
    root.withdraw()
    
    target_dir = filedialog.askdirectory(title="选择需要清理的文件夹")
    if not target_dir:
        print("未选择文件夹")
        exit()
    
    print(f"支持的图片格式: {', '.join(IMAGE_EXTENSIONS)}")
    
    stats, error = run_scan(target_dir)
    if error:
        messagebox.showerror("错误", error)
        exit()
    
    msg = f"有效配对: {stats['paired']} 对\n"
    msg += f"孤立图片: {stats['orphan_image']} 个\n"
    msg += f"孤立JSON: {stats['orphan_json']} 个\n"
    msg += f"特殊配对: {len(stats['special_pairs'])} 组\n"
    msg += f"扫描文件夹: {stats['folder_count']} 个"
    
    if stats['special_pairs']:
        msg += "\n\n--- 特殊配对详情 ---"
        for i, sp in enumerate(stats['special_pairs'][:5], 1):
            msg += f"\n[{i}] {sp['folder']}"
            msg += f"\n    包含文件: {', '.join(sp['files'])}"
        if len(stats['special_pairs']) > 5:
            msg += f"\n... 还有 {len(stats['special_pairs']) - 5} 组"
    
    messagebox.showinfo("扫描结果", msg)
