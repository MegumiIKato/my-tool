import os
from pathlib import Path
import sys
import threading
import time
from tkinter import PhotoImage, filedialog

import customtkinter as ctk

from .theme import *
from tools.image_count import run_count
from tools.image_json_sampler import run_sampler, get_default_output_dir
from tools.label_validator import run_validator, export_template
from tools.orphan_image_cleaner import run_scan, run_clean
from tools.polygon_overlap_checker import run_polygon_overlap_check


HELP_TEXTS = {
    "image_count": [
        "选择扫描文件夹后点击“开始扫描”，结果会导出为 Excel。",
        "只在叶子文件夹内配对，支持 jpg、jpeg、png、tif、tiff。",
        "结果文件保存在源目录，文件名为 文件计数统计结果.xlsx。",
    ],
    "orphan_cleaner": [
        "先扫描查看统计结果，再按需要选择删除孤立图片或孤立 JSON。",
        "同名多格式图片加 JSON 会视为特殊配对，不会自动删除。",
        "删除操作不可恢复，建议先确认扫描结果。",
    ],
    "label_validator": [
        "先选择待检查文件夹，再上传字典文件后开始检查。",
        "字典支持 csv、txt、xlsx、xls；表头第一列需为 label。",
        "检查报告保存在源目录，文件名为 标签校验报告.xlsx。",
    ],
    "polygon_checker": [
        "选择源文件夹，可设置阈值和输出目录，然后开始检查。",
        "只检查 polygon，原始文件不会被修改，问题副本会单独导出。",
        "默认生成 ERROR_CHECK_RESULTS 目录，并输出 多边形重叠检查报告.xlsx 报告。",
    ],
    "sampler": [
        "选择源文件夹，设置抽样数量和输出目录后开始抽样。",
        "若不填写输出目录，会在源目录下自动创建抽样结果文件夹。",
        "会复制抽中的图片与 JSON，并统计 shapes 总数。",
    ],
}


def get_asset_path(filename: str) -> Path:
    """获取图标等静态资源路径，兼容开发环境与 PyInstaller 打包环境。"""
    if hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS) / "assets" / filename

    return Path(__file__).resolve().parents[1] / "assets" / filename


def create_modal_window(owner, title: str, width: int, height: int) -> ctk.CTkToplevel:
    """创建绑定到主窗口的模态弹窗，并居中显示。"""
    parent_window = owner.winfo_toplevel()

    window = ctk.CTkToplevel(parent_window)
    window.title(title)
    window.geometry(f"{width}x{height}")
    window.resizable(False, False)
    window.configure(fg_color=COLOR_BG_MAIN)
    window.transient(parent_window)
    window.grab_set()
    window.lift()

    parent_window.update_idletasks()
    parent_x = parent_window.winfo_rootx()
    parent_y = parent_window.winfo_rooty()
    parent_width = parent_window.winfo_width()
    parent_height = parent_window.winfo_height()

    pos_x = parent_x + max((parent_width - width) // 2, 0)
    pos_y = parent_y + max((parent_height - height) // 2, 0)
    window.geometry(f"{width}x{height}+{pos_x}+{pos_y}")
    window.focus()
    return window


def create_modal_header(window, title: str, description: str | None = None) -> ctk.CTkFrame:
    """创建统一风格的弹窗头部。"""
    header = ctk.CTkFrame(
        window,
        fg_color=COLOR_BG_CARD,
        corner_radius=12,
        border_width=1,
        border_color=COLOR_BORDER,
    )
    header.pack(fill="x", padx=20, pady=(20, 12))

    ctk.CTkLabel(
        header,
        text=title,
        font=APP_FONT_BOLD,
        text_color=COLOR_TEXT_PRIMARY,
    ).pack(anchor="w", padx=18, pady=(16, 6))

    if description:
        ctk.CTkLabel(
            header,
            text=description,
            font=APP_FONT,
            text_color=COLOR_TEXT_SECONDARY,
            justify="left",
            anchor="w",
            wraplength=480,
        ).pack(fill="x", padx=18, pady=(0, 16))

    return header


class ToolHelpCard(ctk.CTkFrame):
    """工具帮助说明卡片。"""

    EXPAND_ARROW = "◀"
    COLLAPSE_ARROW = "▼"

    def __init__(self, master, lines: list[str], **kwargs):
        super().__init__(master, fg_color=COLOR_BG_CARD, corner_radius=12, **kwargs)

        self.lines = lines
        self.expanded = False

        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.pack(fill="x", padx=15, pady=(10, 8))

        self.title_label = ctk.CTkLabel(
            self.header_frame,
            text="帮助说明",
            font=APP_FONT,
            text_color=COLOR_TEXT_PRIMARY,
        )
        self.title_label.pack(side="left")

        self.arrow_label = ctk.CTkLabel(
            self.header_frame,
            text=self.EXPAND_ARROW,
            font=APP_FONT_BOLD,
            text_color=COLOR_TEXT_MUTED,
        )
        self.arrow_label.pack(side="right")

        self.content_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.content_labels = []

        self._bind_toggle_events()

        for line in lines:
            item_label = ctk.CTkLabel(
                self.content_frame,
                text=line,
                font=APP_FONT_SMALL,
                text_color=COLOR_TEXT_SECONDARY,
                justify="left",
                anchor="w",
                wraplength=760,
            )
            self.content_labels.append(item_label)

    def _bind_toggle_events(self):
        self.header_frame.bind("<Button-1>", self._toggle)
        self.title_label.bind("<Button-1>", self._toggle)
        self.arrow_label.bind("<Button-1>", self._toggle)

    def _toggle(self, _event=None):
        if self.expanded:
            self.content_frame.pack_forget()
            self.arrow_label.configure(text=self.EXPAND_ARROW)
            self.expanded = False
            return

        self.content_frame.pack(fill="x", padx=15, pady=(0, 10))
        self.arrow_label.configure(text=self.COLLAPSE_ARROW)
        for item_label in self.content_labels:
            item_label.pack(fill="x", anchor="w", pady=(0, 6))
        self.expanded = True


class OrphanCleanerPanel(ctk.CTkFrame):
    """孤立文件清理工具面板"""

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)

        self._create_ui()

    def _create_ui(self):
        self.title_label = ctk.CTkLabel(
            self, text="孤立文件清理",
            font=APP_FONT_HEADER, text_color=COLOR_TEXT_PRIMARY
        )
        self.title_label.pack(anchor="w", pady=(20, 10), padx=20)

        self.desc_label = ctk.CTkLabel(
            self,
            text="清理孤立的图片或JSON文件",
            font=APP_FONT, text_color=COLOR_TEXT_SECONDARY
        )
        self.desc_label.pack(anchor="w", pady=(0, 20), padx=20)

        self.help_card = ToolHelpCard(self, lines=HELP_TEXTS["orphan_cleaner"])
        self.help_card.pack(fill="x", padx=20, pady=(0, 15))

        self.params_card = ctk.CTkFrame(self, fg_color=COLOR_BG_CARD, corner_radius=12)
        self.params_card.pack(fill="x", padx=20, pady=(0, 15))

        self.mode_frame = ctk.CTkFrame(self.params_card, fg_color="transparent")
        self.mode_frame.pack(fill="x", padx=15, pady=(15, 10))

        self.mode_label = ctk.CTkLabel(
            self.mode_frame, text="清理模式", font=APP_FONT,
            text_color=COLOR_TEXT_SECONDARY
        )
        self.mode_label.pack(side="left", padx=(0, 10))

        self.mode_var = ctk.StringVar(value="image")

        self.radio_image = ctk.CTkRadioButton(
            self.mode_frame, text="删除孤立图片",
            variable=self.mode_var, value="image",
            font=APP_FONT, fg_color=COLOR_PRIMARY,
            command=self._refresh_clean_button_state
        )
        self.radio_image.pack(side="left", padx=(0, 15))

        self.radio_json = ctk.CTkRadioButton(
            self.mode_frame, text="删除孤立JSON",
            variable=self.mode_var, value="json",
            font=APP_FONT, fg_color=COLOR_PRIMARY,
            command=self._refresh_clean_button_state
        )
        self.radio_json.pack(side="left")

        self.folder_selector = PathSelector(
            self.params_card, label="源文件夹"
        )
        self.folder_selector.pack(fill="x", padx=15, pady=(0, 15))

        self.info_label = ctk.CTkLabel(
            self.params_card,
            text="支持图片格式: jpg, jpeg, png, tif, tiff",
            font=APP_FONT_SMALL, text_color=COLOR_TEXT_MUTED
        )
        self.info_label.pack(anchor="w", padx=15, pady=(0, 15))

        self.buttons_card = ctk.CTkFrame(self, fg_color="transparent")
        self.buttons_card.pack(fill="x", padx=20, pady=(0, 15))

        self.btn_scan = ctk.CTkButton(
            self.buttons_card, text="开始扫描",
            font=APP_FONT_BOLD, height=45,
            fg_color=COLOR_PRIMARY, hover_color=COLOR_PRIMARY_HOVER,
            text_color="#FFFFFF",
            command=self._run_scan
        )
        self.btn_scan.pack(side="left", padx=(0, 10))

        self.btn_clean = ctk.CTkButton(
            self.buttons_card, text="开始清理",
            font=APP_FONT_BOLD, height=45,
            fg_color="#EF4444", hover_color="#DC2626",
            text_color="#FFFFFF",
            command=self._run_clean,
            state="disabled"
        )
        self.btn_clean.pack(side="left", padx=(0, 10))

        self.btn_clear = ctk.CTkButton(
            self.buttons_card, text="清空",
            font=APP_FONT, height=45,
            fg_color=COLOR_TEXT_MUTED, hover_color=COLOR_BORDER,
            text_color="#FFFFFF",
            command=self._clear_input
        )
        self.btn_clear.pack(side="left")

        self.scan_result_card = ctk.CTkFrame(self, fg_color=COLOR_BG_CARD, corner_radius=12)
        self.scan_result_card.pack(fill="x", padx=20, pady=(0, 15))

        self.scan_result_label = ctk.CTkLabel(
            self.scan_result_card, text="扫描结果",
            font=APP_FONT_BOLD, text_color=COLOR_TEXT_PRIMARY
        )
        self.scan_result_label.pack(anchor="w", padx=15, pady=(10, 5))

        self.stats_frame = ctk.CTkFrame(self.scan_result_card, fg_color="transparent")
        self.stats_frame.pack(fill="x", padx=15, pady=(0, 5))

        self.row1_frame = ctk.CTkFrame(self.stats_frame, fg_color="transparent")
        self.row1_frame.pack(fill="x")

        self.lbl_paired = ctk.CTkLabel(
            self.row1_frame, text="有效配对: 0 对",
            font=APP_FONT, text_color=COLOR_TEXT_SECONDARY
        )
        self.lbl_paired.pack(side="left", padx=(0, 20))

        self.lbl_orphan_image = ctk.CTkLabel(
            self.row1_frame, text="孤立图片: 0 个",
            font=APP_FONT, text_color="#EF4444"
        )
        self.lbl_orphan_image.pack(side="left", padx=(0, 20))

        self.lbl_orphan_json = ctk.CTkLabel(
            self.row1_frame, text="孤立JSON: 0 个",
            font=APP_FONT, text_color="#EF4444"
        )
        self.lbl_orphan_json.pack(side="left")

        self.row2_frame = ctk.CTkFrame(self.stats_frame, fg_color="transparent")
        self.row2_frame.pack(fill="x", pady=(5, 10))

        self.lbl_special = ctk.CTkLabel(
            self.row2_frame, text="特殊配对: 0 组",
            font=APP_FONT, text_color="#F59E0B"
        )
        self.lbl_special.pack(side="left", padx=(0, 20))

        self.lbl_folder = ctk.CTkLabel(
            self.row2_frame, text="扫描文件夹: 0 个",
            font=APP_FONT, text_color=COLOR_TEXT_SECONDARY
        )
        self.lbl_folder.pack(side="left")

        self.log_card = ctk.CTkFrame(self, fg_color=COLOR_BG_CARD, corner_radius=12)
        self.log_card.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        self.log_label = ctk.CTkLabel(
            self.log_card, text="执行日志",
            font=APP_FONT_BOLD, text_color=COLOR_TEXT_PRIMARY
        )
        self.log_label.pack(anchor="w", padx=15, pady=(10, 5))

        self.log_viewer = LogViewer(self.log_card, height=160)
        self.log_viewer.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        self.scan_stats = None

    def _run_scan(self):
        target_dir = self.folder_selector.get()
        if not target_dir:
            self.log_viewer.append("请选择源文件夹")
            return

        self.btn_scan.configure(state="disabled", text="扫描中...")
        self.log_viewer.clear()
        self.log_viewer.append(f"开始扫描文件夹: {target_dir}")
        self.log_viewer.append(f"支持图片格式: jpg, jpeg, png, tif, tiff")

        start_time = time.time()

        def run_task():
            try:
                stats, error = run_scan(target_dir)
            except Exception as exc:
                stats, error = None, f"执行扫描失败: {str(exc)}"
            elapsed = time.time() - start_time
            self.after(0, lambda: self._on_scan_complete(stats, error, elapsed))

        thread = threading.Thread(target=run_task, daemon=True)
        thread.start()

    def _on_scan_complete(self, stats, error, elapsed):
        self.btn_scan.configure(state="normal", text="开始扫描")

        if error:
            self.log_viewer.append(f"错误: {error}")
            return

        self.scan_stats = stats
        self.log_viewer.append(f"扫描完成! 用时: {elapsed:.2f}秒")
        self.log_viewer.append(f"有效配对: {stats['paired']} 对")
        self.log_viewer.append(f"孤立图片: {stats['orphan_image']} 个")
        self.log_viewer.append(f"孤立JSON: {stats['orphan_json']} 个")
        self.log_viewer.append(f"扫描文件夹: {stats['folder_count']} 个")

        special_count = len(stats.get('special_pairs', []))
        self.lbl_paired.configure(text=f"有效配对: {stats['paired']} 对")
        self.lbl_orphan_image.configure(text=f"孤立图片: {stats['orphan_image']} 个")
        self.lbl_orphan_json.configure(text=f"孤立JSON: {stats['orphan_json']} 个")
        self.lbl_special.configure(text=f"特殊配对: {special_count} 组")
        self.lbl_folder.configure(text=f"扫描文件夹: {stats['folder_count']} 个")

        if special_count > 0:
            self.log_viewer.append(f"特殊配对: {special_count} 组（需要手动处理）")
            self.log_viewer.append("--- 特殊配对详情 ---")
            for i, sp in enumerate(stats['special_pairs'][:10], 1):
                folder_name = os.path.basename(sp['folder']) or sp['folder']
                self.log_viewer.append(f"[{i}] {folder_name}: {', '.join(sp['files'])}")
            if special_count > 10:
                self.log_viewer.append(f"... 还有 {special_count - 10} 组")

        self._refresh_clean_button_state()

    def _refresh_clean_button_state(self):
        if not self.scan_stats:
            self.btn_clean.configure(state="disabled")
            return

        mode = self.mode_var.get()
        orphan_count = self.scan_stats['orphan_image'] if mode == 'image' else self.scan_stats['orphan_json']
        self.btn_clean.configure(state="normal" if orphan_count > 0 else "disabled")

    def _run_clean(self):
        target_dir = self.folder_selector.get()
        if not target_dir:
            self.log_viewer.append("请选择源文件夹")
            return

        if not self.scan_stats:
            self.log_viewer.append("请先执行扫描")
            return

        mode = self.mode_var.get()
        orphan_count = self.scan_stats['orphan_image'] if mode == 'image' else self.scan_stats['orphan_json']

        if orphan_count == 0:
            self.log_viewer.append("没有需要清理的文件")
            return

        mode_text = "孤立图片" if mode == 'image' else "孤立JSON"
        confirm_text = f"确定要删除 {orphan_count} 个{mode_text}吗？\n\n此操作不可恢复！"

        confirm_window = create_modal_window(self, "确认清理", 400, 180)
        create_modal_header(confirm_window, "确认清理", "请再次确认本次删除操作，删除后无法恢复。")

        ctk.CTkLabel(
            confirm_window, text=confirm_text,
            font=APP_FONT, text_color=COLOR_TEXT_PRIMARY,
            wraplength=350
        ).pack(padx=24, pady=(6, 20))

        btn_frame = ctk.CTkFrame(confirm_window, fg_color="transparent")
        btn_frame.pack(pady=(0, 20))

        def do_clean():
            confirm_window.destroy()
            self._execute_clean(target_dir, mode)

        def cancel():
            confirm_window.destroy()

        ctk.CTkButton(
            btn_frame, text="确认删除",
            font=APP_FONT_BOLD, width=120, height=40,
            fg_color="#EF4444", hover_color="#DC2626",
            text_color="#FFFFFF",
            command=do_clean
        ).pack(side="left", padx=(0, 15))

        ctk.CTkButton(
            btn_frame, text="取消",
            font=APP_FONT, width=100, height=40,
            fg_color=COLOR_TEXT_MUTED, hover_color=COLOR_BORDER,
            text_color="#FFFFFF",
            command=cancel
        ).pack(side="left")

    def _execute_clean(self, target_dir, mode):
        self.btn_clean.configure(state="disabled", text="清理中...")
        self.log_viewer.append(f"开始清理...")
        mode_text = "孤立图片" if mode == 'image' else "孤立JSON"

        start_time = time.time()

        def run_task():
            try:
                stats, error = run_clean(target_dir, mode)
            except Exception as exc:
                stats, error = None, f"执行清理失败: {str(exc)}"
            elapsed = time.time() - start_time
            self.after(0, lambda: self._on_clean_complete(stats, error, elapsed, mode_text))

        thread = threading.Thread(target=run_task, daemon=True)
        thread.start()

    def _on_clean_complete(self, stats, error, elapsed, mode_text):
        self.btn_clean.configure(state="normal", text="开始清理")

        if error:
            self.log_viewer.append(f"错误: {error}")
            return

        self.log_viewer.append(f"清理完成! 用时: {elapsed:.2f}秒")
        self.log_viewer.append(f"已删除{mode_text}: {stats['deleted']} 个")
        failed_files = stats.get('failed', [])
        if failed_files:
            self.log_viewer.append(f"删除失败: {len(failed_files)} 个")
            for item in failed_files[:5]:
                self.log_viewer.append(f"失败文件: {item['path']} | {item['reason']}")
            if len(failed_files) > 5:
                self.log_viewer.append(f"... 还有 {len(failed_files) - 5} 个删除失败")
        self.log_viewer.append(f"剩余有效配对: {stats['paired']} 对")

        special_count = len(stats.get('special_pairs', []))
        self.lbl_paired.configure(text=f"有效配对: {stats['paired']} 对")
        self.lbl_orphan_image.configure(text=f"孤立图片: {stats['orphan_image']} 个")
        self.lbl_orphan_json.configure(text=f"孤立JSON: {stats['orphan_json']} 个")
        self.lbl_special.configure(text=f"特殊配对: {special_count} 组")

        if special_count > 0:
            self.log_viewer.append("")
            self.log_viewer.append(f"注意: 存在 {special_count} 组特殊配对文件，请手动检查处理")

        self.scan_stats = stats
        self._refresh_clean_button_state()

    def _clear_input(self):
        self.folder_selector.set("")
        self.mode_var.set("image")
        self.scan_stats = None
        self.log_viewer.clear()
        self.lbl_paired.configure(text="有效配对: 0 对")
        self.lbl_orphan_image.configure(text="孤立图片: 0 个")
        self.lbl_orphan_json.configure(text="孤立JSON: 0 个")
        self.lbl_special.configure(text="特殊配对: 0 组")
        self.lbl_folder.configure(text="扫描文件夹: 0 个")
        self._refresh_clean_button_state()


class LabelValidatorPanel(ctk.CTkFrame):
    """标签校验工具面板"""

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)

        self._create_ui()

    def _create_ui(self):
        self.title_label = ctk.CTkLabel(
            self, text="标签正确性检查",
            font=APP_FONT_HEADER, text_color=COLOR_TEXT_PRIMARY
        )
        self.title_label.pack(anchor="w", pady=(20, 10), padx=20)

        self.desc_label = ctk.CTkLabel(
            self,
            text="校验 JSON 文件中的标签是否在有效字典中",
            font=APP_FONT, text_color=COLOR_TEXT_SECONDARY
        )
        self.desc_label.pack(anchor="w", pady=(0, 20), padx=20)

        self.help_card = ToolHelpCard(self, lines=HELP_TEXTS["label_validator"])
        self.help_card.pack(fill="x", padx=20, pady=(0, 15))

        self.params_card = ctk.CTkFrame(self, fg_color=COLOR_BG_CARD, corner_radius=12)
        self.params_card.pack(fill="x", padx=20, pady=(0, 15))

        self.folder_selector = PathSelector(
            self.params_card, label="待校验文件夹"
        )
        self.folder_selector.pack(fill="x", padx=15, pady=(15, 10))

        self.dict_frame = ctk.CTkFrame(self.params_card, fg_color="transparent")
        self.dict_frame.pack(fill="x", padx=15, pady=(0, 10))

        self.dict_label = ctk.CTkLabel(
            self.dict_frame, text="标签字典", font=APP_FONT,
            text_color=COLOR_TEXT_SECONDARY
        )
        self.dict_label.pack(side="left", padx=(0, 10))

        self.dict_var = ctk.StringVar()
        self.dict_entry = ctk.CTkEntry(
            self.dict_frame, textvariable=self.dict_var, font=APP_FONT,
            placeholder_text="请上传标签字典文件",
            placeholder_text_color=COLOR_TEXT_MUTED,
            fg_color=COLOR_BG_INPUT, border_color=COLOR_BORDER
        )
        self.dict_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))

        self.btn_upload = ctk.CTkButton(
            self.dict_frame, text="上传", font=APP_FONT,
            width=70, fg_color=COLOR_PRIMARY, hover_color=COLOR_PRIMARY_HOVER,
            text_color="#FFFFFF",
            command=self._upload_dict
        )
        self.btn_upload.pack(side="left", padx=(0, 10))

        self.btn_format_help = ctk.CTkButton(
            self.dict_frame, text="格式说明", font=APP_FONT,
            width=80, fg_color=COLOR_TEXT_MUTED, hover_color=COLOR_BORDER,
            text_color="#FFFFFF",
            command=self._show_format_help
        )
        self.btn_format_help.pack(side="left")

        self.dict_preview = ctk.CTkLabel(
            self.params_card,
            text="",
            font=APP_FONT_SMALL, text_color=COLOR_TEXT_MUTED
        )
        self.dict_preview.pack(anchor="w", padx=15, pady=(0, 15))

        self.buttons_card = ctk.CTkFrame(self, fg_color="transparent")
        self.buttons_card.pack(fill="x", padx=20, pady=(0, 15))

        self.btn_run = ctk.CTkButton(
            self.buttons_card, text="开始检查",
            font=APP_FONT_BOLD, height=45,
            fg_color=COLOR_PRIMARY, hover_color=COLOR_PRIMARY_HOVER,
            text_color="#FFFFFF",
            command=self._run_validator
        )
        self.btn_run.pack(side="left", padx=(0, 10))

        self.btn_open_folder = ctk.CTkButton(
            self.buttons_card, text="打开结果文件夹",
            font=APP_FONT, height=45,
            fg_color=COLOR_SUCCESS, hover_color=COLOR_SUCCESS,
            text_color="#FFFFFF",
            command=self._open_result_folder,
            state="disabled"
        )
        self.btn_open_folder.pack(side="left", padx=(0, 10))

        self.btn_template = ctk.CTkButton(
            self.buttons_card, text="下载模板",
            font=APP_FONT, height=45,
            fg_color=COLOR_TEXT_MUTED, hover_color=COLOR_BORDER,
            text_color="#FFFFFF",
            command=self._download_template
        )
        self.btn_template.pack(side="left", padx=(0, 10))

        self.btn_clear = ctk.CTkButton(
            self.buttons_card, text="清空",
            font=APP_FONT, height=45,
            fg_color=COLOR_TEXT_MUTED, hover_color=COLOR_BORDER,
            text_color="#FFFFFF",
            command=self._clear_input
        )
        self.btn_clear.pack(side="left")

        self.result_path = None

        self.log_card = ctk.CTkFrame(self, fg_color=COLOR_BG_CARD, corner_radius=12)
        self.log_card.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        self.log_label = ctk.CTkLabel(
            self.log_card, text="执行日志",
            font=APP_FONT_BOLD, text_color=COLOR_TEXT_PRIMARY
        )
        self.log_label.pack(anchor="w", padx=15, pady=(10, 5))

        self.log_viewer = LogViewer(self.log_card, height=200)
        self.log_viewer.pack(fill="both", expand=True, padx=10, pady=(0, 10))

    def _upload_dict(self):
        file_path = filedialog.askopenfilename(
            title="选择标签字典文件",
            filetypes=[("字典文件", "*.csv *.txt *.xlsx *.xls"), ("所有文件", "*.*")]
        )
        if file_path:
            self.dict_var.set(file_path)
            from tools.label_validator import load_label_dict
            labels, error = load_label_dict(file_path)
            if error:
                self.dict_preview.configure(text=f"加载失败: {error}", text_color="#EF4444")
            else:
                self.dict_preview.configure(
                    text=f"已加载 {len(labels)} 个有效标签",
                    text_color=COLOR_SUCCESS
                )

    def _show_format_help(self):
        help_text = (
            "支持的字典文件格式：CSV / TXT / XLSX / XLS\n\n"
            "【CSV 格式示例】\n"
            "第一列列名必须为 'label'\n"
            "label\n"
            "0101\n"
            "0201\n"
            "0301\n"
            "TTQ\n\n"
            "【TXT 格式示例】\n"
            "每行一个标签值\n"
            "0101\n"
            "0201\n"
            "0301\n"
            "TTQ\n\n"
            "【XLSX/XLS 格式示例】\n"
            "第一列列名必须为 'label'，后续行填写标签值"
        )
        
        help_window = create_modal_window(self, "字典文件格式说明", 620, 540)
        create_modal_header(help_window, "字典文件格式说明", "支持 CSV、TXT、XLSX、XLS。请按下面示例准备第一列或每行的标签值。")
        
        textbox = ctk.CTkTextbox(
            help_window,
            font=APP_FONT,
            text_color=COLOR_TEXT_PRIMARY,
            fg_color=COLOR_BG_INPUT,
            border_width=1,
            border_color=COLOR_BORDER,
        )
        textbox.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        textbox.insert("1.0", help_text)
        textbox.configure(state="disabled")

    def _download_template(self):
        folder = filedialog.askdirectory(title="选择模板保存位置")
        if not folder:
            return
        
        try:
            template_path = export_template(folder, 'csv')
            self.log_viewer.append(f"模板已保存: {template_path}")
        except Exception as e:
            self.log_viewer.append(f"导出模板失败: {str(e)}")

    def _run_validator(self):
        target_dir = self.folder_selector.get()
        if not target_dir:
            self.log_viewer.append("请选择源文件夹")
            return
        
        dict_path = self.dict_var.get().strip()
        if not dict_path:
            self.log_viewer.append("请上传标签字典文件")
            return
        
        if not os.path.exists(dict_path):
            self.log_viewer.append("字典文件不存在")
            return
        
        self.btn_run.configure(state="disabled", text="检查中...")
        self.result_path = None
        self.btn_open_folder.configure(state="disabled")
        self.log_viewer.clear()
        self.log_viewer.append(f"开始检查文件夹: {target_dir}")
        self.log_viewer.append(f"使用字典: {dict_path}")
        
        start_time = time.time()
        
        def run_task():
            try:
                output_path, error, stats = run_validator(target_dir, dict_path)
            except Exception as exc:
                output_path, error, stats = None, f"执行检查失败: {str(exc)}", {}
            elapsed = time.time() - start_time
            self.after(0, lambda: self._on_complete(output_path, error, stats, elapsed))
        
        thread = threading.Thread(target=run_task, daemon=True)
        thread.start()

    def _on_complete(self, output_path, error, stats, elapsed):
        self.btn_run.configure(state="normal", text="开始检查")
        
        if error:
            self.log_viewer.append(f"错误: {error}")
            return
        
        self.result_path = output_path
        self.log_viewer.append(f"检查完成! 用时: {elapsed:.2f}秒")
        self.log_viewer.append(f"总文件数: {stats['total_files']}")
        self.log_viewer.append(f"有效文件: {stats['valid_count']}")
        self.log_viewer.append(f"存在问题: {stats['error_count']}")
        if 'error_item_count' in stats:
            self.log_viewer.append(f"问题条目: {stats['error_item_count']}")
        self.log_viewer.append(f"报告已保存: {output_path}")
        self.btn_open_folder.configure(state="normal")

    def _clear_input(self):
        self.folder_selector.set("")
        self.dict_var.set("")
        self.dict_preview.configure(text="", text_color=COLOR_TEXT_MUTED)
        self.log_viewer.clear()
        self.result_path = None
        self.btn_open_folder.configure(state="disabled")

    def _open_result_folder(self):
        if self.result_path and os.path.exists(self.result_path):
            result_folder = os.path.dirname(self.result_path)
            import platform
            if platform.system() == "Windows":
                os.startfile(result_folder)
            else:
                import subprocess
                subprocess.run(["open", result_folder])


class PolygonOverlapPanel(ctk.CTkFrame):
    """多边形重叠检查工具面板"""

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)

        self.result_path = None
        self._create_ui()

    def _create_ui(self):
        self.title_label = ctk.CTkLabel(
            self, text="多边形重叠检查",
            font=APP_FONT_HEADER, text_color=COLOR_TEXT_PRIMARY
        )
        self.title_label.pack(anchor="w", pady=(20, 10), padx=20)

        self.desc_label = ctk.CTkLabel(
            self,
            text="检查 Labelme JSON 中 polygon 标注是否重叠，并导出问题文件副本",
            font=APP_FONT, text_color=COLOR_TEXT_SECONDARY
        )
        self.desc_label.pack(anchor="w", pady=(0, 20), padx=20)

        self.help_card = ToolHelpCard(self, lines=HELP_TEXTS["polygon_checker"])
        self.help_card.pack(fill="x", padx=20, pady=(0, 15))

        self.params_card = ctk.CTkFrame(self, fg_color=COLOR_BG_CARD, corner_radius=12)
        self.params_card.pack(fill="x", padx=20, pady=(0, 15))

        self.source_selector = PathSelector(
            self.params_card, label="源文件夹"
        )
        self.source_selector.pack(fill="x", padx=15, pady=(15, 10))

        self.output_frame = ctk.CTkFrame(self.params_card, fg_color="transparent")
        self.output_frame.pack(fill="x", padx=15, pady=(0, 10))

        self.output_label = ctk.CTkLabel(
            self.output_frame, text="输出目录", font=APP_FONT,
            text_color=COLOR_TEXT_SECONDARY
        )
        self.output_label.pack(side="left", padx=(0, 10))

        self.output_var = ctk.StringVar()
        self.output_entry = ctk.CTkEntry(
            self.output_frame, textvariable=self.output_var, font=APP_FONT,
            placeholder_text="默认: 源文件夹/ERROR_CHECK_RESULTS",
            placeholder_text_color=COLOR_TEXT_MUTED,
            fg_color=COLOR_BG_INPUT, border_color=COLOR_BORDER
        )
        self.output_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))

        self.btn_default = ctk.CTkButton(
            self.output_frame, text="默认", font=APP_FONT,
            width=60, fg_color=COLOR_TEXT_MUTED, hover_color=COLOR_BORDER,
            text_color="#FFFFFF",
            command=self._set_default_output
        )
        self.btn_default.pack(side="left", padx=(0, 10))

        self.btn_browse_output = ctk.CTkButton(
            self.output_frame, text="浏览", font=APP_FONT,
            width=80, fg_color=COLOR_PRIMARY, hover_color=COLOR_PRIMARY_HOVER,
            text_color="#FFFFFF",
            command=self._browse_output
        )
        self.btn_browse_output.pack(side="left")

        self.threshold_frame = ctk.CTkFrame(self.params_card, fg_color="transparent")
        self.threshold_frame.pack(fill="x", padx=15, pady=(0, 10))

        self.threshold_label = ctk.CTkLabel(
            self.threshold_frame, text="重叠面积阈值", font=APP_FONT,
            text_color=COLOR_TEXT_SECONDARY
        )
        self.threshold_label.pack(side="left", padx=(0, 10))

        self.threshold_var = ctk.StringVar(value="0.1")
        self.threshold_entry = ctk.CTkEntry(
            self.threshold_frame, textvariable=self.threshold_var, font=APP_FONT,
            width=100,
            fg_color=COLOR_BG_INPUT, border_color=COLOR_BORDER
        )
        self.threshold_entry.pack(side="left", padx=(0, 10))

        self.threshold_hint = ctk.CTkLabel(
            self.threshold_frame,
            text="说明：当两个 polygon 的交集面积大于该值时，判定为重叠。默认 0.1。",
            font=APP_FONT_SMALL, text_color=COLOR_TEXT_MUTED
        )
        self.threshold_hint.pack(side="left")

        self.info_label = ctk.CTkLabel(
            self.params_card,
            text="仅检查 polygon；问题标签会改为 [重叠] 原标签；不修改原始文件",
            font=APP_FONT_SMALL, text_color=COLOR_TEXT_MUTED
        )
        self.info_label.pack(anchor="w", padx=15, pady=(0, 15))

        self.buttons_card = ctk.CTkFrame(self, fg_color="transparent")
        self.buttons_card.pack(fill="x", padx=20, pady=(0, 15))

        self.btn_run = ctk.CTkButton(
            self.buttons_card, text="开始检查",
            font=APP_FONT_BOLD, height=45,
            fg_color=COLOR_PRIMARY, hover_color=COLOR_PRIMARY_HOVER,
            text_color="#FFFFFF",
            command=self._run_checker
        )
        self.btn_run.pack(side="left", padx=(0, 10))

        self.btn_open_folder = ctk.CTkButton(
            self.buttons_card, text="打开结果文件夹",
            font=APP_FONT, height=45,
            fg_color=COLOR_SUCCESS, hover_color=COLOR_SUCCESS,
            text_color="#FFFFFF",
            command=self._open_result_folder,
            state="disabled"
        )
        self.btn_open_folder.pack(side="left", padx=(0, 10))

        self.btn_clear = ctk.CTkButton(
            self.buttons_card, text="清空",
            font=APP_FONT, height=45,
            fg_color=COLOR_TEXT_MUTED, hover_color=COLOR_BORDER,
            text_color="#FFFFFF",
            command=self._clear_input
        )
        self.btn_clear.pack(side="left")

        self.log_card = ctk.CTkFrame(self, fg_color=COLOR_BG_CARD, corner_radius=12)
        self.log_card.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        self.log_label = ctk.CTkLabel(
            self.log_card, text="执行日志",
            font=APP_FONT_BOLD, text_color=COLOR_TEXT_PRIMARY
        )
        self.log_label.pack(anchor="w", padx=15, pady=(10, 5))

        self.log_viewer = LogViewer(self.log_card, height=200)
        self.log_viewer.pack(fill="both", expand=True, padx=10, pady=(0, 10))

    def _get_default_output_dir(self, source_dir: str) -> str:
        return os.path.join(source_dir, "ERROR_CHECK_RESULTS")

    def _set_default_output(self):
        source_dir = self.source_selector.get().strip()
        if not source_dir:
            self.log_viewer.append("请先选择源文件夹")
            return

        self.output_var.set(self._get_default_output_dir(source_dir))

    def _browse_output(self):
        folder = filedialog.askdirectory(title="选择输出目录")
        if folder:
            self.output_var.set(folder)

    def _run_checker(self):
        source_dir = self.source_selector.get().strip()
        if not source_dir:
            self.log_viewer.append("请选择源文件夹")
            return

        try:
            threshold = float(self.threshold_var.get().strip())
            if threshold < 0:
                self.log_viewer.append("重叠面积阈值不能小于 0")
                return
        except ValueError:
            self.log_viewer.append("重叠面积阈值必须是有效数字")
            return

        output_dir = self.output_var.get().strip()
        if not output_dir:
            output_dir = self._get_default_output_dir(source_dir)
            self.output_var.set(output_dir)

        self.btn_run.configure(state="disabled", text="检查中...")
        self.btn_open_folder.configure(state="disabled")
        self.result_path = None
        self.log_viewer.clear()
        self.log_viewer.append(f"开始检查文件夹: {source_dir}")
        self.log_viewer.append(f"输出目录: {output_dir}")
        self.log_viewer.append(f"重叠面积阈值: {threshold}")

        start_time = time.time()

        def run_task():
            try:
                result_path, error, stats = run_polygon_overlap_check(source_dir, threshold, output_dir)
            except Exception as exc:
                result_path, error, stats = None, f"执行检查失败: {str(exc)}", {}
            elapsed = time.time() - start_time
            self.after(0, lambda: self._on_complete(result_path, error, stats, elapsed))

        thread = threading.Thread(target=run_task, daemon=True)
        thread.start()

    def _on_complete(self, result_path, error, stats, elapsed):
        self.btn_run.configure(state="normal", text="开始检查")

        if error:
            self.log_viewer.append(f"错误: {error}")
            return

        self.result_path = result_path
        self.log_viewer.append(f"检查完成! 用时: {elapsed:.2f}秒")
        self.log_viewer.append(f"JSON 总数: {stats['total_files']}")
        self.log_viewer.append(f"实际检查: {stats['checked_files']}")
        self.log_viewer.append(f"读取跳过: {stats['skipped_files']}")
        self.log_viewer.append(f"问题文件: {stats['error_files']}")
        self.log_viewer.append(f"问题 shape 总数: {stats['total_overlap_shapes']}")
        self.log_viewer.append(f"重叠 pair 总数: {stats['total_overlap_pairs']}")
        self.log_viewer.append(f"结果目录: {result_path}")
        if stats.get("report_path"):
            self.log_viewer.append(f"检查报告: {stats['report_path']}")

        if stats["details"]:
            self.log_viewer.append("--- 问题文件详情（最多显示 10 条）---")
            shown_count = 0
            for detail in stats["details"]:
                if detail["overlap_shape_count"] <= 0:
                    continue
                shown_count += 1
                self.log_viewer.append(
                    f"[{shown_count}] {detail['file']} | shape {detail['overlap_shape_count']} 个 | pair {detail['overlap_pair_count']} 组"
                )
                if detail.get("overlap_pairs_text"):
                    self.log_viewer.append(f"    重叠情况: {detail['overlap_pairs_text']}")
                if detail["warning"]:
                    self.log_viewer.append(f"    提示: {detail['warning']}")
                if shown_count >= 10:
                    break

            unread_count = max(stats["error_files"] - shown_count, 0)
            if unread_count > 0:
                self.log_viewer.append(f"... 还有 {unread_count} 个问题文件")

        warning_details = [detail for detail in stats["details"] if detail["warning"] and detail["overlap_shape_count"] == 0]
        if warning_details:
            self.log_viewer.append("--- 跳过文件提示（最多显示 5 条）---")
            for index, detail in enumerate(warning_details[:5], 1):
                self.log_viewer.append(f"[{index}] {detail['file']} | {detail['warning']}")

        self.btn_open_folder.configure(state="normal")

    def _clear_input(self):
        self.source_selector.set("")
        self.output_var.set("")
        self.threshold_var.set("0.1")
        self.result_path = None
        self.log_viewer.clear()
        self.btn_open_folder.configure(state="disabled")

    def _open_result_folder(self):
        if self.result_path and os.path.exists(self.result_path):
            import platform
            if platform.system() == "Windows":
                os.startfile(self.result_path)
            else:
                import subprocess
                subprocess.run(["open", self.result_path])


class SamplerPanel(ctk.CTkFrame):
    """检查抽样工具面板"""

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)

        self._create_ui()

    def _create_ui(self):
        self.title_label = ctk.CTkLabel(
            self, text="检查抽样",
            font=APP_FONT_HEADER, text_color=COLOR_TEXT_PRIMARY
        )
        self.title_label.pack(anchor="w", pady=(20, 10), padx=20)

        self.desc_label = ctk.CTkLabel(
            self,
            text="从数据集中均匀抽取样本用于质量检查",
            font=APP_FONT, text_color=COLOR_TEXT_SECONDARY
        )
        self.desc_label.pack(anchor="w", pady=(0, 20), padx=20)

        self.help_card = ToolHelpCard(self, lines=HELP_TEXTS["sampler"])
        self.help_card.pack(fill="x", padx=20, pady=(0, 15))

        self.params_card = ctk.CTkFrame(self, fg_color=COLOR_BG_CARD, corner_radius=12)
        self.params_card.pack(fill="x", padx=20, pady=(0, 15))

        self.source_selector = PathSelector(
            self.params_card, label="源文件夹"
        )
        self.source_selector.pack(fill="x", padx=15, pady=(15, 10))

        self.output_frame = ctk.CTkFrame(self.params_card, fg_color="transparent")
        self.output_frame.pack(fill="x", padx=15, pady=(0, 10))

        self.output_label = ctk.CTkLabel(
            self.output_frame, text="输出目录", font=APP_FONT,
            text_color=COLOR_TEXT_SECONDARY
        )
        self.output_label.pack(side="left", padx=(0, 10))

        self.output_var = ctk.StringVar()
        self.output_entry = ctk.CTkEntry(
            self.output_frame, textvariable=self.output_var, font=APP_FONT,
            placeholder_text="默认: 源文件夹/抽样结果xxx",
            placeholder_text_color=COLOR_TEXT_MUTED,
            fg_color=COLOR_BG_INPUT, border_color=COLOR_BORDER
        )
        self.output_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))

        self.btn_default = ctk.CTkButton(
            self.output_frame, text="默认", font=APP_FONT,
            width=60, fg_color=COLOR_TEXT_MUTED, hover_color=COLOR_BORDER,
            text_color="#FFFFFF",
            command=self._set_default_output
        )
        self.btn_default.pack(side="left", padx=(0, 10))

        self.btn_browse_output = ctk.CTkButton(
            self.output_frame, text="浏览", font=APP_FONT,
            width=80, fg_color=COLOR_PRIMARY, hover_color=COLOR_PRIMARY_HOVER,
            text_color="#FFFFFF",
            command=self._browse_output
        )
        self.btn_browse_output.pack(side="left")

        self.count_frame = ctk.CTkFrame(self.params_card, fg_color="transparent")
        self.count_frame.pack(fill="x", padx=15, pady=(0, 15))

        self.count_label = ctk.CTkLabel(
            self.count_frame, text="抽样数量", font=APP_FONT,
            text_color=COLOR_TEXT_SECONDARY
        )
        self.count_label.pack(side="left", padx=(0, 10))

        self.count_var = ctk.StringVar(value="50")
        self.count_entry = ctk.CTkEntry(
            self.count_frame, textvariable=self.count_var, font=APP_FONT,
            width=100,
            fg_color=COLOR_BG_INPUT, border_color=COLOR_BORDER
        )
        self.count_entry.pack(side="left", padx=(0, 5))

        self.count_unit = ctk.CTkLabel(
            self.count_frame, text="张", font=APP_FONT,
            text_color=COLOR_TEXT_MUTED
        )
        self.count_unit.pack(side="left")

        self.buttons_card = ctk.CTkFrame(self, fg_color="transparent")
        self.buttons_card.pack(fill="x", padx=20, pady=(0, 15))

        self.btn_run = ctk.CTkButton(
            self.buttons_card, text="开始抽样",
            font=APP_FONT_BOLD, height=45,
            fg_color=COLOR_PRIMARY, hover_color=COLOR_PRIMARY_HOVER,
            text_color="#FFFFFF",
            command=self._run_sampler
        )
        self.btn_run.pack(side="left", padx=(0, 10))

        self.btn_open_folder = ctk.CTkButton(
            self.buttons_card, text="打开结果文件夹",
            font=APP_FONT, height=45,
            fg_color=COLOR_SUCCESS, hover_color=COLOR_SUCCESS,
            text_color="#FFFFFF",
            command=self._open_result_folder,
            state="disabled"
        )
        self.btn_open_folder.pack(side="left", padx=(0, 10))

        self.btn_clear = ctk.CTkButton(
            self.buttons_card, text="清空",
            font=APP_FONT, height=45,
            fg_color=COLOR_TEXT_MUTED, hover_color=COLOR_BORDER,
            text_color="#FFFFFF",
            command=self._clear_input
        )
        self.btn_clear.pack(side="left")

        self.result_path = None

        self.log_card = ctk.CTkFrame(self, fg_color=COLOR_BG_CARD, corner_radius=12)
        self.log_card.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        self.log_label = ctk.CTkLabel(
            self.log_card, text="执行日志",
            font=APP_FONT_BOLD, text_color=COLOR_TEXT_PRIMARY
        )
        self.log_label.pack(anchor="w", padx=15, pady=(10, 5))

        self.log_viewer = LogViewer(self.log_card, height=200)
        self.log_viewer.pack(fill="both", expand=True, padx=10, pady=(0, 10))

    def _set_default_output(self):
        source_dir = self.source_selector.get()
        if not source_dir:
            self.log_viewer.append("请先选择源文件夹")
            return
        default_dir = get_default_output_dir(source_dir)
        self.output_var.set(default_dir)

    def _browse_output(self):
        folder = filedialog.askdirectory(title="选择输出目录")
        if folder:
            self.output_var.set(folder)

    def _run_sampler(self):
        source_dir = self.source_selector.get()
        if not source_dir:
            self.log_viewer.append("请选择源文件夹")
            return

        output_dir = self.output_var.get().strip()
        if not output_dir:
            output_dir = get_default_output_dir(source_dir)
            self.output_var.set(output_dir)

        try:
            sample_count = int(self.count_var.get())
            if sample_count <= 0:
                self.log_viewer.append("抽样数量必须大于0")
                return
        except ValueError:
            self.log_viewer.append("抽样数量必须是有效数字")
            return

        self.btn_run.configure(state="disabled", text="抽样中...")
        self.result_path = None
        self.btn_open_folder.configure(state="disabled")
        self.log_viewer.clear()
        self.log_viewer.append(f"开始扫描文件夹: {source_dir}")
        self.log_viewer.append(f"输出目录: {output_dir}")
        self.log_viewer.append(f"抽样数量: {sample_count} 张")

        start_time = time.time()

        def run_task():
            try:
                output_path, error, stats = run_sampler(source_dir, output_dir, sample_count)
            except Exception as exc:
                output_path, error, stats = None, f"执行抽样失败: {str(exc)}", {}
            elapsed = time.time() - start_time
            self.after(0, lambda: self._on_sampler_complete(output_path, error, stats, elapsed))

        thread = threading.Thread(target=run_task, daemon=True)
        thread.start()

    def _on_sampler_complete(self, output_path, error, stats, elapsed):
        self.btn_run.configure(state="normal", text="开始抽样")

        if error:
            self.log_viewer.append(f"错误: {error}")
            return

        self.result_path = output_path
        self.log_viewer.append(f"抽样完成! 用时: {elapsed:.2f}秒")
        self.log_viewer.append(f"共找到可用样本: {stats['total_found']} 组")
        self.log_viewer.append(f"实际抽样数量: {stats['sampled']} 张")
        self.log_viewer.append(f"标签(Shapes)总数: {stats['labels']}")
        self.log_viewer.append(f"结果保存至: {output_path}")
        self.btn_open_folder.configure(state="normal")

    def _clear_input(self):
        self.source_selector.set("")
        self.output_var.set("")
        self.count_var.set("50")
        self.log_viewer.clear()
        self.result_path = None
        self.btn_open_folder.configure(state="disabled")

    def _open_result_folder(self):
        if self.result_path and os.path.exists(self.result_path):
            import platform
            if platform.system() == "Windows":
                os.startfile(self.result_path)
            else:
                import subprocess
                subprocess.run(["open", self.result_path])


class ImageCountPanel(ctk.CTkFrame):
    """图像计数工具面板"""
    
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        
        self._create_ui()
    
    def _create_ui(self):
        self.title_label = ctk.CTkLabel(
            self, text="文件计数与匹配统计",
            font=APP_FONT_HEADER, text_color=COLOR_TEXT_PRIMARY
        )
        self.title_label.pack(anchor="w", pady=(20, 10), padx=20)
        
        self.desc_label = ctk.CTkLabel(
            self,
            text="统计指定目录下所有子文件夹中的图片文件与 JSON 文件的配对情况",
            font=APP_FONT, text_color=COLOR_TEXT_SECONDARY
        )
        self.desc_label.pack(anchor="w", pady=(0, 20), padx=20)

        self.help_card = ToolHelpCard(self, lines=HELP_TEXTS["image_count"])
        self.help_card.pack(fill="x", padx=20, pady=(0, 15))

        self.params_card = ctk.CTkFrame(self, fg_color=COLOR_BG_CARD, corner_radius=12)
        self.params_card.pack(fill="x", padx=20, pady=(0, 15))
        
        self.path_selector = PathSelector(
            self.params_card, label="扫描文件夹"
        )
        self.path_selector.pack(fill="x", padx=15, pady=(15, 15))
        
        self.info_label = ctk.CTkLabel(
            self.params_card,
            text="自动识别: jpg, jpeg, png, tif, tiff",
            font=APP_FONT_SMALL, text_color=COLOR_TEXT_MUTED
        )
        self.info_label.pack(anchor="w", padx=15, pady=(5, 15))
        
        self.buttons_card = ctk.CTkFrame(self, fg_color="transparent")
        self.buttons_card.pack(fill="x", padx=20, pady=(0, 15))
        
        self.btn_run = ctk.CTkButton(
            self.buttons_card, text="开始扫描",
            font=APP_FONT_BOLD, height=45,
            fg_color=COLOR_PRIMARY, hover_color=COLOR_PRIMARY_HOVER,
            text_color="#FFFFFF",
            command=self._run_scan
        )
        self.btn_run.pack(side="left", padx=(0, 10))
        
        self.btn_open_folder = ctk.CTkButton(
            self.buttons_card, text="打开结果文件夹",
            font=APP_FONT, height=45,
            fg_color=COLOR_SUCCESS, hover_color=COLOR_SUCCESS,
            text_color="#FFFFFF",
            command=self._open_result_folder,
            state="disabled"
        )
        self.btn_open_folder.pack(side="left", padx=(0, 10))
        
        self.btn_clear = ctk.CTkButton(
            self.buttons_card, text="清空",
            font=APP_FONT, height=45,
            fg_color=COLOR_TEXT_MUTED, hover_color=COLOR_BORDER,
            text_color="#FFFFFF",
            command=self._clear_input
        )
        self.btn_clear.pack(side="left")
        
        self.result_path = None
        
        self.log_card = ctk.CTkFrame(self, fg_color=COLOR_BG_CARD, corner_radius=12)
        self.log_card.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        self.log_label = ctk.CTkLabel(
            self.log_card, text="执行日志",
            font=APP_FONT_BOLD, text_color=COLOR_TEXT_PRIMARY
        )
        self.log_label.pack(anchor="w", padx=15, pady=(10, 5))
        
        self.log_viewer = LogViewer(self.log_card, height=200)
        self.log_viewer.pack(fill="both", expand=True, padx=10, pady=(0, 10))
    
    def _run_scan(self):
        folder = self.path_selector.get()
        if not folder:
            self.log_viewer.append("请先选择要扫描的文件夹")
            return
        
        self.btn_run.configure(state="disabled", text="扫描中...")
        self.result_path = None
        self.btn_open_folder.configure(state="disabled")
        self.log_viewer.clear()
        self.log_viewer.append(f"开始扫描文件夹: {folder}")
        self.log_viewer.append("自动识别: jpg, jpeg, png, tif, tiff")
        
        start_time = time.time()
        
        def run_task():
            try:
                output_path, error, stats = run_count(folder)
            except Exception as exc:
                output_path, error, stats = None, f"执行扫描失败: {str(exc)}", {}
            elapsed = time.time() - start_time
            self.after(0, lambda: self._on_scan_complete(output_path, error, stats, elapsed))
        
        thread = threading.Thread(target=run_task, daemon=True)
        thread.start()
    
    def _on_scan_complete(self, output_path, error, stats, elapsed):
        self.btn_run.configure(state="normal", text="开始扫描")
        
        if error:
            self.log_viewer.append(f"错误: {error}")
            return
        
        self.result_path = output_path
        self.log_viewer.append(f"扫描完成! 用时: {elapsed:.2f}秒")
        self.log_viewer.append(f"总共扫描文件夹数: {stats['total_folders']}")
        
        imgs = stats['total_images']
        img_details = ", ".join([f"{ext.replace('.', '')} {cnt}个" for ext, cnt in imgs.items() if cnt > 0])
        total_imgs = sum(imgs.values())
        self.log_viewer.append(f"总共照片数: {img_details}，共 {total_imgs}个")
        
        self.log_viewer.append(f"总共json文件数: {stats['total_json']}")
        self.log_viewer.append(f"总匹配成功数: {stats['total_matched']}")
        self.log_viewer.append(f"结果已保存到: {output_path}")
        self.btn_open_folder.configure(state="normal")
    
    def _clear_input(self):
        self.path_selector.set("")
        self.log_viewer.clear()
        self.result_path = None
        self.btn_open_folder.configure(state="disabled")
    
    def _open_result_folder(self):
        if self.result_path and os.path.exists(self.result_path):
            result_folder = os.path.dirname(self.result_path)
            import platform
            if platform.system() == "Windows":
                os.startfile(result_folder)
            else:
                import subprocess
                subprocess.run(["open", result_folder])


class PathSelector(ctk.CTkFrame):
    """路径选择组件"""
    
    def __init__(self, master, label: str = "选择文件夹", **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        
        self.label = ctk.CTkLabel(
            self, text=label, font=APP_FONT,
            text_color=COLOR_TEXT_SECONDARY
        )
        self.label.pack(side="left", padx=(0, 10))
        
        self.path_var = ctk.StringVar()
        
        self.entry = ctk.CTkEntry(
            self, textvariable=self.path_var, font=APP_FONT,
            placeholder_text_color=COLOR_TEXT_MUTED,
            fg_color=COLOR_BG_INPUT, border_color=COLOR_BORDER
        )
        self.entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        self.btn_browse = ctk.CTkButton(
            self, text="浏览", font=APP_FONT,
            width=80, fg_color=COLOR_PRIMARY, hover_color=COLOR_PRIMARY_HOVER,
            command=self._browse
        )
        self.btn_browse.pack(side="left")
    
    def _browse(self):
        folder = filedialog.askdirectory(title="选择文件夹")
        if folder:
            self.path_var.set(folder)
    
    def get(self) -> str:
        return self.path_var.get()
    
    def set(self, value: str):
        self.path_var.set(value)


class LogViewer(ctk.CTkTextbox):
    """日志查看器组件"""
    
    def __init__(self, master, **kwargs):
        super().__init__(
            master, font=APP_FONT_SMALL,
            text_color=COLOR_TEXT_SECONDARY,
            fg_color=COLOR_BG_INPUT,
            **kwargs
        )
        self.configure(state="disabled")
    
    def append(self, message: str):
        self.configure(state="normal")
        self.insert("end", message + "\n")
        self.see("end")
        self.configure(state="disabled")
    
    def clear(self):
        self.configure(state="normal")
        self.delete("1.0", "end")
        self.configure(state="disabled")


class MainWindow(ctk.CTk):
    """主窗口"""
    
    def __init__(self):
        super().__init__()
        
        self.title("Labelme 工具箱")
        self.geometry("1000x700")
        self.minsize(900, 600)
        self._window_icon = None
        self._setup_window_icon()
        
        self._setup_ui()

    def _setup_window_icon(self):
        """设置窗口图标，优先加载 Windows ICO，并保留 PNG 作为回退。"""
        ico_path = get_asset_path("app_icon.ico")
        png_path = get_asset_path("app_icon.png")

        try:
            if ico_path.exists():
                self.iconbitmap(default=str(ico_path))
        except Exception:
            pass

        try:
            if png_path.exists():
                self._window_icon = PhotoImage(file=str(png_path))
                self.iconphoto(True, self._window_icon)
        except Exception:
            pass
    
    def _setup_ui(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        self._create_sidebar()
        self._create_main_area()
    
    def _create_sidebar(self):
        self.sidebar = ctk.CTkFrame(
            self, width=220, corner_radius=0,
            fg_color=COLOR_BG_SIDEBAR
        )
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        
        self.logo_label = ctk.CTkLabel(
            self.sidebar, text="Labelme 工具箱",
            font=APP_FONT_HEADER, text_color=COLOR_PRIMARY
        )
        self.logo_label.pack(anchor="w", padx=20, pady=(20, 8))
        self.logo_label.bind("<Button-1>", self._on_logo_clicked)
        
        self.separator = ctk.CTkFrame(self.sidebar, height=2, fg_color=COLOR_BORDER)
        self.separator.pack(fill="x", padx=15, pady=(0, 10))
        
        self.tool_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.tool_frame.pack(fill="both", expand=True, pady=10)

        self.about_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.about_frame.pack(fill="x", padx=0, pady=(0, 12), side="bottom")
        
        self.tool_buttons = []
        self.tool_button_map = {}
        tools = [
            ("文件计数与匹配统计", "image_counter"),
            ("孤立文件清理", "orphan_cleaner"),
            ("标签正确性检查", "label_validator"),
            ("多边形重叠检查", "polygon_checker"),
            ("检查抽样", "sampler"),
        ]
        
        for i, (text, tool_id) in enumerate(tools):
            btn = ctk.CTkButton(
                self.tool_frame, text=text,
                font=APP_FONT, height=45,
                fg_color="transparent",
                text_color=COLOR_TEXT_PRIMARY,
                hover_color=COLOR_SIDEBAR_SELECTED,
                anchor="w",
                border_width=0,
                command=lambda t=tool_id: self._on_tool_selected(t)
            )
            btn.pack(fill="x", padx=10, pady=3)
            self.tool_buttons.append(btn)
            self.tool_button_map[tool_id] = btn

        self.about_button = ctk.CTkButton(
            self.about_frame,
            text="关于",
            font=APP_FONT,
            height=45,
            fg_color="transparent",
            text_color=COLOR_TEXT_PRIMARY,
            hover_color=COLOR_SIDEBAR_SELECTED,
            anchor="w",
            border_width=0,
            command=lambda: self._on_tool_selected("about"),
        )
        self.about_button.pack(fill="x", padx=10, pady=3)
        self.tool_buttons.append(self.about_button)
        self.tool_button_map["about"] = self.about_button
    
    def _create_main_area(self):
        self.main_area = ctk.CTkFrame(self, fg_color=COLOR_BG_MAIN)
        self.main_area.grid(row=0, column=1, sticky="nsew", padx=0, pady=0)
        
        self.tool_panels = {}
        self.current_panel = None
        
        self._show_welcome()
    
    def _show_welcome(self):
        self._clear_main_area()
        self._set_active_tool_button("about")
        self.current_panel = None
        
        self.home_frame = ctk.CTkFrame(self.main_area, fg_color="transparent")
        self.home_frame.pack(fill="both", expand=True, padx=36, pady=32)

        self.content_label = ctk.CTkLabel(
            self.home_frame, text="欢迎使用 Labelme 工具箱",
            font=APP_FONT_HEADER, text_color=COLOR_TEXT_PRIMARY
        )
        self.content_label.pack(anchor="w", pady=(8, 12))
        
        self.welcome_text = ctk.CTkLabel(
            self.home_frame,
            text="一个面向 Labelme 标注数据处理的桌面工具集，覆盖统计、清理、校验、重叠检查与抽样五类常用任务。",
            font=APP_FONT, text_color=COLOR_TEXT_SECONDARY
        )
        self.welcome_text.pack(anchor="w")

        self.intro_card = ctk.CTkFrame(
            self.home_frame,
            fg_color=COLOR_BG_CARD,
            corner_radius=14,
            border_width=1,
            border_color=COLOR_BORDER,
        )
        self.intro_card.pack(fill="x", pady=(24, 18))

        self.intro_title = ctk.CTkLabel(
            self.intro_card,
            text="工具集简介",
            font=APP_FONT_BOLD,
            text_color=COLOR_TEXT_PRIMARY,
        )
        self.intro_title.pack(anchor="w", padx=20, pady=(18, 10))

        intro_lines = [
            "文件计数与匹配统计：按叶子文件夹汇总图片与 JSON 配对情况，并导出结果。",
            "孤立文件清理与标签检查：辅助发现孤立文件、异常标签，降低人工排查成本。",
            "多边形重叠检查与抽样：定位重叠标注问题，并快速抽取样本进行人工复核。",
        ]

        for line in intro_lines:
            item_label = ctk.CTkLabel(
                self.intro_card,
                text=f"• {line}",
                font=APP_FONT,
                text_color=COLOR_TEXT_SECONDARY,
                justify="left",
                anchor="w",
            )
            item_label.pack(fill="x", padx=20, pady=4)

        self.copyright_label = ctk.CTkLabel(
            self.home_frame,
            text="Copyright © Shuyang Gu",
            font=APP_FONT_SMALL,
            text_color=COLOR_TEXT_MUTED,
        )
        self.copyright_label.pack(anchor="w", pady=(6, 0))
    
    def _clear_main_area(self):
        for widget in self.main_area.winfo_children():
            widget.pack_forget()
    
    def _show_panel(self, panel_class):
        self._clear_main_area()
        
        if panel_class.__name__ not in self.tool_panels:
            panel = panel_class(self.main_area)
            panel.pack(fill="both", expand=True)
            self.tool_panels[panel_class.__name__] = panel
        else:
            self.tool_panels[panel_class.__name__].pack(fill="both", expand=True)
        
        self.current_panel = panel_class.__name__

    def _reset_tool_button_state(self):
        for btn in self.tool_buttons:
            btn.configure(fg_color="transparent", text_color=COLOR_TEXT_PRIMARY)

    def _set_active_tool_button(self, tool_id: str):
        self._reset_tool_button_state()
        active_button = self.tool_button_map.get(tool_id)
        if active_button is not None:
            active_button.configure(
                fg_color=COLOR_SIDEBAR_SELECTED,
                text_color=COLOR_PRIMARY,
            )

    def _on_logo_clicked(self, _event=None):
        self._show_welcome()

    def _on_tool_selected(self, tool_id: str):
        """工具选择回调"""
        if tool_id == "about":
            self._show_welcome()
            return

        self._set_active_tool_button(tool_id)
        if tool_id == "image_counter":
            self._show_panel(ImageCountPanel)
        elif tool_id == "orphan_cleaner":
            self._show_panel(OrphanCleanerPanel)
        elif tool_id == "label_validator":
            self._show_panel(LabelValidatorPanel)
        elif tool_id == "polygon_checker":
            self._show_panel(PolygonOverlapPanel)
        elif tool_id == "sampler":
            self._show_panel(SamplerPanel)
    
    def _show_placeholder(self, tool_name: str):
        self._clear_main_area()
        
        self.content_label = ctk.CTkLabel(
            self.main_area, text=tool_name,
            font=APP_FONT_HEADER, text_color=COLOR_TEXT_PRIMARY
        )
        self.content_label.pack(pady=(40, 20))
        
        self.welcome_text = ctk.CTkLabel(
            self.main_area,
            text="该工具正在开发中...",
            font=APP_FONT, text_color=COLOR_TEXT_SECONDARY
        )
        self.welcome_text.pack()
