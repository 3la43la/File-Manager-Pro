import os
import shutil
import hashlib
import threading
from pathlib import Path
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QTextEdit, QProgressBar, 
                             QLabel, QFileDialog, QMessageBox)
from PyQt6.QtCore import Qt, pyqtSignal, QObject
from PyQt6.QtGui import QFont

import arabic_reshaper
from bidi.algorithm import get_display

# كلاس لإرسال الرسائل من الـ Thread إلى الواجهة بأمان
class WorkerSignals(QObject):
    log_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(int)
    finished_signal = pyqtSignal(list)

class MediaMoverPyQt(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle(self.fix_text("ناقل الملفات الاحترافي | Alaa.ksa"))
        self.resize(900, 650)
        self.setStyleSheet("background-color: #1e1e1e; color: #ffffff;")

        # البيانات
        self.source_dirs = set()
        self.dest_dir = None
        self.transfer_log = []
        self.categories = {
            'Images': {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.heic', '.bmp'},
            'Videos': {'.mp4', '.mkv', '.mov', '.avi', '.webm'},
            'Documents': {'.pdf', '.docx', '.doc', '.txt', '.xlsx', '.pptx'},
            'Archives': {'.zip', '.rar', '.7z', '.tar'}
        }
        self.all_extensions = {ext for sub in self.categories.values() for ext in sub}

        self._init_ui()

    def fix_text(self, text):
        if not text: return ""
        reshaped = arabic_reshaper.reshape(text)
        return get_display(reshaped)

    def _init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QHBoxLayout(central_widget)

        # --- القائمة الجانبية ---
        sidebar = QVBoxLayout()
        
        btn_style = """
            QPushButton {
                background-color: #2c3e50; border: none; padding: 10px; 
                border-radius: 5px; font-size: 14px; min-width: 150px;
            }
            QPushButton:hover { background-color: #34495e; }
            QPushButton:disabled { background-color: #7f8c8d; }
        """

        self.btn_add = QPushButton(self.fix_text("➕ إضافة مصدر"))
        self.btn_dest = QPushButton(self.fix_text("🎯 تحديد الوجهة"))
        self.btn_clear = QPushButton(self.fix_text("🧹 مسح القائمة"))
        self.btn_start = QPushButton(self.fix_text("🚀 بدء النقل"))
        
        self.btn_start.setEnabled(False)
        self.btn_start.setStyleSheet("background-color: #27ae60;")

        for btn in [self.btn_add, self.btn_dest, self.btn_clear, self.btn_start]:
            btn.setStyleSheet(btn_style if btn != self.btn_start else btn_style + "background-color: #27ae60;")
            sidebar.addWidget(btn)
        
        sidebar.addStretch()
        layout.addLayout(sidebar)

        # --- المنطقة الرئيسية ---
        main_layout = QVBoxLayout()

        self.sources_display = QTextEdit()
        self.sources_display.setReadOnly(True)
        self.sources_display.setMaximumHeight(100)
        
        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)
        self.log_display.setStyleSheet("background-color: #000; color: #2ecc71; font-family: 'Monospace';")

        self.progress_bar = QProgressBar()
        self.progress_bar.setStyleSheet("QProgressBar { border: 2px solid grey; border-radius: 5px; text-align: center; } "
                                      "QProgressBar::chunk { background-color: #2ecc71; }")

        main_layout.addWidget(QLabel(self.fix_text("المجلدات المختارة:")))
        main_layout.addWidget(self.sources_display)
        main_layout.addWidget(QLabel(self.fix_text("سجل العمليات:")))
        main_layout.addWidget(self.log_display)
        main_layout.addWidget(self.progress_bar)

        layout.addLayout(main_layout, stretch=1)

        # الربط بالدوال
        self.btn_add.clicked.connect(self.add_source)
        self.btn_dest.clicked.connect(self.set_destination)
        self.btn_clear.clicked.connect(self.clear_all)
        self.btn_start.clicked.connect(self.start_process)

    def add_source(self):
        folder = QFileDialog.getExistingDirectory(self, self.fix_text("اختر مجلد المصدر"))
        if folder:
            self.source_dirs.add(folder)
            self.sources_display.append(f"📂 {folder}")
            self.check_ready()

    def set_destination(self):
        folder = QFileDialog.getExistingDirectory(self, self.fix_text("اختر مجلد الوجهة"))
        if folder:
            self.dest_dir = Path(folder)
            self.log_message(f"الوجهة: {folder}")
            self.check_ready()

    def check_ready(self):
        if self.source_dirs and self.dest_dir:
            self.btn_start.setEnabled(True)

    def clear_all(self):
        self.source_dirs.clear()
        self.sources_display.clear()
        self.btn_start.setEnabled(False)

    def log_message(self, msg):
        self.log_display.append(f"> {self.fix_text(msg)}")

    def start_process(self):
        self.btn_start.setEnabled(False)
        self.transfer_log = []
        
        # إعداد الـ Worker والـ Thread
        self.signals = WorkerSignals()
        self.signals.log_signal.connect(self.log_message)
        self.signals.progress_signal.connect(self.progress_bar.setValue)
        self.signals.finished_signal.connect(self.on_finished)
        
        threading.Thread(target=self.engine_worker, daemon=True).start()

    def get_hash(self, path):
        h = hashlib.md5()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""): h.update(chunk)
        return h.hexdigest()

    def engine_worker(self):
        files = []
        for s in self.source_dirs:
            for p in Path(s).rglob('*'):
                if p.is_file() and p.suffix.lower() in self.all_extensions:
                    files.append(p)

        if not files:
            self.signals.log_signal.emit("لم يتم العثور على ملفات.")
            return

        for i, f_path in enumerate(files):
            try:
                cat = "Others"
                for c, exts in self.categories.items():
                    if f_path.suffix.lower() in exts: cat = c; break
                
                dest_f = self.dest_dir / cat
                dest_f.mkdir(exist_ok=True)
                target = dest_f / f_path.name
                
                if target.exists():
                    if self.get_hash(f_path) == self.get_hash(target):
                        self.transfer_log.append(f_path)
                        continue
                    target = dest_f / f_path.with_name(f"{f_path.stem}_{i}{f_path.suffix}").name

                shutil.copy2(f_path, target)
                if self.get_hash(f_path) == self.get_hash(target):
                    self.transfer_log.append(f_path)
                    self.signals.log_signal.emit(f"تم: {f_path.name}")
            except: pass
            
            self.signals.progress_signal.emit(int((i+1)/len(files)*100))

        self.signals.finished_signal.emit(self.transfer_log)

    def on_finished(self, log):
        QMessageBox.information(self, self.fix_text("انتهى"), self.fix_text(f"تم نقل {len(log)} ملف بنجاح."))
        if log:
            res = QMessageBox.question(self, self.fix_text("تأكيد"), self.fix_text("حذف الأصول؟"))
            if res == QMessageBox.StandardButton.Yes:
                for f in log: 
                    try: f.unlink()
                    except: pass
                self.log_message("تم الحذف.")
        self.btn_start.setEnabled(True)

if __name__ == "__main__":
    app = QApplication([])
    app.setStyle('Fusion') # لضمان مظهر موحد على لينكس
    window = MediaMoverPyQt()
    window.show()
    app.exec()