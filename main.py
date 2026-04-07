#!/usr/bin/env python
"""
Labelme 工具箱

功能说明：
- 整合五个标注数据处理工具的图形化界面工具箱
- 支持文件计数、孤立清理、标签校验、重叠检测、抽样检查

工具列表：
1. 文件计数与匹配统计
2. 孤立文件清理
3. 标签正确性检查
4. 多边形重叠情况检查
5. 检查抽样
"""

import sys
from gui.main_window import MainWindow


def main():
    app = MainWindow()
    app.mainloop()


if __name__ == "__main__":
    main()
