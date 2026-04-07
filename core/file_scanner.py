"""
文件扫描核心模块

提供文件扫描的公共函数，支持统一的图片格式处理
"""

import os
from pathlib import Path
from typing import Generator


IMAGE_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.tif', '.tiff')


def _should_exclude_path(path: Path, exclude_dirs: list[str] | None) -> bool:
    """判断路径是否应被排除。

    支持传入目录名、相对路径或绝对路径。
    """
    if not exclude_dirs:
        return False

    path_parts = set(path.parts)
    resolved_path = path.resolve()

    for exclude in exclude_dirs:
        if not exclude:
            continue

        exclude_path = Path(exclude)
        exclude_name = exclude_path.name
        if exclude_name and exclude_name in path_parts:
            return True

        try:
            resolved_path.relative_to(exclude_path.resolve())
            return True
        except Exception:
            continue

    return False


def is_image_file(filename: str) -> bool:
    """判断是否为图片文件"""
    _, ext = os.path.splitext(filename)
    return ext.lower() in IMAGE_EXTENSIONS


def get_leaf_folders(root_path: str) -> list[str]:
    """获取所有叶子文件夹（无子文件夹的目录）
    
    参数:
        root_path: 根目录路径
    
    返回:
        叶子文件夹路径列表
    """
    leaf_folders = []
    for root, dirs, files in os.walk(root_path):
        if not dirs:
            leaf_folders.append(root)
    return leaf_folders


def scan_leaf_dir(leaf_dir: str) -> dict:
    """扫描单个叶子文件夹内的文件配对情况
    
    参数:
        leaf_dir: 叶子文件夹路径
    
    返回:
        {
            'paired': int,              # 正常配对数（单格式图片+JSON）
            'paired_names': set,        # 配对的文件名集合
            'orphan_image': int,        # 孤立图片数
            'orphan_json': int,         # 孤立JSON数
            'special_pairs': list,      # 特殊配对列表
            'image_counts': dict,        # 各格式图片数量
            'json_count': int           # JSON数量
        }
    """
    image_files = []  # [(name_lower, full_filename), ...]
    json_files = []   # [(name_lower, full_filename), ...]
    
    image_counts = {ext: 0 for ext in IMAGE_EXTENSIONS}
    
    for file_name in os.listdir(leaf_dir):
        name, ext = os.path.splitext(file_name)
        name_lower = name.lower()
        ext_lower = ext.lower()
        
        if is_image_file(file_name):
            image_files.append((name_lower, file_name))
            image_counts[ext_lower] += 1
        elif ext_lower == '.json':
            json_files.append((name_lower, file_name))
    
    image_names = {item[0] for item in image_files}
    json_names = {item[0] for item in json_files}
    
    paired_names = image_names & json_names
    normal_paired_names = set()
    special_pairs = []
    
    for name in paired_names:
        image_filenames = [fname for n, fname in image_files if n == name]
        
        if len(image_filenames) == 1:
            normal_paired_names.add(name)
        else:
            json_filename = [fname for n, fname in json_files if n == name][0]
            special_pairs.append({
                'folder': leaf_dir,
                'name': name,
                'files': image_filenames + [json_filename]
            })
    
    orphan_image_names = image_names - json_names
    orphan_json_names = json_names - image_names
    
    return {
        'paired': len(normal_paired_names),
        'paired_names': normal_paired_names,
        'orphan_image': len(orphan_image_names),
        'orphan_json': len(orphan_json_names),
        'special_pairs': special_pairs,
        'image_counts': image_counts,
        'json_count': len(json_files)
    }


def scan_all_leaf_dirs(root_path: str) -> dict:
    """扫描所有叶子文件夹，返回汇总统计
    
    参数:
        root_path: 根目录路径
    
    返回:
        {
            'paired': int,
            'orphan_image': int,
            'orphan_json': int,
            'special_pairs': list,
            'folder_count': int,
            'image_counts': dict,
            'total_json': int
        }
    """
    leaf_folders = get_leaf_folders(root_path)
    
    total_paired = 0
    total_orphan_image = 0
    total_orphan_json = 0
    all_special_pairs = []
    total_image_counts = {ext: 0 for ext in IMAGE_EXTENSIONS}
    total_json = 0
    
    for leaf_dir in leaf_folders:
        result = scan_leaf_dir(leaf_dir)
        total_paired += result['paired']
        total_orphan_image += result['orphan_image']
        total_orphan_json += result['orphan_json']
        all_special_pairs.extend(result['special_pairs'])
        total_json += result['json_count']
        
        for ext, count in result['image_counts'].items():
            total_image_counts[ext] += count
    
    return {
        'paired': total_paired,
        'orphan_image': total_orphan_image,
        'orphan_json': total_orphan_json,
        'special_pairs': all_special_pairs,
        'folder_count': len(leaf_folders),
        'image_counts': total_image_counts,
        'total_json': total_json
    }


def find_orphans_in_leaf(leaf_dir: str) -> dict:
    """查找叶子文件夹中的孤立文件和特殊配对
    
    参数:
        leaf_dir: 叶子文件夹路径
    
    返回:
        {
            'orphan_image_paths': list,  # 孤立图片完整路径
            'orphan_json_paths': list,    # 孤立JSON完整路径
            'special_pairs': list,       # 特殊配对列表
            'orphan_image_names': set,    # 孤立图片文件名（不含扩展名）
            'orphan_json_names': set      # 孤立JSON文件名（不含扩展名）
        }
    """
    image_files = []
    json_files = []
    
    for file_name in os.listdir(leaf_dir):
        name, ext = os.path.splitext(file_name)
        name_lower = name.lower()
        full_path = os.path.join(leaf_dir, file_name)
        
        if is_image_file(file_name):
            image_files.append((name_lower, file_name, full_path))
        elif ext.lower() == '.json':
            json_files.append((name_lower, file_name, full_path))
    
    image_names = {item[0] for item in image_files}
    json_names = {item[0] for item in json_files}
    
    paired_names = image_names & json_names
    special_pairs = []
    
    for name in paired_names:
        image_filenames = [f for n, f, p in image_files if n == name]
        if len(image_filenames) > 1:
            json_filename = [f for n, f, p in json_files if n == name][0]
            special_pairs.append({
                'folder': leaf_dir,
                'name': name,
                'files': image_filenames + [json_filename]
            })
    
    orphan_image_names = image_names - json_names
    orphan_json_names = json_names - image_names
    
    orphan_image_paths = [p for n, f, p in image_files if n in orphan_image_names]
    orphan_json_paths = [p for n, f, p in json_files if n in orphan_json_names]
    
    return {
        'orphan_image_paths': orphan_image_paths,
        'orphan_json_paths': orphan_json_paths,
        'special_pairs': special_pairs,
        'orphan_image_names': orphan_image_names,
        'orphan_json_names': orphan_json_names
    }


def find_all_orphans(root_path: str) -> dict:
    """扫描所有叶子文件夹中的孤立文件
    
    参数:
        root_path: 根目录路径
    
    返回:
        {
            'paired': int,
            'orphan_image': int,
            'orphan_json': int,
            'special_pairs': list,
            'orphan_image_paths': list,
            'orphan_json_paths': list,
            'folder_count': int,
            'image_counts': dict,
            'total_json': int
        }
    """
    scan_result = scan_all_leaf_dirs(root_path)
    
    all_orphan_image_paths = []
    all_orphan_json_paths = []
    
    for leaf_dir in get_leaf_folders(root_path):
        orphan_result = find_orphans_in_leaf(leaf_dir)
        all_orphan_image_paths.extend(orphan_result['orphan_image_paths'])
        all_orphan_json_paths.extend(orphan_result['orphan_json_paths'])
    
    return {
        'paired': scan_result['paired'],
        'orphan_image': scan_result['orphan_image'],
        'orphan_json': scan_result['orphan_json'],
        'special_pairs': scan_result['special_pairs'],
        'orphan_image_paths': all_orphan_image_paths,
        'orphan_json_paths': all_orphan_json_paths,
        'folder_count': scan_result['folder_count'],
        'image_counts': scan_result['image_counts'],
        'total_json': scan_result['total_json']
    }


def scan_json_files(root_path: str, exclude_dirs: list[str] = None) -> Generator[Path, None, None]:
    """递归扫描目录下所有 JSON 文件
    
    参数:
        root_path: 根目录路径
        exclude_dirs: 要排除的目录名列表
    
    返回:
        JSON 文件路径生成器
    """
    if exclude_dirs is None:
        exclude_dirs = []
    
    root = Path(root_path)
    for json_file in root.rglob("*.json"):
        if _should_exclude_path(json_file, exclude_dirs):
            continue
        yield json_file


def scan_image_json_pairs(root_path: str, exclude_dirs: list[str] = None) -> dict[str, list[tuple[str, str]]]:
    """扫描图片和 JSON 文件配对，按文件夹分组
    
    参数:
        root_path: 根目录路径
        exclude_dirs: 要排除的目录名列表
    
    返回:
        dict: {folder_path: [(img_file, json_file), ...]}
    """
    if exclude_dirs is None:
        exclude_dirs = []

    folder_map = {}
    
    for root, dirs, files in os.walk(root_path):
        root_path_current = Path(root)
        dirs[:] = [d for d in dirs if not _should_exclude_path(root_path_current / d, exclude_dirs)]

        if _should_exclude_path(root_path_current, exclude_dirs):
            continue
            
        json_files = [f for f in files if f.lower().endswith('.json')]
        pairs = []
        file_lookup = {Path(file_name).stem.lower(): file_name for file_name in files if is_image_file(file_name)}
        
        for jf in json_files:
            base_name = os.path.splitext(jf)[0]
            img_name = file_lookup.get(base_name.lower())
            
            if img_name:
                pairs.append((img_name, jf))
        
        if pairs:
            folder_map[root] = pairs
    
    return folder_map


def find_orphan_files(folder_path: str) -> tuple[set, set, int]:
    """查找孤立的 JPG 和 JSON 文件（兼容旧接口）
    
    参数:
        folder_path: 文件夹路径
    
    返回:
        (jpg_names, json_names, folder_count)
        - jpg_names: jpg/jpeg 文件名集合
        - json_names: json 文件名集合
        - folder_count: 文件夹数量
    """
    jpg_names = set()
    json_names = set()
    folder_count = 0
    
    for root_dir, dirs, files in os.walk(folder_path):
        folder_count += 1
        for file_name in files:
            _, ext = os.path.splitext(file_name)
            ext_lower = ext.lower()
            
            if ext_lower not in ('.jpg', '.jpeg', '.json'):
                continue
            
            name = os.path.splitext(file_name)[0].lower()
            
            if ext_lower in ('.jpg', '.jpeg'):
                jpg_names.add(name)
            elif ext_lower == '.json':
                json_names.add(name)
    
    return jpg_names, json_names, folder_count
