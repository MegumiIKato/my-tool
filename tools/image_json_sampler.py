"""
图片-JSON 抽样工具 (Image JSON Sampler)

功能说明：
- 从选定的文件夹中递归查找所有图片及其对应的 Labelme JSON 文件
- 使用轮询算法从多个子文件夹中均匀分散抽取指定数量的样本
- 将抽样的图片和 JSON 文件复制到指定输出目录
- 统计并报告抽样结果中的标签（shapes）总数

使用场景：
- 标注质量抽查
- 数据集抽样检验
"""

import os
import json
import random
import shutil
from pathlib import Path

from core.file_scanner import IMAGE_EXTENSIONS, scan_image_json_pairs


def get_image_json_pairs(root_path: str) -> dict[str, list[tuple[str, str]]]:
    """递归获取所有图片及其对应的json文件对
    
    参数:
        root_path: 根目录路径
    
    返回:
        文件夹路径到 (图片名, json名) 列表的映射
    """
    exclude_dirs = ["照片检查+", "抽样结果", "ERROR_CHECK_RESULTS"]
    return scan_image_json_pairs(root_path, exclude_dirs=exclude_dirs)


def dispersed_sample(folder_map: dict, target_count: int) -> list[tuple[str, tuple[str, str]]]:
    """从多个文件夹中尽量均匀分散地抽取
    
    参数:
        folder_map: 文件夹映射
        target_count: 目标抽取数量
    
    返回:
        (文件夹路径, (图片名, json名)) 列表
    """
    selected_pairs = []
    folders = list(folder_map.keys())

    total_available = sum(len(v) for v in folder_map.values())
    if total_available <= target_count:
        for folder in folders:
            for pair in folder_map[folder]:
                selected_pairs.append((folder, pair))
        return selected_pairs

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


def run_sampler(source_dir: str, output_dir: str, sample_count: int = 50) -> tuple[str | None, str | None, dict]:
    """执行抽样逻辑
    
    参数:
        source_dir: 源文件夹路径
        output_dir: 输出目录路径
        sample_count: 抽样数量
    
    返回:
        (output_path, error, stats)
        - output_path: 输出目录路径，成功时返回
        - error: 错误信息，无错误返回 None
        - stats: {'sampled': int, 'labels': int, 'total_found': int}
    """
    if not os.path.isdir(source_dir):
        return None, "源文件夹不存在或不是有效目录", {}

    output_path = Path(output_dir).resolve()
    source_path = Path(source_dir).resolve()

    exclude_dirs = [str(output_path), "照片检查+", "抽样结果", "ERROR_CHECK_RESULTS"]
    folder_map = scan_image_json_pairs(source_dir, exclude_dirs=exclude_dirs)
    total_found = sum(len(v) for v in folder_map.values())

    if total_found == 0:
        return None, "源文件夹内未找到有效的图片和同名JSON对", {}

    output_path.mkdir(parents=True, exist_ok=True)

    sampled_list = dispersed_sample(folder_map, sample_count)
    total_labels = 0
    copied_count = 0

    for root_path, (img_name, json_name) in sampled_list:
        source_folder = Path(root_path).resolve()
        relative_folder = source_folder.relative_to(source_path)
        target_folder = output_path / relative_folder
        target_folder.mkdir(parents=True, exist_ok=True)

        image_src = source_folder / img_name
        image_dst = target_folder / img_name
        json_src = source_folder / json_name
        json_dst = target_folder / json_name

        shutil.copy2(image_src, image_dst)
        shutil.copy2(json_src, json_dst)
        copied_count += 1

        try:
            with open(json_dst, 'r', encoding='utf-8') as f:
                data = json.load(f)
                total_labels += len(data.get('shapes', []))
        except Exception:
            pass

    stats = {
        'sampled': copied_count,
        'labels': total_labels,
        'total_found': total_found,
        'supported_formats': list(IMAGE_EXTENSIONS),
    }

    return str(output_path), None, stats


def get_default_output_dir(source_dir: str) -> str:
    """获取默认输出目录路径
    
    参数:
        source_dir: 源文件夹路径
    
    返回:
        默认输出目录路径 (源目录/抽样结果)
    """
    base_name = os.path.basename(os.path.normpath(source_dir))
    return os.path.join(source_dir, f"抽样结果{base_name}")
