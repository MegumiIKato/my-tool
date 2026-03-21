"""
Excel 转字符串转换器 (Excel to String Converter)

功能说明：
- 自动查找当前目录下的第一个 Excel 文件
- 读取指定列（默认为 B 列）的数据
- 将数据转换为字符串并用英文分号连接
- 输出处理结果和统计信息

使用场景：
- 批量提取 Excel 数据
- 生成标签列表
- 数据格式转换
"""

import pandas as pd
import os
import glob


def process_single_excel():
    xlsx_files = glob.glob("*.xlsx")

    if not xlsx_files:
        print("错误：当前目录下未找到 .xlsx 文件。")
        return

    file_path = xlsx_files[0]
    print(f"正在读取文件: {file_path}")

    try:
        df = pd.read_excel(file_path, usecols="B")

        column_c_name = df.columns[0]

        data_list = df[column_c_name].dropna().astype(str).tolist()

        result_str = ";".join(data_list)

        print("\n--- 处理结果 ---")
        if result_str:
            print(result_str)
        else:
            print("(该列没有数据)")

        print("\n--- 统计信息 ---")
        print(f"总数计数: {len(data_list)}")

    except Exception as e:
        print(f"处理过程中出现错误: {e}")


if __name__ == "__main__":
    process_single_excel()
