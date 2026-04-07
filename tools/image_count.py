import os
import sys
from openpyxl import Workbook
from core.file_scanner import get_leaf_folders, scan_leaf_dir, IMAGE_EXTENSIONS


def select_folder():
    from tkinter import filedialog, Tk
    root = Tk()
    root.withdraw()
    root.attributes('-topmost', True)
    folder_selected = filedialog.askdirectory(title="选择要统计的文件夹")
    root.destroy()
    return folder_selected


def run_count(root_folder: str):
    """执行文件计数统计
    
    参数:
        root_folder: 根目录路径
    
    返回:
        (output_path, error, stats)
    """
    if not root_folder:
        return None, "未选择文件夹"
    
    if not os.path.isdir(root_folder):
        return None, "文件夹路径无效"
    
    leaf_folders = get_leaf_folders(root_folder)
    
    total_folders = 0
    total_images_by_ext = {ext: 0 for ext in IMAGE_EXTENSIONS}
    total_json = 0
    total_matched = 0
    
    wb = Workbook()
    ws = wb.active
    ws.title = "统计结果"
    ws.append(["序号", "文件夹路径", "jpg文件数", "jpeg文件数", "png文件数", "tif文件数", "tiff文件数", "json文件数", "文件配对成功数"])
    
    for idx, fld in enumerate(leaf_folders, 1):
        result = scan_leaf_dir(fld)
        
        total_imgs = sum(result['image_counts'].values())
        if total_imgs > 0 or result['json_count'] > 0:
            ws.append([
                idx, fld,
                result['image_counts']['.jpg'],
                result['image_counts']['.jpeg'],
                result['image_counts']['.png'],
                result['image_counts']['.tif'],
                result['image_counts']['.tiff'],
                result['json_count'],
                result['paired']
            ])
            total_folders += 1
            for ext, cnt in result['image_counts'].items():
                total_images_by_ext[ext] += cnt
            total_json += result['json_count']
            total_matched += result['paired']
    
    output_path = os.path.join(root_folder, "文件计数统计结果.xlsx")
    wb.save(output_path)
    
    stats = {
        "total_folders": total_folders,
        "total_images": total_images_by_ext,
        "total_json": total_json,
        "total_matched": total_matched
    }
    
    return output_path, None, stats


if __name__ == "__main__":
    folder = select_folder()
    if not folder:
        print("未选择文件夹")
        sys.exit(1)
    
    output_path, error, stats = run_count(folder)
    
    if error:
        print(f"错误: {error}")
        sys.exit(1)
    
    print(f"统计完成，结果已保存到: {output_path}")
    print(f"共扫描文件夹数: {stats['total_folders']}")
    print(f"总共照片数: {sum(stats['total_images'].values())}")
    print(f"总共json文件数: {stats['total_json']}")
    print(f"总匹配成功数: {stats['total_matched']}")
