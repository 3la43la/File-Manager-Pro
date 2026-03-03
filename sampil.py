import sys
import os
import shutil
import platform
import subprocess
from PyQt6.QtWidgets import (QApplication, QMainWindow, QPushButton, QVBoxLayout, 
                             QWidget, QFileDialog, QLabel, QMessageBox, QTabWidget, 
                             QListWidget, QHBoxLayout)
from PyQt6.QtCore import Qt
import arabic_reshaper

class FolderManagerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.initUI()

    def ar(self, text):
        if not text: return ""
        return arabic_reshaper.reshape(text)

    def open_folder_universal(self, path):
        path = os.path.normpath(path)
        try:
            if platform.system() == "Windows":
                os.startfile(path)
            elif platform.system() == "Darwin":
                subprocess.run(["open", path])
            else:
                subprocess.run(["xdg-open", path])
        except: pass

    def initUI(self):
        self.setWindowTitle(self.ar("مدير الملفات الاحترافي"))
        self.setFixedSize(550, 550)
        self.tabs = QTabWidget()
        self.tab1 = QWidget()
        self.init_tab1()
        self.tab2 = QWidget()
        self.init_tab2()
        self.tabs.addTab(self.tab1, self.ar("تفريغ مجلدات"))
        self.tabs.addTab(self.tab2, self.ar("نقل ملفات محددة"))
        self.setCentralWidget(self.tabs)

    def init_tab1(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        # توسيط العبارة في التبويب الأول أيضاً
        label = QLabel(self.ar("تنظيم ذكي: استخراج كافة الملفات من المجلدات الفرعية وجمعها في مكان واحد، مع تنظيف المجلدات الفارغة تلقائياً."))
        label.setWordWrap(True)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter) # التعديل هنا: توسيط
        label.setStyleSheet("font-size: 14px; color: #27ae60; padding: 10px;")
        
        btn = QPushButton(self.ar("بدء عملية التفريغ"))
        btn.setMinimumHeight(70)
        btn.setStyleSheet("background-color: #27ae60; color: white; font-weight: bold; border-radius: 12px; font-size: 16px;")
        btn.clicked.connect(self.flatten_process)
        
        layout.addWidget(label)
        layout.addStretch()
        layout.addWidget(btn)
        self.tab1.setLayout(layout)

    def init_tab2(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        self.selected_files = []
        
        # --- التعديل الجوهري: توسيط العبارة المطلوبة ---
        label = QLabel(self.ar("قائمة الملفات المختارة :"))
        label.setAlignment(Qt.AlignmentFlag.AlignCenter) # محاذاة في الوسط تماماً
        label.setStyleSheet("""
            font-weight: bold; 
            font-size: 14px; 
            color: #27ae60; 
            margin-bottom: 10px;
            padding: 5px;
        """)
        
        self.file_list_widget = QListWidget()
        self.file_list_widget.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.file_list_widget.setStyleSheet("""
            QListWidget {
                border: 2px solid #dcdde1;
                border-radius: 8px;
                background-color: #ffffff;
                color: #2f3640;
                font-weight: bold;
                font-size: 13px;
                padding: 5px;
            }
        """)

        list_btns_layout = QHBoxLayout()
        btn_select = QPushButton(self.ar("إضافة ملفات"))
        btn_select.setMinimumHeight(35)
        btn_clear = QPushButton(self.ar("تفريغ القائمة"))
        btn_clear.setMinimumHeight(35)
        btn_clear.setStyleSheet("color: #e74c3c;")
        btn_select.clicked.connect(self.select_files)
        btn_clear.clicked.connect(self.clear_list)
        list_btns_layout.addWidget(btn_select)
        list_btns_layout.addWidget(btn_clear)

        btn_move = QPushButton(self.ar("تحديد الوجهة وبدء النقل"))
        btn_move.setMinimumHeight(65)
        btn_move.setStyleSheet("background-color: #2980b9; color: white; font-weight: bold; border-radius: 12px; font-size: 16px;")
        btn_move.clicked.connect(self.move_specific_files)

        layout.addWidget(label)
        layout.addWidget(self.file_list_widget)
        layout.addLayout(list_btns_layout)
        layout.addStretch()
        layout.addWidget(btn_move)
        self.tab2.setLayout(layout)

    def flatten_process(self):
        target_dir = QFileDialog.getExistingDirectory(self, self.ar("اختر المجلد المستهدف"))
        if not target_dir: return
        try:
            count = 0
            for root_path, dirs, files in os.walk(target_dir, topdown=False):
                for file in files:
                    src, dst = os.path.join(root_path, file), os.path.join(target_dir, file)
                    if src != dst:
                        shutil.move(src, self.get_unique_path(dst))
                        count += 1
                if root_path != target_dir: os.rmdir(root_path)
            self.show_message("نجاح", f"اكتملت العملية! تم نقل {count} ملف بنجاح.")
            self.open_folder_universal(target_dir)
        except Exception as e: self.show_message("خطأ", str(e))

    def select_files(self):
        files, _ = QFileDialog.getOpenFileNames(self, self.ar("اختر الملفات"))
        if files:
            self.selected_files.extend(files)
            self.update_list_display()

    def clear_list(self):
        self.selected_files = []
        self.file_list_widget.clear()

    def update_list_display(self):
        self.file_list_widget.clear()
        for f in self.selected_files:
            self.file_list_widget.addItem(os.path.basename(f))

    def move_specific_files(self):
        if not self.selected_files:
            self.show_message("تنبيه", "يرجى اختيار ملفات أولاً!")
            return
        dest_dir = QFileDialog.getExistingDirectory(self, self.ar("اختر وجهة النقل"))
        if not dest_dir: return
        try:
            for file_path in self.selected_files:
                dest_path = os.path.join(dest_dir, os.path.basename(file_path))
                shutil.move(file_path, self.get_unique_path(dest_path))
            self.show_message("تم النقل", "تم نقل جميع الملفات بنجاح.")
            self.clear_list()
            self.open_folder_universal(dest_dir)
        except Exception as e: self.show_message("خطأ", str(e))

    def get_unique_path(self, path):
        counter = 1
        base, ext = os.path.splitext(path)
        new_path = path
        while os.path.exists(new_path):
            new_path = f"{base}_{counter}{ext}"
            counter += 1
        return new_path

    def show_message(self, title, text):
        msg = QMessageBox(self)
        msg.setWindowTitle(self.ar(title))
        msg.setText(self.ar(text))
        msg.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        msg.exec()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
    window = FolderManagerApp()
    window.show()
    sys.exit(app.exec())