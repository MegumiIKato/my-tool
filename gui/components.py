import customtkinter as ctk
from .theme import *


class CardFrame(ctk.CTkFrame):
    """卡片容器组件"""
    
    def __init__(self, master, title: str = "", **kwargs):
        super().__init__(master, **kwargs)
        
        if title:
            self.title_label = ctk.CTkLabel(
                self, text=title, font=APP_FONT_BOLD,
                text_color=COLOR_TEXT_PRIMARY
            )
            self.title_label.pack(anchor="w", padx=15, pady=(10, 5))
        
        self.content_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.content_frame.pack(fill="both", expand=True, padx=10, pady=10)


class ParameterInput(ctk.CTkFrame):
    """参数输入组件"""
    
    def __init__(self, master, label: str, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        
        self.label = ctk.CTkLabel(
            self, text=label, font=APP_FONT,
            text_color=COLOR_TEXT_SECONDARY
        )
        self.label.pack(side="left", padx=(0, 10))
        
        self.entry = ctk.CTkEntry(
            self, font=APP_FONT,
            placeholder_text_color=COLOR_TEXT_MUTED
        )
        self.entry.pack(side="left", fill="x", expand=True)
    
    def get(self) -> str:
        return self.entry.get()
    
    def set(self, value: str):
        self.entry.delete(0, "end")
        self.entry.insert(0, value)


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
            placeholder_text_color=COLOR_TEXT_MUTED
        )
        self.entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        self.btn_browse = ctk.CTkButton(
            self, text="浏览", font=APP_FONT,
            width=80, command=self._browse
        )
        self.btn_browse.pack(side="left")
    
    def _browse(self):
        from tkinter import filedialog
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


class ActionButton(ctk.CTkButton):
    """操作按钮组件"""
    
    def __init__(self, master, text: str, command, **kwargs):
        super().__init__(
            master, text=text, command=command,
            font=APP_FONT, **kwargs
        )
