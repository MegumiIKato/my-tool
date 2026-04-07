"""
多边形重叠检查工具。

功能说明：
- 递归扫描目录中的 Labelme JSON 文件
- 检查 polygon 标注之间是否存在重叠
- 对问题 shape 的标签写入 [重叠] 前缀，并将问题 shape 排到前面
- 将有问题的 JSON 和对应图片复制到输出目录，保留原目录结构
- 生成 xlsx 格式的检查报告
"""

import json
import os
import shutil
from pathlib import Path

from openpyxl import Workbook
from shapely.geometry import Polygon
from shapely.strtree import STRtree

from core.file_scanner import IMAGE_EXTENSIONS


DEFAULT_OUTPUT_DIR_NAME = "ERROR_CHECK_RESULTS"
REPORT_FILE_NAME = "polygon_overlap_report.xlsx"
OVERLAP_LABEL_PREFIX = "[重叠] "


def _iter_json_files(source_dir: Path, output_dir: Path) -> list[Path]:
    """递归获取待检查的 JSON 文件，跳过结果目录。"""
    json_files = []

    for json_path in source_dir.rglob("*.json"):
        try:
            json_path.relative_to(output_dir)
            continue
        except ValueError:
            json_files.append(json_path)

    return json_files


def _find_image_for_json(json_path: Path) -> Path | None:
    """查找与 JSON 同名的图片文件。"""
    json_stem = json_path.stem.lower()
    for child in json_path.parent.iterdir():
        if not child.is_file():
            continue
        if child.stem.lower() != json_stem:
            continue
        if child.suffix.lower() in IMAGE_EXTENSIONS:
            return child
    return None


def _build_polygon_shape(shape: dict) -> Polygon | None:
    """将 polygon shape 转为可计算的几何对象。"""
    if shape.get("shape_type") != "polygon":
        return None

    points = shape.get("points", [])
    if len(points) < 3:
        return None

    try:
        polygon = Polygon(points)
    except Exception:
        return None

    if not polygon.is_valid:
        polygon = polygon.buffer(0)

    if polygon.is_empty or polygon.area <= 0:
        return None

    return polygon


def _mark_overlap_label(label: str) -> str:
    """为有问题的标签增加可见前缀。"""
    clean_label = str(label or "").strip()
    if clean_label.startswith(OVERLAP_LABEL_PREFIX):
        return clean_label
    return f"{OVERLAP_LABEL_PREFIX}{clean_label}" if clean_label else OVERLAP_LABEL_PREFIX.strip()


def _format_overlap_pairs(polygons: list[dict], overlap_pairs: set[tuple[int, int]]) -> str:
    """格式化重叠对信息，用于报告展示。"""
    pair_texts = []

    for left_index, right_index in sorted(overlap_pairs):
        left_label = str(polygons[left_index]["shape"].get("label", "")).strip() or "<空标签>"
        right_label = str(polygons[right_index]["shape"].get("label", "")).strip() or "<空标签>"
        pair_texts.append(f"{left_label} <-> {right_label}")

    return "；".join(pair_texts)


def _write_report(output_path: Path, details: list[dict]) -> str:
    """生成 xlsx 格式报告。"""
    report_path = output_path / REPORT_FILE_NAME

    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = "重叠检查报告"
    worksheet.append(["序号", "文件路径", "问题形状数", "重叠对数", "重叠情况", "提示"])

    row_index = 1
    for detail in details:
        if detail["overlap_shape_count"] <= 0:
            continue

        worksheet.append([
            row_index,
            detail["file"],
            detail["overlap_shape_count"],
            detail["overlap_pair_count"],
            detail["overlap_pairs_text"],
            detail["warning"],
        ])
        row_index += 1

    if row_index == 1:
        worksheet.append([1, "-", 0, 0, "未发现重叠问题", ""])

    workbook.save(report_path)
    return str(report_path)


def analyze_overlap(json_path: str, threshold: float = 0.1) -> tuple[dict | None, dict]:
    """分析单个 JSON 的多边形重叠情况。"""
    detail = {
        "has_overlap": False,
        "overlap_shape_count": 0,
        "overlap_pair_count": 0,
        "overlap_pairs_text": "",
        "warning": "",
    }

    try:
        with open(json_path, "r", encoding="utf-8") as file:
            data = json.load(file)
    except Exception as exc:
        detail["warning"] = f"文件读取失败: {str(exc)}"
        return None, detail

    shapes = data.get("shapes", [])
    if not shapes:
        return None, detail

    polygons = []
    other_shapes = []
    invalid_polygon_count = 0

    for index, shape in enumerate(shapes):
        polygon = _build_polygon_shape(shape)
        if polygon is None:
            if shape.get("shape_type") == "polygon":
                points = shape.get("points", [])
                if len(points) >= 3:
                    invalid_polygon_count += 1
            other_shapes.append(shape)
            continue

        polygons.append({
            "index": index,
            "shape": shape,
            "geom": polygon,
        })

    if invalid_polygon_count > 0:
        detail["warning"] = f"发现 {invalid_polygon_count} 个无效 polygon，已跳过"

    if len(polygons) < 2:
        return None, detail

    geom_list = [item["geom"] for item in polygons]
    tree = STRtree(geom_list)
    overlap_indices = set()
    overlap_pairs = set()

    for current_index, polygon_info in enumerate(polygons):
        current_geom = polygon_info["geom"]

        try:
            match_indices = tree.query(current_geom, predicate="intersects")
        except Exception as exc:
            detail["warning"] = f"几何计算失败: {str(exc)}"
            return None, detail

        for match_index in match_indices:
            if current_index == match_index:
                continue

            pair = tuple(sorted((current_index, match_index)))
            if pair in overlap_pairs:
                continue

            try:
                intersection_area = current_geom.intersection(polygons[match_index]["geom"]).area
            except Exception:
                continue

            if intersection_area > threshold:
                overlap_indices.add(current_index)
                overlap_indices.add(match_index)
                overlap_pairs.add(pair)

    if not overlap_indices:
        return None, detail

    error_shapes = []
    normal_shapes = []

    for polygon_index, polygon_info in enumerate(polygons):
        shape_data = dict(polygon_info["shape"])

        if polygon_index in overlap_indices:
            shape_data["label"] = _mark_overlap_label(shape_data.get("label", ""))
            error_shapes.append(shape_data)
        else:
            normal_shapes.append(shape_data)

    data["shapes"] = error_shapes + normal_shapes + other_shapes
    detail["has_overlap"] = True
    detail["overlap_shape_count"] = len(overlap_indices)
    detail["overlap_pair_count"] = len(overlap_pairs)
    detail["overlap_pairs_text"] = _format_overlap_pairs(polygons, overlap_pairs)
    return data, detail


def run_polygon_overlap_check(
    source_dir: str,
    threshold: float = 0.1,
    output_dir: str | None = None,
) -> tuple[str | None, str | None, dict]:
    """批量执行多边形重叠检查。"""
    empty_stats = {
        "total_files": 0,
        "checked_files": 0,
        "error_files": 0,
        "skipped_files": 0,
        "total_overlap_shapes": 0,
        "total_overlap_pairs": 0,
        "report_path": "",
        "details": [],
    }

    if not source_dir:
        return None, "未选择源文件夹", empty_stats

    source_path = Path(source_dir)
    if not source_path.is_dir():
        return None, "源文件夹不存在或不是有效目录", empty_stats

    if threshold < 0:
        return None, "重叠面积阈值不能小于 0", empty_stats

    if output_dir:
        output_path = Path(output_dir)
    else:
        output_path = source_path / DEFAULT_OUTPUT_DIR_NAME

    all_json_files = _iter_json_files(source_path, output_path)
    empty_stats["total_files"] = len(all_json_files)

    if not all_json_files:
        return None, "源文件夹内未找到 JSON 文件", empty_stats

    output_path.mkdir(parents=True, exist_ok=True)

    stats = {
        "total_files": len(all_json_files),
        "checked_files": 0,
        "error_files": 0,
        "skipped_files": 0,
        "total_overlap_shapes": 0,
        "total_overlap_pairs": 0,
        "report_path": "",
        "details": [],
    }

    for json_file in all_json_files:
        modified_data, detail = analyze_overlap(str(json_file), threshold)
        relative_path = os.path.relpath(json_file, source_path)

        if detail["warning"].startswith("文件读取失败"):
            stats["skipped_files"] += 1
            stats["details"].append({
                "file": relative_path,
                "overlap_shape_count": 0,
                "overlap_pair_count": 0,
                "overlap_pairs_text": "",
                "image_found": False,
                "warning": detail["warning"],
            })
            continue

        stats["checked_files"] += 1

        if not modified_data:
            if detail["warning"]:
                stats["details"].append({
                    "file": relative_path,
                    "overlap_shape_count": 0,
                    "overlap_pair_count": 0,
                    "overlap_pairs_text": "",
                    "image_found": False,
                    "warning": detail["warning"],
                })
            continue

        target_json_path = output_path / relative_path
        target_json_path.parent.mkdir(parents=True, exist_ok=True)

        with open(target_json_path, "w", encoding="utf-8") as file:
            json.dump(modified_data, file, indent=2, ensure_ascii=False)

        image_path = _find_image_for_json(json_file)
        image_found = image_path is not None

        if image_path:
            target_image_path = target_json_path.with_suffix(image_path.suffix)
            shutil.copy2(image_path, target_image_path)

        warning = detail["warning"]
        if not image_found:
            warning = f"{warning}；未找到对应图片" if warning else "未找到对应图片"

        stats["error_files"] += 1
        stats["total_overlap_shapes"] += detail["overlap_shape_count"]
        stats["total_overlap_pairs"] += detail["overlap_pair_count"]
        stats["details"].append({
            "file": relative_path,
            "overlap_shape_count": detail["overlap_shape_count"],
            "overlap_pair_count": detail["overlap_pair_count"],
            "overlap_pairs_text": detail["overlap_pairs_text"],
            "image_found": image_found,
            "warning": warning,
        })

    stats["report_path"] = _write_report(output_path, stats["details"])
    return str(output_path), None, stats
