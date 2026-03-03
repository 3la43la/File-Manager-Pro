import sys
import os
import shutil
import platform
import subprocess
from PyQt6.QtWidgets import (QApplication, QMainWindow, QPushButton, QVBoxLayout, 
                             QWidget, QFileDialog, QLabel, QMessageBox, QTabWidget, QListWidget)
from PyQt6.QtCore import Qt
import arabic_reshaper

class FolderManagerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.initUI()

    def ar(self, text):
        """إصلاح ربط الحروف العربية"""
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
        self.setFixedSize(550, 500)
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
        label = QLabel(self.ar("سيقوم هذا الخيار بسحب جميع الملفات من المجلدات الفرعية للمجلد الرئيسي وحذفها."))
        label.setWordWrap(True)
        btn = QPushButton(self.ar("بدء عملية التفريغ"))
        btn.setMinimumHeight(60)
        btn.setStyleSheet("background-color: #27ae60; color: white; font-weight: bold; border-radius: 10px;")
        btn.clicked.connect(self.flatten_process)
        layout.addWidget(label)
        layout.addStretch()
        layout.addWidget(btn)
        self.tab1.setLayout(layout)

    def init_tab2(self):
        layout = QVBoxLayout()
        self.selected_files = []
        
        label = QLabel(self.ar("قائمة الملفات المختارة (تظهر بخط غامق):"))
        label.setAlignment(Qt.AlignmentFlag.AlignRight)
        
        # التعديل هنا: خلفية بيضاء وخط غامق
        self.file_list_widget = QListWidget()
        self.file_list_widget.setStyleSheet("""
            QListWidget {
                border: 2px solid #dcdde1;
                border-radius: 8px;
                background-color: #ffffff;
                color: #2f3640;
                font-weight: bold;
                font-size: 13px;
                padding: 10px;
            }
            QListWidget::item {
                padding: 5px;
                border-bottom: 1px solid #f1f2f6;
            }
        """)

        btn_select = QPushButton(self.ar("1. اختيار الملفات"))
        btn_select.setMinimumHeight(45)
        btn_select.setStyleSheet("background-color: #2980b9; color: white; font-weight: bold; border-radius: 10px;")
        btn_select.clicked.connect(self.select_files)

        btn_move = QPushButton(self.ar("2. تحديد الوجهة ونقل الملفات"))
        btn_move.setMinimumHeight(60)
        btn_move.setStyleSheet("background-color: #2980b9; color: white; font-weight: bold; border-radius: 10px; font-size: 16px;")
        btn_move.clicked.connect(self.move_specific_files)

        layout.addWidget(label)
        layout.addWidget(self.file_list_widget)
        layout.addWidget(btn_select)
        layout.addStretch()
        layout.addWidget(btn_move)
        self.tab2.setLayout(layout)

    def select_files(self):
        files, _ = QFileDialog.getOpenFileNames(self, self.ar("اختر الملفات"))
        if files:
            self.selected_files = files
            self.file_list_widget.clear()
            for f in files:
                self.file_list_widget.addItem(os.path.basename(f))

    def move_specific_files(self):
        if not self.selected_files:
            self.show_message("تنبيه", "يرجى اختيار ملفات أولاً!")
            return
        dest_dir = QFileDialog.getExistingDirectory(self, self.ar("اختر الوجهة"))
        if not dest_dir: return
        try:
            for file_path in self.selected_files:
                dest_path = os.path.join(dest_dir, os.path.basename(file_path))
                shutil.move(file_path, self.get_unique_path(dest_path))
            self.show_message("نجاح", "تم نقل الملفات بنجاح.")
            self.file_list_widget.clear()
            self.selected_files = []
            self.open_folder_universal(dest_dir)
        except Exception as e: self.show_message("خطأ", str(e))

    def flatten_process(self):
        target_dir = QFileDialog.getExistingDirectory(self, self.ar("اختر المجلد"))
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
            self.show_message("نجاح", f"تم نقل {count} ملف.")
            self.open_folder_universal(target_dir)
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