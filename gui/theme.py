import customtkinter as ctk
import platform


ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")


# 主色调 - 按钮、链接、强调元素
COLOR_PRIMARY = "#2563EB"          # 主按钮背景色（蓝色）
COLOR_PRIMARY_HOVER = "#1D4ED8"    # 主按钮悬停色（深蓝）
COLOR_SUCCESS = "#10B981"           # 成功/完成按钮背景色（绿色）
COLOR_WARNING = "#F59E0B"           # 警告按钮背景色（黄色）
COLOR_ERROR = "#EF4444"             # 错误/删除按钮背景色（红色）


# 背景色 - 页面、卡片、输入框
COLOR_BG_MAIN = "#F8FAFC"           # 主内容区域背景色
COLOR_BG_SIDEBAR = "#FFFFFF"        # 侧边栏背景色
COLOR_BG_CARD = "#FFFFFF"           # 卡片/容器背景色
COLOR_BG_INPUT = "#F1F5F9"          # 输入框背景色


# 边框色 - 分割线、输入框边框
COLOR_BORDER = "#E2E8F0"            # 边框默认色
COLOR_BORDER_HOVER = "#CBD5E1"      # 边框悬停色


# 文字颜色 - 标题、正文、提示
COLOR_TEXT_PRIMARY = "#1E293B"      # 主要文字颜色（深灰，用于标题）
COLOR_TEXT_SECONDARY = "#64748B"    # 次要文字颜色（中灰，用于正文）
COLOR_TEXT_MUTED = "#94A3B8"        # 弱化文字颜色（浅灰，用于提示）


# 交互状态
COLOR_SIDEBAR_SELECTED = "#EFF6FF"  # 侧边栏按钮选中背景色


# 字体配置 - 按平台选择更稳定的中文字体，避免字形下沿被裁切
if platform.system() == "Windows":
    FONT_FAMILY = "Microsoft YaHei UI"
elif platform.system() == "Darwin":
    FONT_FAMILY = "PingFang SC"
else:
    FONT_FAMILY = "Noto Sans CJK SC"

APP_FONT = (FONT_FAMILY, 14)         # 常规字体
APP_FONT_BOLD = (FONT_FAMILY, 14, "bold")     # 粗体
APP_FONT_HEADER = (FONT_FAMILY, 20, "bold")   # 标题字体
APP_FONT_SMALL = (FONT_FAMILY, 12)            # 小号字体
