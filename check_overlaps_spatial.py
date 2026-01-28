import json
import os
import sys
import tkinter as tk
from tkinter import filedialog
from pathlib import Path
from shapely.geometry import Polygon
from shapely.strtree import STRtree
from tqdm import tqdm

def check_and_fix_overlap(json_path, threshold=0.1):
    """
    检查重叠并返回修改后的数据。如果没有重叠，返回 None。
    """
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"\n[读取跳过] 无法读取 {json_path}: {e}")
        return None

    shapes = data.get('shapes', [])
    if not shapes:
        return None

    polygons = []
    other_shapes = []
    for i, s in enumerate(shapes):
        if s.get('shape_type') == 'polygon' and len(s.get('points', [])) >= 3:
            poly = Polygon(s['points'])
            if not poly.is_valid:
                poly = poly.buffer(0)
            polygons.append({'orig_data': s, 'geom': poly})
        else:
            other_shapes.append(s)

    if not polygons:
        return None

    # 空间索引
    geom_list = [p['geom'] for p in polygons]
    tree = STRtree(geom_list)
    overlap_indices = set()

    for i, poly_info in enumerate(polygons):
        curr_geom = poly_info['geom']
        # 查找可能的相交对象索引 (predicate='intersects' 是 Shapely 2.0+ 的高效写法)
        possible_matches = tree.query(curr_geom, predicate='intersects')
        
        for match_idx in possible_matches:
            if i == match_idx:
                continue
            
            other_geom = polygons[match_idx]['geom']
            try:
                # 准确计算面积
                inter_area = curr_geom.intersection(other_geom).area
                if inter_area > threshold:
                    overlap_indices.add(i)
                    overlap_indices.add(match_idx)
            except:
                continue

    if not overlap_indices:
        return None

    # 存在重叠，开始处理标签名和排序
    error_shapes = []
    normal_shapes = []

    for i, poly_info in enumerate(polygons):
        s_data = poly_info['orig_data']
        if i in overlap_indices:
            # 策略：加前缀并置顶
            if not s_data['label'].startswith('!!OVERLAP_'):
                s_data['label'] = f"!!OVERLAP_{s_data['label']}"
            error_shapes.append(s_data)
        else:
            normal_shapes.append(s_data)

    # 组合新形状列表：错误在前，正常在后，非多边形最后
    data['shapes'] = error_shapes + normal_shapes + other_shapes
    return data

def main():
    # 隐藏 Tkinter 主窗口
    root = tk.Tk()
    root.withdraw()

    print("=== Labelme 耕地数据重叠检查工具 ===")
    
    # 1. 弹出文件夹选择框
    src_dir = filedialog.askdirectory(title="选择包含 Labelme JSON 的源文件夹 (支持多级子目录)")
    if not src_dir:
        print("未选择文件夹，程序退出。")
        return

    # 2. 设置输出路径
    dst_dir = Path(src_dir).parent / (Path(src_dir).name + "_ERROR")
    
    json_files = list(Path(src_dir).rglob("*.json"))
    if not json_files:
        print("文件夹内未找到 JSON 文件。")
        input("按回车键退出...")
        return

    print(f"找到 {len(json_files)} 个 JSON 文件。")
    print(f"检查出的有误文件将保存至: {dst_dir}")
    print("-" * 50)

    error_count = 0
    for json_path in tqdm(json_files, desc="处理进度"):
        modified_data = check_and_fix_overlap(json_path)
        
        if modified_data:
            error_count += 1
            # 保持相对路径结构
            rel_path = json_path.relative_to(src_dir)
            out_path = dst_dir / rel_path
            out_path.parent.mkdir(parents=True, exist_ok=True)

            with open(out_path, 'w', encoding='utf-8') as f:
                json.dump(modified_data, f, indent=2, ensure_ascii=False)
            
            # 打印错误来源路径
            tqdm.write(f"[发现重叠] 源文件: {json_path}")

    print("-" * 50)
    print(f"检查结束！")
    print(f"总计检查: {len(json_files)} 个文件")
    print(f"发现问题: {error_count} 个文件 (已输出至检查文件夹)")
    
    if error_count == 0:
        print("未发现重叠问题。")
    
    input("\n处理完成，按回车键退出...")

if __name__ == "__main__":
    main()
