# -*- coding: utf-8 -*-
import os
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import tkinter.font as tkfont

# تعريف امتدادات الملفات المطلوبة
IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp', '.ico', '.svg'}
VIDEO_EXTENSIONS = {'.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm', '.m4v', '.mpg', '.mpeg'}
ALLOWED_EXTENSIONS = IMAGE_EXTENSIONS.union(VIDEO_EXTENSIONS)

class FileMoverApp:
    def __init__(self, root):
        self.root = root
        self.root.title("نقل ملفات الوسائط")
        self.root.geometry("600x500")
        self.root.resizable(True, True)

        # ضبط الخط لدعم اللغة العربية
        self.setup_arabic_font()

        # متغيرات لتخزين المسارات
        self.source_folders = []
        self.destination_folder = ""

        # إنشاء واجهة المستخدم
        self.create_widgets()

    def setup_arabic_font(self):
        """ضبط الخط الافتراضي ليدعم العربية"""
        # قائمة بالخطوط التي تدعم العربية (مرتبة حسب الأفضلية)
        arabic_fonts = ['Traditional Arabic', 'Tahoma', 'Arial', 'Helvetica', 'Sans Serif']
        selected_font = None

        # البحث عن أول خط موجود في النظام
        for font_family in arabic_fonts:
            if font_family in tkfont.families():
                selected_font = font_family
                break
        if not selected_font:
            selected_font = 'Arial'  # خط افتراضي

        # تغيير الخط الافتراضي لجميع العناصر
        default_font = tkfont.nametofont("TkDefaultFont")
        default_font.configure(family=selected_font, size=10)

        # تغيير خط Text و Listbox أيضاً
        self.text_font = tkfont.Font(family=selected_font, size=10)

    def create_widgets(self):
        # إطار المصادر
        source_frame = ttk.LabelFrame(self.root, text="المجلدات المصدر", padding=5)
        source_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # قائمة المجلدات المصدر مع دعم العربية
        self.source_listbox = tk.Listbox(source_frame, selectmode=tk.SINGLE, font=self.text_font)
        self.source_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # أزرار التحكم بالمصادر
        btn_frame = ttk.Frame(source_frame)
        btn_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(5, 0))

        ttk.Button(btn_frame, text="إضافة مجلد", command=self.add_source).pack(fill=tk.X, pady=2)
        ttk.Button(btn_frame, text="حذف المحدد", command=self.remove_source).pack(fill=tk.X, pady=2)
        ttk.Button(btn_frame, text="تفريغ الكل", command=self.clear_sources).pack(fill=tk.X, pady=2)

        # إطار الوجهة
        dest_frame = ttk.LabelFrame(self.root, text="مجلد الوجهة", padding=5)
        dest_frame.pack(fill=tk.X, padx=10, pady=5)

        self.dest_label = ttk.Label(dest_frame, text="لم يتم اختيار مجلد", relief=tk.SUNKEN, anchor=tk.W)
        self.dest_label.pack(side=tk.LEFT, fill=tk.X, expand=True)

        ttk.Button(dest_frame, text="اختيار مجلد", command=self.select_destination).pack(side=tk.RIGHT, padx=(5, 0))

        # إطار الإعدادات
        options_frame = ttk.LabelFrame(self.root, text="خيارات", padding=5)
        options_frame.pack(fill=tk.X, padx=10, pady=5)

        self.keep_structure_var = tk.BooleanVar()
        ttk.Checkbutton(options_frame, text="الحفاظ على هيكل المجلدات الفرعية", variable=self.keep_structure_var).pack(anchor=tk.W)

        # إطار السجل والتحكم
        log_frame = ttk.LabelFrame(self.root, text="سجل العمليات", padding=5)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.log_text = tk.Text(log_frame, height=8, state=tk.DISABLED, wrap=tk.WORD, font=self.text_font)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.config(yscrollcommand=scrollbar.set)

        # إطار الأزرار السفلية
        bottom_frame = ttk.Frame(self.root)
        bottom_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Button(bottom_frame, text="بدء النقل", command=self.start_move).pack(side=tk.LEFT, padx=5)
        ttk.Button(bottom_frame, text="إغلاق", command=self.root.quit).pack(side=tk.RIGHT, padx=5)

    def add_source(self):
        folder = filedialog.askdirectory(title="اختر مجلد مصدر")
        if folder:
            self.source_folders.append(folder)
            self.source_listbox.insert(tk.END, folder)

    def remove_source(self):
        selected = self.source_listbox.curselection()
        if selected:
            index = selected[0]
            del self.source_folders[index]
            self.source_listbox.delete(index)

    def clear_sources(self):
        self.source_folders.clear()
        self.source_listbox.delete(0, tk.END)

    def select_destination(self):
        folder = filedialog.askdirectory(title="اختر مجلد الوجهة")
        if folder:
            self.destination_folder = folder
            self.dest_label.config(text=folder)

    def log(self, message):
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
        self.root.update()

    def get_unique_filename(self, dest_path, filename):
        """إرجاع اسم ملف فريد في المجلد الوجهة عن طريق إضافة رقم إذا كان الاسم موجوداً"""
        base, ext = os.path.splitext(filename)
        counter = 1
        new_filename = filename
        while os.path.exists(os.path.join(dest_path, new_filename)):
            new_filename = f"{base}_{counter}{ext}"
            counter += 1
        return new_filename

    def move_files(self):
        moved_count = 0
        error_count = 0

        for src_folder in self.source_folders:
            if not os.path.isdir(src_folder):
                self.log(f"❌ المجلد غير موجود: {src_folder}")
                continue

            for root, dirs, files in os.walk(src_folder):
                # تحديد المسار النسبي للمجلد الفرعي
                rel_path = os.path.relpath(root, src_folder)
                if rel_path == '.':
                    rel_path = ''

                for file in files:
                    file_ext = os.path.splitext(file)[1].lower()
                    if file_ext in ALLOWED_EXTENSIONS:
                        src_file = os.path.join(root, file)

                        # تحديد مسار الوجهة
                        if self.keep_structure_var.get():
                            # الحفاظ على هيكل المجلدات الفرعية
                            dest_subdir = os.path.join(self.destination_folder, rel_path)
                            os.makedirs(dest_subdir, exist_ok=True)
                            dest_file = os.path.join(dest_subdir, file)
                        else:
                            # نقل جميع الملفات إلى مجلد واحد
                            dest_file = os.path.join(self.destination_folder, file)

                        # التأكد من عدم وجود تعارض في الأسماء
                        if not self.keep_structure_var.get():
                            # فقط في حالة النقل المسطح نتعامل مع الأسماء المكررة
                            dest_file = os.path.join(self.destination_folder, self.get_unique_filename(self.destination_folder, file))

                        try:
                            shutil.move(src_file, dest_file)
                            self.log(f"✅ تم نقل: {src_file} -> {dest_file}")
                            moved_count += 1
                        except Exception as e:
                            self.log(f"❌ خطأ في نقل {src_file}: {str(e)}")
                            error_count += 1

        return moved_count, error_count

    def start_move(self):
        # التحقق من المدخلات
        if not self.source_folders:
            messagebox.showwarning("تحذير", "الرجاء إضافة مجلدات مصدر على الأقل.")
            return
        if not self.destination_folder:
            messagebox.showwarning("تحذير", "الرجاء اختيار مجلد الوجهة.")
            return
        if not os.path.isdir(self.destination_folder):
            messagebox.showerror("خطأ", "مجلد الوجهة غير موجود.")
            return

        # تأكيد العملية
        result = messagebox.askyesno("تأكيد", "هل أنت متأكد من بدء عملية النقل؟\nسيتم نقل جميع ملفات الصور والفيديو من المجلدات المصدر إلى الوجهة.")
        if not result:
            return

        self.log("🔄 جاري بدء عملية النقل...")
        moved, errors = self.move_files()
        self.log(f"✨ انتهت العملية: تم نقل {moved} ملف، فشل {errors} ملف.")

        messagebox.showinfo("اكتمل", f"تمت العملية بنجاح.\nالملفات المنقولة: {moved}\nالأخطاء: {errors}")

if __name__ == "__main__":
    root = tk.Tk()
    app = FileMoverApp(root)
    root.mainloop()