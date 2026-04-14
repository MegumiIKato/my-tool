import os
import re
from collections import defaultdict
from pathlib import Path

from openpyxl import Workbook

from core.file_scanner import is_image_file, scan_leaf_dir


CITY_BY_PREFIX = {
    "3301": "杭州市",
    "3302": "宁波市",
    "3303": "温州市",
    "3304": "嘉兴市",
    "3305": "湖州市",
    "3306": "绍兴市",
    "3307": "金华市",
    "3308": "衢州市",
    "3309": "舟山市",
    "3310": "台州市",
    "3311": "丽水市",
}


REGION_CODE_NAME_ROWS = [
    ("330102", "上城区"),
    ("330105", "拱墅区"),
    ("330106", "西湖区"),
    ("330108", "滨江区"),
    ("330109", "萧山区"),
    ("330110", "余杭区"),
    ("330111", "富阳区"),
    ("330112", "临安区"),
    ("330113", "临平区"),
    ("330114", "钱塘区"),
    ("330122", "桐庐县"),
    ("330127", "淳安县"),
    ("330182", "建德市"),
    ("330203", "海曙区"),
    ("330205", "江北区"),
    ("330206", "北仑区"),
    ("330211", "镇海区"),
    ("330212", "鄞州区"),
    ("330213", "奉化区"),
    ("330225", "象山县"),
    ("330226", "宁海县"),
    ("330281", "余姚市"),
    ("330282", "慈溪市"),
    ("330302", "鹿城区"),
    ("330303", "龙湾区"),
    ("330304", "瓯海区"),
    ("330305", "洞头区"),
    ("330324", "永嘉县"),
    ("330326", "平阳县"),
    ("330327", "苍南县"),
    ("330328", "文成县"),
    ("330329", "泰顺县"),
    ("330381", "瑞安市"),
    ("330382", "乐清市"),
    ("330383", "龙港市"),
    ("330402", "南湖区"),
    ("330411", "秀洲区"),
    ("330421", "嘉善县"),
    ("330424", "海盐县"),
    ("330481", "海宁市"),
    ("330482", "平湖市"),
    ("330483", "桐乡市"),
    ("330502", "吴兴区"),
    ("330503", "南浔区"),
    ("330521", "德清县"),
    ("330522", "长兴县"),
    ("330523", "安吉县"),
    ("330602", "越城区"),
    ("330603", "柯桥区"),
    ("330604", "上虞区"),
    ("330624", "新昌县"),
    ("330681", "诸暨市"),
    ("330683", "嵊州市"),
    ("330702", "婺城区"),
    ("330703", "金东区"),
    ("330723", "武义县"),
    ("330726", "浦江县"),
    ("330727", "磐安县"),
    ("330781", "兰溪市"),
    ("330782", "义乌市"),
    ("330783", "东阳市"),
    ("330784", "永康市"),
    ("330802", "柯城区"),
    ("330803", "衢江区"),
    ("330822", "常山县"),
    ("330824", "开化县"),
    ("330825", "龙游县"),
    ("330881", "江山市"),
    ("330902", "定海区"),
    ("330903", "普陀区"),
    ("330921", "岱山县"),
    ("330922", "嵊泗县"),
    ("331002", "椒江区"),
    ("331003", "黄岩区"),
    ("331004", "路桥区"),
    ("331022", "三门县"),
    ("331023", "天台县"),
    ("331024", "仙居县"),
    ("331081", "温岭市"),
    ("331082", "临海市"),
    ("331083", "玉环市"),
    ("331102", "莲都区"),
    ("331121", "青田县"),
    ("331122", "缙云县"),
    ("331123", "遂昌县"),
    ("331124", "松阳县"),
    ("331125", "云和县"),
    ("331126", "庆元县"),
    ("331127", "景宁畲族自治县"),
    ("331181", "龙泉市"),
]


REGION_NAME_ALIASES = {
    "景宁县": "景宁畲族自治县",
}

SUBMISSION_PATTERN = re.compile(r"第([0-9一二三四五六七八九十两零〇]+)次数据提交")
REGION_CODE_PATTERN = re.compile(r"^(\d{6})")
OUTPUT_FILENAME = "行政区提交配对统计结果.xlsx"


def _build_region_records() -> list[dict[str, str]]:
    """构建按映射表顺序排列的行政区记录。"""
    records = []
    for code, name in REGION_CODE_NAME_ROWS:
        city = CITY_BY_PREFIX[code[:4]]
        records.append({
            "code": code,
            "city": city,
            "name": name,
        })
    return records


REGION_RECORDS = _build_region_records()
REGION_BY_CODE = {record["code"]: record for record in REGION_RECORDS}
REGION_BY_NAME = {record["name"]: record for record in REGION_RECORDS}
for alias, target in REGION_NAME_ALIASES.items():
    REGION_BY_NAME[alias] = REGION_BY_NAME[target]


def _parse_chinese_number(value: str) -> int | None:
    """解析批次名称中的中文数字，仅需覆盖常见的十位以内场景。"""
    if not value:
        return None

    if value.isdigit():
        return int(value)

    digit_map = {
        "零": 0,
        "〇": 0,
        "一": 1,
        "二": 2,
        "两": 2,
        "三": 3,
        "四": 4,
        "五": 5,
        "六": 6,
        "七": 7,
        "八": 8,
        "九": 9,
    }

    if value == "十":
        return 10

    if "十" in value:
        left, right = value.split("十", 1)
        if left:
            tens = digit_map.get(left)
            if tens is None:
                return None
        else:
            tens = 1

        if right:
            ones = digit_map.get(right)
            if ones is None:
                return None
        else:
            ones = 0

        return tens * 10 + ones

    if len(value) == 1:
        return digit_map.get(value)

    return None


def _submission_sort_key(submission_name: str) -> tuple[int, str]:
    """按第几次提交排序，无法识别时按名称排后。"""
    match = SUBMISSION_PATTERN.search(submission_name)
    if not match:
        return 10**6, submission_name

    order = _parse_chinese_number(match.group(1))
    if order is None:
        return 10**6, submission_name

    return order, submission_name


def _extract_submission_and_region(root_folder: str, leaf_dir: str) -> tuple[str | None, str | None]:
    """从叶子目录相对路径中提取提交目录与行政区目录。"""
    root_path = Path(root_folder).resolve()
    leaf_path = Path(leaf_dir).resolve()

    try:
        relative_parts = leaf_path.relative_to(root_path).parts
    except Exception:
        return None, None

    for index, part in enumerate(relative_parts):
        if "次数据提交" not in part:
            continue

        if index + 2 >= len(relative_parts):
            return None, None

        return part, relative_parts[index + 2]

    return None, None


def _resolve_region(region_dir_name: str) -> dict[str, str] | None:
    """根据目录名解析行政区。"""
    region_name = region_dir_name.strip()
    if not region_name:
        return None

    code_match = REGION_CODE_PATTERN.match(region_name)
    if code_match:
        region = REGION_BY_CODE.get(code_match.group(1))
        if region:
            return region

        region_name = region_name[6:].strip()

    return REGION_BY_NAME.get(region_name)


def _apply_basic_styles(worksheet, submission_names: list[str]) -> None:
    """设置基础列宽，避免导出结果过于拥挤。"""
    worksheet.column_dimensions["A"].width = 14
    worksheet.column_dimensions["B"].width = 12
    worksheet.column_dimensions["C"].width = 20

    column_index = 4
    for submission_name in submission_names:
        column_letter = worksheet.cell(row=1, column=column_index).column_letter
        worksheet.column_dimensions[column_letter].width = max(len(submission_name) + 2, 18)
        column_index += 1


def _get_pairable_dirs(root_folder: str) -> list[str]:
    """返回所有实际存放图片或 JSON 的目录，按目录内局部配对。"""
    pairable_dirs = []
    for current_root, _dirs, files in os.walk(root_folder):
        has_candidate_files = any(is_image_file(file_name) or file_name.lower().endswith(".json") for file_name in files)
        if has_candidate_files:
            pairable_dirs.append(current_root)
    return pairable_dirs


def run_region_submission_count(root_folder: str) -> tuple[str | None, str | None, dict]:
    """统计根目录下各行政区在不同提交批次中的配对成功数。"""
    if not root_folder:
        return None, "未选择文件夹", {}

    if not os.path.isdir(root_folder):
        return None, "文件夹路径无效", {}

    pairable_dirs = _get_pairable_dirs(root_folder)
    if not pairable_dirs:
        return None, "未找到可扫描的图片或 JSON 所在目录", {}

    counts_by_region: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    submission_names = set()
    invalid_structure_samples = []
    unmatched_region_samples = []
    invalid_structure_count = 0
    unmatched_region_count = 0
    counted_leaf_folders = 0
    total_matched = 0

    for current_dir in pairable_dirs:
        submission_name, region_dir_name = _extract_submission_and_region(root_folder, current_dir)
        if not submission_name or not region_dir_name:
            invalid_structure_count += 1
            if len(invalid_structure_samples) < 10:
                invalid_structure_samples.append(current_dir)
            continue

        submission_names.add(submission_name)
        region = _resolve_region(region_dir_name)
        if region is None:
            unmatched_region_count += 1
            if len(unmatched_region_samples) < 10:
                unmatched_region_samples.append({
                    "region_dir": region_dir_name,
                    "leaf_dir": current_dir,
                })
            continue

        scan_result = scan_leaf_dir(current_dir)
        paired_count = scan_result["paired"]
        if paired_count <= 0:
            continue

        counts_by_region[region["code"]][submission_name] += paired_count
        counted_leaf_folders += 1
        total_matched += paired_count

    ordered_submissions = sorted(submission_names, key=_submission_sort_key)
    output_path = os.path.join(root_folder, OUTPUT_FILENAME)

    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = "统计结果"

    headers = ["行政区代码", "所在市", "行政区名称", *ordered_submissions]
    worksheet.append(headers)

    for region in REGION_RECORDS:
        region_counts = counts_by_region.get(region["code"], {})
        row = [int(region["code"]), region["city"], region["name"]]

        for submission_name in ordered_submissions:
            value = region_counts.get(submission_name)
            row.append(value if value else None)

        worksheet.append(row)

    _apply_basic_styles(worksheet, ordered_submissions)
    workbook.save(output_path)

    stats = {
        "total_pairable_dirs": len(pairable_dirs),
        "counted_pairable_dirs": counted_leaf_folders,
        "submission_count": len(ordered_submissions),
        "region_count_with_data": sum(1 for value in counts_by_region.values() if value),
        "total_matched": total_matched,
        "invalid_structure_count": invalid_structure_count,
        "unmatched_region_count": unmatched_region_count,
        "invalid_structure_samples": invalid_structure_samples,
        "unmatched_region_samples": unmatched_region_samples,
    }

    return output_path, None, stats
