"""
孤立JPG/JSON文件清理工具

功能说明：
- 扫描选定目录及其子目录中的所有文件
- 支持两种清理模式：删除孤立JPG或删除孤立JSON
- 自动清理处理过程中产生的空文件夹
- 生成清理统计报告

使用场景：
- 数据集预处理和清洗
- 删除标注不完整的图片或缺失图片的标注
- 整理文件夹结构
"""

import os
import tkinter as tk
from tkinter import filedialog
from tkinter import ttk
from tkinter import font


def get_font(family='Microsoft YaHei UI', size=10, bold=False):
    available_fonts = tk.font.families()
    if family in available_fonts:
        return (family, size, 'bold' if bold else 'normal')
    fallback_fonts = ['Segoe UI', 'Arial', 'Helvetica', 'System']
    for fb in fallback_fonts:
        if fb in available_fonts:
            return (fb, size, 'bold' if bold else 'normal')
    return (None, size, 'bold' if bold else 'normal')


class OrphanImageCleaner:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("孤立JPG/JSON文件清理工具")
        self.root.geometry("520x480")
        self.root.minsize(520, 480)

        self.font_title = get_font(size=14, bold=True)
        self.font_header = get_font(size=11, bold=True)
        self.font_content = get_font(size=10)
        self.font_action = get_font(size=11)

        self.target_path = tk.StringVar()
        self.scan_result = {"paired": 0, "orphan_jpg": 0, "orphan_json": 0, "folder_count": 0, "depth": 0}
        self.clean_result = {"deleted": 0, "paired": 0}

        self.mode_var = tk.StringVar(value="jpg")
        self.valid_extensions = ('.jpg', '.jpeg', '.json')

        self._setup_style()
        self._create_widgets()

    def _setup_style(self):
        style = ttk.Style()
        style.theme_use('clam')

        style.configure('Title.TLabel', font=self.font_title, foreground='#2c3e50')
        style.configure('Header.TLabel', font=self.font_header, foreground='#34495e')
        style.configure('Content.TLabel', font=self.font_content, foreground='#57606f')

        style.configure('Custom.TRadiobutton', font=self.font_content, foreground='#2c3e50')
        style.map('Custom.TRadiobutton',
            foreground=[('active', '#3498db')],
            indicatorcolor=[('selected', '#3498db'), ('!selected', '#95a5a6')]
        )

        style.configure('Action.TButton', font=self.font_action, padding=(10, 5))
        style.map('Action.TButton',
            background=[('active', '#3498db'), ('!active', '#2980b9')],
            foreground=[('active', '#ffffff'), ('!active', '#ffffff')]
        )

        style.configure('Browse.TButton', font=self.font_content, padding=(8, 3))

        style.configure('Result.TFrame', background='#ecf0f1', relief='solid', borderwidth=1)
        style.configure('Result.TLabel', font=self.font_content, background='#ecf0f1', foreground='#2c3e50')

    def _create_widgets(self):
        self.root.configure(background='#ffffff')

        mode_frame = tk.Frame(self.root, background='#ffffff', pady=15)
        mode_frame.pack(fill="x", padx=25)

        ttk.Label(mode_frame, text="清理模式:", style='Title.TLabel').pack(side="left")

        rb1 = ttk.Radiobutton(
            mode_frame, text="删除孤立图片（无JSON的JPG）",
            variable=self.mode_var, value="jpg",
            style='Custom.TRadiobutton'
        )
        rb1.pack(side="left", padx=20)

        rb2 = ttk.Radiobutton(
            mode_frame, text="删除孤立JSON（无JPG的JSON）",
            variable=self.mode_var, value="json",
            style='Custom.TRadiobutton'
        )
        rb2.pack(side="left", padx=20)

        path_frame = tk.Frame(self.root, background='#ffffff', pady=5)
        path_frame.pack(fill="x", padx=25)

        ttk.Label(path_frame, text="选择文件夹:", style='Content.TLabel').pack(side="left")

        self.path_entry = tk.Entry(path_frame, textvariable=self.target_path, width=35, font=self.font_content)
        self.path_entry.pack(side="left", padx=8)

        ttk.Button(path_frame, text="浏览", command=self._browse_folder, style='Browse.TButton').pack(side="left")

        scan_btn = ttk.Button(self.root, text="开始扫描", command=self._scan_files, style='Action.TButton')
        scan_btn.pack(pady=10)

        scan_result_frame = ttk.Frame(self.root, style='Result.TFrame', padding=15)
        scan_result_frame.pack(fill="x", padx=25, pady=5)

        ttk.Label(scan_result_frame, text="扫描结果:", style='Header.TLabel').pack(anchor="w")

        self.scan_labels = ttk.Frame(scan_result_frame)
        self.scan_labels.pack(fill="x", pady=8)

        self.lbl_paired = ttk.Label(self.scan_labels, text="有效配对: 0 对", style='Result.TLabel')
        self.lbl_paired.grid(row=0, column=0, padx=20, sticky='w')

        self.lbl_orphan_jpg = ttk.Label(self.scan_labels, text="JPG孤立: 0 个", style='Result.TLabel')
        self.lbl_orphan_jpg.grid(row=0, column=1, padx=20, sticky='w')

        self.lbl_orphan_json = ttk.Label(self.scan_labels, text="JSON孤立: 0 个", style='Result.TLabel')
        self.lbl_orphan_json.grid(row=0, column=2, padx=20, sticky='w')

        self.scan_labels.columnconfigure(0, weight=1)
        self.scan_labels.columnconfigure(1, weight=1)
        self.scan_labels.columnconfigure(2, weight=1)

        self.folder_labels = ttk.Frame(scan_result_frame)
        self.folder_labels.pack(fill="x", pady=5)

        self.lbl_folder_count = ttk.Label(self.folder_labels, text="扫描文件夹: 0 个", style='Result.TLabel')
        self.lbl_folder_count.grid(row=0, column=0, padx=20, sticky='w')

        self.lbl_depth = ttk.Label(self.folder_labels, text="嵌套层数: 0 层", style='Result.TLabel')
        self.lbl_depth.grid(row=0, column=1, padx=20, sticky='w')

        self.folder_labels.columnconfigure(0, weight=1)
        self.folder_labels.columnconfigure(1, weight=1)

        clean_btn = ttk.Button(self.root, text="开始清理", command=self._clean_files, style='Action.TButton')
        clean_btn.pack(pady=10)

        clean_result_frame = ttk.Frame(self.root, style='Result.TFrame', padding=15)
        clean_result_frame.pack(fill="x", padx=25, pady=5)

        ttk.Label(clean_result_frame, text="清理结果:", style='Header.TLabel').pack(anchor="w")

        self.clean_labels = ttk.Frame(clean_result_frame)
        self.clean_labels.pack(fill="x", pady=8)

        self.lbl_deleted = ttk.Label(self.clean_labels, text="已清理: 0 个", style='Result.TLabel')
        self.lbl_deleted.grid(row=0, column=0, padx=20, sticky='w')

        self.lbl_paired_clean = ttk.Label(self.clean_labels, text="有效配对: 0 对", style='Result.TLabel')
        self.lbl_paired_clean.grid(row=0, column=1, padx=20, sticky='w')

        self.clean_labels.columnconfigure(0, weight=1)
        self.clean_labels.columnconfigure(1, weight=1)

    def _browse_folder(self):
        folder = filedialog.askdirectory(title="选择需要清理的文件夹")
        if folder:
            self.target_path.set(folder)
            self._reset_labels()

    def _reset_labels(self):
        self.lbl_paired.config(text="有效配对: 0 对")
        self.lbl_orphan_jpg.config(text="JPG孤立: 0 个")
        self.lbl_orphan_json.config(text="JSON孤立: 0 个")
        self.lbl_folder_count.config(text="扫描文件夹: 0 个")
        self.lbl_depth.config(text="嵌套层数: 0 层")
        self.lbl_deleted.config(text="已清理: 0 个")
        self.lbl_paired_clean.config(text="有效配对: 0 对")

    def _is_valid_file(self, filename):
        _, ext = os.path.splitext(filename)
        return ext.lower() in self.valid_extensions

    def _calculate_depth(self, target_path):
        max_depth = 0
        base_depth = target_path.rstrip(os.sep).count(os.sep)
        for root, dirs, files in os.walk(target_path):
            depth = root.count(os.sep) - base_depth
            max_depth = max(max_depth, depth)
        return max_depth

    def _scan_files(self):
        target_path = self.target_path.get()
        if not target_path:
            return

        jpg_names = set()
        json_names = set()

        folder_count = 0
        max_depth = 0
        base_depth = target_path.rstrip(os.sep).count(os.sep)

        for root_dir, dirs, files in os.walk(target_path):
            folder_count += 1
            current_depth = root_dir.count(os.sep) - base_depth
            max_depth = max(max_depth, current_depth)

            for file_name in files:
                if not self._is_valid_file(file_name):
                    continue

                name, ext = os.path.splitext(file_name)
                name_lower = name.lower()

                if ext.lower() in ('.jpg', '.jpeg'):
                    jpg_names.add(name_lower)
                elif ext.lower() == '.json':
                    json_names.add(name_lower)

        paired_names = jpg_names & json_names
        orphan_jpg = jpg_names - json_names
        orphan_json = json_names - jpg_names

        self.scan_result = {
            "paired": len(paired_names),
            "orphan_jpg": len(orphan_jpg),
            "orphan_json": len(orphan_json),
            "folder_count": folder_count,
            "depth": max_depth
        }

        self.lbl_paired.config(text=f"有效配对: {self.scan_result['paired']} 对")
        self.lbl_orphan_jpg.config(text=f"JPG孤立: {self.scan_result['orphan_jpg']} 个")
        self.lbl_orphan_json.config(text=f"JSON孤立: {self.scan_result['orphan_json']} 个")
        self.lbl_folder_count.config(text=f"扫描文件夹: {self.scan_result['folder_count']} 个")
        self.lbl_depth.config(text=f"嵌套层数: {self.scan_result['depth']} 层")

    def _clean_files(self):
        target_path = self.target_path.get()
        if not target_path:
            return

        mode = self.mode_var.get()
        deleted_count = 0

        jpg_names = set()
        json_names = set()

        for root_dir, dirs, files in os.walk(target_path):
            for file_name in files:
                if not self._is_valid_file(file_name):
                    continue

                name, ext = os.path.splitext(file_name)
                name_lower = name.lower()

                if ext.lower() in ('.jpg', '.jpeg'):
                    jpg_names.add(name_lower)
                elif ext.lower() == '.json':
                    json_names.add(name_lower)

        paired_names = jpg_names & json_names

        if mode == "jpg":
            orphan_jpg = jpg_names - json_names
            for root_dir, dirs, files in os.walk(target_path):
                for file_name in files:
                    if not self._is_valid_file(file_name):
                        continue

                    name, ext = os.path.splitext(file_name)
                    if ext.lower() in ('.jpg', '.jpeg') and name.lower() in orphan_jpg:
                        file_path = os.path.join(root_dir, file_name)
                        try:
                            os.remove(file_path)
                            deleted_count += 1
                        except Exception:
                            pass
        else:
            orphan_json = json_names - jpg_names
            for root_dir, dirs, files in os.walk(target_path):
                for file_name in files:
                    if not self._is_valid_file(file_name):
                        continue

                    name, ext = os.path.splitext(file_name)
                    if ext.lower() == '.json' and name.lower() in orphan_json:
                        file_path = os.path.join(root_dir, file_name)
                        try:
                            os.remove(file_path)
                            deleted_count += 1
                        except Exception:
                            pass

        for root_dir, dirs, files in os.walk(target_path, topdown=False):
            if root_dir == target_path:
                continue
            try:
                if not os.listdir(root_dir):
                    os.rmdir(root_dir)
            except Exception:
                pass

        self.clean_result = {
            "deleted": deleted_count,
            "paired": len(paired_names)
        }

        self.lbl_deleted.config(text=f"已清理: {self.clean_result['deleted']} 个")
        self.lbl_paired_clean.config(text=f"有效配对: {self.clean_result['paired']} 对")

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    app = OrphanImageCleaner()
    app.run()