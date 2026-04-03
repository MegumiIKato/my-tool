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


class OrphanImageCleaner:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("孤立JPG/JSON文件清理工具")
        self.root.geometry("500x420")
        self.root.resizable(False, False)

        self.target_path = tk.StringVar()
        self.scan_result = {"paired": 0, "orphan_jpg": 0, "orphan_json": 0}
        self.clean_result = {"deleted": 0, "paired": 0}

        self.mode_var = tk.StringVar(value="jpg")
        self.valid_extensions = ('.jpg', '.jpeg', '.json')

        self._create_widgets()

    def _create_widgets(self):
        mode_frame = tk.Frame(self.root, pady=10)
        mode_frame.pack(fill="x", padx=20)

        tk.Label(mode_frame, text="清理模式:", font=("Arial", 12)).pack(side="left")

        rb1 = tk.Radiobutton(
            mode_frame, text="删除孤立图片（无JSON的JPG）",
            variable=self.mode_var, value="jpg",
            font=("Arial", 10)
        )
        rb1.pack(side="left", padx=10)

        rb2 = tk.Radiobutton(
            mode_frame, text="删除孤立JSON（无JPG的JSON）",
            variable=self.mode_var, value="json",
            font=("Arial", 10)
        )
        rb2.pack(side="left", padx=10)

        path_frame = tk.Frame(self.root, pady=5)
        path_frame.pack(fill="x", padx=20)

        tk.Label(path_frame, text="选择文件夹:", font=("Arial", 11)).pack(side="left")

        self.path_entry = tk.Entry(path_frame, textvariable=self.target_path, width=35)
        self.path_entry.pack(side="left", padx=5)

        tk.Button(path_frame, text="浏览", command=self._browse_folder, width=8).pack(side="left")

        scan_btn = tk.Button(self.root, text="开始扫描", command=self._scan_files, height=2, width=15)
        scan_btn.pack(pady=5)

        scan_result_frame = tk.Frame(self.root, bd=2, relief="sunken")
        scan_result_frame.pack(fill="x", padx=20, pady=5)

        tk.Label(scan_result_frame, text="扫描结果:", font=("Arial", 11, "bold")).pack(anchor="w")

        self.scan_labels = tk.Frame(scan_result_frame)
        self.scan_labels.pack(fill="x", pady=5)

        self.lbl_paired = tk.Label(self.scan_labels, text="有效配对: 0 对", font=("Arial", 10))
        self.lbl_paired.pack(side="left", padx=15)

        self.lbl_orphan_jpg = tk.Label(self.scan_labels, text="JPG孤立: 0 个", font=("Arial", 10))
        self.lbl_orphan_jpg.pack(side="left", padx=15)

        self.lbl_orphan_json = tk.Label(self.scan_labels, text="JSON孤立: 0 个", font=("Arial", 10))
        self.lbl_orphan_json.pack(side="left", padx=15)

        clean_btn = tk.Button(self.root, text="开始清理", command=self._clean_files, height=2, width=15)
        clean_btn.pack(pady=5)

        clean_result_frame = tk.Frame(self.root, bd=2, relief="sunken")
        clean_result_frame.pack(fill="x", padx=20, pady=5)

        tk.Label(clean_result_frame, text="清理结果:", font=("Arial", 11, "bold")).pack(anchor="w")

        self.clean_labels = tk.Frame(clean_result_frame)
        self.clean_labels.pack(fill="x", pady=5)

        self.lbl_deleted = tk.Label(self.clean_labels, text="已清理: 0 个", font=("Arial", 10))
        self.lbl_deleted.pack(side="left", padx=15)

        self.lbl_paired_clean = tk.Label(self.clean_labels, text="有效配对: 0 对", font=("Arial", 10))
        self.lbl_paired_clean.pack(side="left", padx=15)

    def _browse_folder(self):
        folder = filedialog.askdirectory(title="选择需要清理的文件夹")
        if folder:
            self.target_path.set(folder)
            self._reset_labels()

    def _reset_labels(self):
        self.lbl_paired.config(text="有效配对: 0 对")
        self.lbl_orphan_jpg.config(text="JPG孤立: 0 个")
        self.lbl_orphan_json.config(text="JSON孤立: 0 个")
        self.lbl_deleted.config(text="已清理: 0 个")
        self.lbl_paired_clean.config(text="有效配对: 0 对")

    def _is_valid_file(self, filename):
        _, ext = os.path.splitext(filename)
        return ext.lower() in self.valid_extensions

    def _scan_files(self):
        target_path = self.target_path.get()
        if not target_path:
            return

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
        orphan_jpg = jpg_names - json_names
        orphan_json = json_names - jpg_names

        self.scan_result = {
            "paired": len(paired_names),
            "orphan_jpg": len(orphan_jpg),
            "orphan_json": len(orphan_json)
        }

        self.lbl_paired.config(text=f"有效配对: {self.scan_result['paired']} 对")
        self.lbl_orphan_jpg.config(text=f"JPG孤立: {self.scan_result['orphan_jpg']} 个")
        self.lbl_orphan_json.config(text=f"JSON孤立: {self.scan_result['orphan_json']} 个")

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
