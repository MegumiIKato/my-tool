import json
import shutil
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

    geom_list = [p['geom'] for p in polygons]
    tree = STRtree(geom_list)
    overlap_indices = set()

    for i, poly_info in enumerate(polygons):
        curr_geom = poly_info['geom']
        possible_matches = tree.query(curr_geom, predicate='intersects')
        
        for match_idx in possible_matches:
            if i == match_idx:
                continue
            try:
                intersection_area = curr_geom.intersection(polygons[match_idx]['geom']).area
                if intersection_area > threshold:
                    overlap_indices.add(i)
                    overlap_indices.add(match_idx)
            except:
                continue

    if not overlap_indices:
        return None

    # 有重叠，修改标签名并重排序
    error_shapes = []
    normal_shapes = []
    for i, poly_info in enumerate(polygons):
        s_data = poly_info['orig_data']
        if i in overlap_indices:
            if not s_data['label'].startswith('!!OVERLAP_'):
                s_data['label'] = f"!!OVERLAP_{s_data['label']}"
            error_shapes.append(s_data)
        else:
            normal_shapes.append(s_data)

    data['shapes'] = error_shapes + normal_shapes + other_shapes
    return data

def main():
    root = tk.Tk()
    root.withdraw()

    print("=== Labelme 重叠检查与自动修复工具 ===")
    
    # 1. 选择源文件夹
    src_dir_str = filedialog.askdirectory(title="选择包含标注文件的根文件夹(如 A 文件夹)")
    if not src_dir_str:
        return
    src_dir = Path(src_dir_str)

    # 2. 在选定文件夹内新建 ERROR_CHECK 文件夹
    dst_dir_name = "ERROR_CHECK_RESULTS"
    dst_dir = src_dir / dst_dir_name
    
    # 搜索所有 json 
    # 注意：排除掉已经在结果文件夹中的 json，防止重复处理
    all_json_files = [
        p for p in src_dir.rglob("*.json") 
        if dst_dir_name not in p.parts
    ]

    if not all_json_files:
        print("未找到任何 JSON 文件。")
        input("按回车退出...")
        return

    print(f"找到 {len(all_json_files)} 个 JSON 文件。正在检查...")

    error_count = 0
    for json_path in tqdm(all_json_files):
        modified_data = check_and_fix_overlap(json_path)
        
        if modified_data:
            error_count += 1
            
            # 计算相对路径，保持子文件夹结构 (A/A1/xxx.json -> ERROR_CHECK_RESULTS/A1/xxx.json)
            rel_path = json_path.relative_to(src_dir)
            target_json_path = dst_dir / rel_path
            target_json_path.parent.mkdir(parents=True, exist_ok=True)

            # 保存修改后的 JSON
            with open(target_json_path, 'w', encoding='utf-8') as f:
                json.dump(modified_data, f, indent=2, ensure_ascii=False)
            
            # 查找并复制对应的 tif 文件
            # 尝试常见后缀名
            found_tif = False
            for ext in ['.tif', '.tiff', '.TIF', '.TIFF']:
                tif_path = json_path.with_suffix(ext)
                if tif_path.exists():
                    target_tif_path = target_json_path.with_suffix(ext)
                    shutil.copy2(tif_path, target_tif_path)
                    found_tif = True
                    break
            
            tqdm.write(f"[发现重叠] 源路径: {json_path}")
            if not found_tif:
                tqdm.write(f"  [警告] 未找到对应的 TIF 图片文件")

    print("-" * 50)
    print(f"处理完成！")
    print(f"共检查文件: {len(all_json_files)}")
    print(f"发现问题文件: {error_count}")
    if error_count > 0:
        print(f"请在以下路径查看结果: {dst_dir}")
    
    input("\n按回车键退出...")

if __name__ == "__main__":
    main()