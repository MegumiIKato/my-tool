import json
from pathlib import Path
from typing import Any


def load_labelme_json(json_path: Path) -> dict | None:
    """加载 Labelme JSON 文件"""
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return None


def save_labelme_json(json_path: Path, data: dict) -> bool:
    """保存 Labelme JSON 文件"""
    try:
        json_path.parent.mkdir(parents=True, exist_ok=True)
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception:
        return False


def get_shapes(data: dict) -> list[dict]:
    """获取 shapes 列表"""
    return data.get('shapes', [])


def get_labels(data: dict) -> list[str]:
    """获取所有标签名称"""
    return [s.get('label', '') for s in data.get('shapes', [])]


def get_polygon_points(shapes: list[dict]) -> list[list[tuple[float, float]]]:
    """从 shapes 中提取所有多边形点"""
    polygons = []
    for s in shapes:
        if s.get('shape_type') == 'polygon':
            points = s.get('points', [])
            if len(points) >= 3:
                polygons.append(points)
    return polygons


def validate_labels(shapes: list[dict], valid_codes: set) -> list[str]:
    """验证标签是否合法
    
    返回:
        无效标签列表
    """
    invalid = set()
    for shape in shapes:
        label = str(shape.get('label', '')).strip()
        if label and label not in valid_codes:
            invalid.add(label)
    return list(invalid)
