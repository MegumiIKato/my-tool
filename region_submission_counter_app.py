import os
import subprocess
import sys
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk

from tools.region_submission_counter import run_region_submission_count


class RegionSubmissionCounterApp(tk.Tk):
    """临时行政区提交配对统计工具。"""

    def __init__(self):
        super().__init__()

        self.title("行政区提交配对统计")
        self.geometry("860x540")
        self.minsize(760, 460)

        self.result_path = None
        self.path_var = tk.StringVar()

        self._create_ui()

    def _create_ui(self):
        container = ttk.Frame(self, padding=16)
        container.pack(fill="both", expand=True)
        container.columnconfigure(1, weight=1)
        container.rowconfigure(2, weight=1)

        title_label = ttk.Label(container, text="行政区提交配对统计")
        title_label.grid(row=0, column=0, columnspan=4, sticky="w", pady=(0, 12))

        path_label = ttk.Label(container, text="根目录")
        path_label.grid(row=1, column=0, sticky="w", padx=(0, 10), pady=(0, 12))

        path_entry = ttk.Entry(container, textvariable=self.path_var)
        path_entry.grid(row=1, column=1, sticky="ew", pady=(0, 12))

        browse_button = ttk.Button(container, text="浏览", command=self._browse_folder)
        browse_button.grid(row=1, column=2, sticky="ew", padx=10, pady=(0, 12))

        self.run_button = ttk.Button(container, text="开始统计", command=self._run_task)
        self.run_button.grid(row=1, column=3, sticky="ew", pady=(0, 12))

        self.log_text = scrolledtext.ScrolledText(container, wrap="word", font=("Microsoft YaHei UI", 10))
        self.log_text.grid(row=2, column=0, columnspan=4, sticky="nsew")
        self.log_text.configure(state="disabled")

        footer = ttk.Frame(container)
        footer.grid(row=3, column=0, columnspan=4, sticky="ew", pady=(12, 0))
        footer.columnconfigure(0, weight=1)

        self.open_button = ttk.Button(footer, text="打开结果目录", command=self._open_result_folder, state="disabled")
        self.open_button.grid(row=0, column=1, sticky="e")

        close_button = ttk.Button(footer, text="关闭", command=self.destroy)
        close_button.grid(row=0, column=2, sticky="e", padx=(10, 0))

    def _append_log(self, message: str):
        self.log_text.configure(state="normal")
        self.log_text.insert("end", message + "\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def _clear_log(self):
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.configure(state="disabled")

    def _browse_folder(self):
        selected_folder = filedialog.askdirectory(title="选择根目录")
        if selected_folder:
            self.path_var.set(selected_folder)

    def _run_task(self):
        root_folder = self.path_var.get().strip()
        if not root_folder:
            messagebox.showwarning("提示", "请先选择根目录")
            return

        self.result_path = None
        self.open_button.configure(state="disabled")
        self.run_button.configure(state="disabled")
        self._clear_log()
        self._append_log(f"开始统计根目录: {root_folder}")

        def worker():
            try:
                output_path, error, stats = run_region_submission_count(root_folder)
            except Exception as exc:
                output_path, error, stats = None, f"执行失败: {str(exc)}", {}

            self.after(0, lambda: self._on_task_complete(output_path, error, stats))

        threading.Thread(target=worker, daemon=True).start()

    def _on_task_complete(self, output_path: str | None, error: str | None, stats: dict):
        self.run_button.configure(state="normal")

        if error:
            self._append_log(f"错误: {error}")
            messagebox.showerror("错误", error)
            return

        self.result_path = output_path
        self.open_button.configure(state="normal")

        self._append_log(f"统计完成，结果文件: {output_path}")
        self._append_log(f"扫描到的文件目录数: {stats['total_pairable_dirs']}")
        self._append_log(f"参与统计的文件目录数: {stats['counted_pairable_dirs']}")
        self._append_log(f"识别到的提交批次数: {stats['submission_count']}")
        self._append_log(f"有数据的行政区数量: {stats['region_count_with_data']}")
        self._append_log(f"图片与 JSON 配对成功总数: {stats['total_matched']}")

        if stats["invalid_structure_count"]:
            self._append_log(f"未命中目录结构的文件目录数: {stats['invalid_structure_count']}")
            for sample in stats["invalid_structure_samples"]:
                self._append_log(f"  结构未识别: {sample}")

        if stats["unmatched_region_count"]:
            self._append_log(f"未匹配到行政区映射的文件目录数: {stats['unmatched_region_count']}")
            for sample in stats["unmatched_region_samples"]:
                self._append_log(f"  行政区目录: {sample['region_dir']} | 文件目录: {sample['leaf_dir']}")

        messagebox.showinfo("完成", f"统计完成\n结果已保存到:\n{output_path}")

    def _open_result_folder(self):
        if not self.result_path:
            return

        result_dir = os.path.dirname(self.result_path)
        try:
            if sys.platform == "win32":
                os.startfile(result_dir)
            elif sys.platform == "darwin":
                subprocess.run(["open", result_dir], check=False)
            else:
                subprocess.run(["xdg-open", result_dir], check=False)
        except Exception as exc:
            messagebox.showerror("错误", f"打开结果目录失败: {str(exc)}")


def main():
    app = RegionSubmissionCounterApp()
    app.mainloop()


if __name__ == "__main__":
    main()
