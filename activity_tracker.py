import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
import sqlite3
import json
import datetime
from datetime import timedelta
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import pandas as pd # type: ignore
from collections import defaultdict
import os
import hashlib

class ActivityTracker:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("📊 Günlük Aktivite Takibi")
        self.root.geometry("1200x800")
        self.root.configure(bg='#f0f0f0')
        
        # Veritabanı başlatma
        self.init_database()
        
        # Parola kontrolü
        if not self.check_password():
            self.root.destroy()
            return
            
        # Ana arayüz oluşturma
        self.create_interface()
        
        # Verileri yükle
        self.refresh_data()
    
    def init_database(self):
        """SQLite veritabanını başlat"""
        self.conn = sqlite3.connect('activities.db')
        self.cursor = self.conn.cursor()
        
        # Tablolar oluştur
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS activities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                activity TEXT NOT NULL,
                duration INTEGER NOT NULL,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        ''')
        
        self.conn.commit()
    
    def check_password(self):
        """Parola kontrolü yap"""
        # Kayıtlı parola var mı kontrol et
        self.cursor.execute("SELECT value FROM settings WHERE key = 'password'")
        stored_password = self.cursor.fetchone()
        
        if stored_password is None:
            # İlk kurulum - parola belirle
            password = simpledialog.askstring("🔒 Parola Belirle", 
                                            "İlk kullanım için bir parola belirleyin:", 
                                            show='*')
            if password:
                hashed = hashlib.sha256(password.encode()).hexdigest()
                self.cursor.execute("INSERT INTO settings (key, value) VALUES ('password', ?)", (hashed,))
                self.conn.commit()
                return True
            return False
        else:
            # Parola kontrolü
            password = simpledialog.askstring("🔒 Parola Girişi", 
                                            "Uygulamaya erişim için parolanızı girin:", 
                                            show='*')
            if password:
                hashed = hashlib.sha256(password.encode()).hexdigest()
                return hashed == stored_password[0]
            return False
    
    def create_interface(self):
        """Ana arayüzü oluştur"""
        # Notebook (sekmeli arayüz) oluştur
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Sekmeler oluştur
        self.create_input_tab()
        self.create_records_tab()
        self.create_reports_tab()
        self.create_charts_tab()
        self.create_settings_tab()
    
    def create_input_tab(self):
        """Veri girişi sekmesi"""
        input_frame = ttk.Frame(self.notebook)
        self.notebook.add(input_frame, text="📝 Etkinlik Ekle")
        
        # Ana başlık
        title_label = tk.Label(input_frame, text="📅 Günlük Etkinlik Girişi", 
                              font=('Arial', 16, 'bold'), bg='#f0f0f0')
        title_label.pack(pady=20)
        
        # Form alanları
        form_frame = ttk.LabelFrame(input_frame, text="Etkinlik Bilgileri", padding="20")
        form_frame.pack(pady=20, padx=50, fill='x')
        
        # Tarih seçimi
        ttk.Label(form_frame, text="📆 Tarih:").grid(row=0, column=0, sticky='w', pady=5)
        self.date_var = tk.StringVar(value=datetime.date.today().strftime('%Y-%m-%d'))
        date_entry = ttk.Entry(form_frame, textvariable=self.date_var, width=20)
        date_entry.grid(row=0, column=1, sticky='w', padx=(10, 0))
        
        # Etkinlik adı
        ttk.Label(form_frame, text="🎯 Etkinlik:").grid(row=1, column=0, sticky='w', pady=5)
        self.activity_var = tk.StringVar()
        self.activity_combo = ttk.Combobox(form_frame, textvariable=self.activity_var, width=30)
        self.activity_combo.grid(row=1, column=1, sticky='w', padx=(10, 0))
        self.load_activity_suggestions()
        
        # Süre girişi
        ttk.Label(form_frame, text="⏱️ Süre (dakika):").grid(row=2, column=0, sticky='w', pady=5)
        self.duration_var = tk.IntVar()
        duration_entry = ttk.Entry(form_frame, textvariable=self.duration_var, width=20)
        duration_entry.grid(row=2, column=1, sticky='w', padx=(10, 0))
        
        # Not alanı
        ttk.Label(form_frame, text="📝 Notlar:").grid(row=3, column=0, sticky='nw', pady=5)
        self.notes_text = tk.Text(form_frame, width=40, height=4)
        self.notes_text.grid(row=3, column=1, padx=(10, 0), pady=5)
        
        # Butonlar
        button_frame = ttk.Frame(form_frame)
        button_frame.grid(row=4, column=0, columnspan=2, pady=20)
        
        add_btn = ttk.Button(button_frame, text="✅ Etkinliği Kaydet", 
                           command=self.add_activity, style='Accent.TButton')
        add_btn.pack(side='left', padx=5)
        
        clear_btn = ttk.Button(button_frame, text="🗑️ Temizle", 
                             command=self.clear_form)
        clear_btn.pack(side='left', padx=5)
        
        # Günlük özet
        self.daily_summary_label = tk.Label(input_frame, text="", 
                                          font=('Arial', 12), bg='#f0f0f0', fg='#2E8B57')
        self.daily_summary_label.pack(pady=10)
    
    def create_records_tab(self):
        """Kayıtlar sekmesi"""
        records_frame = ttk.Frame(self.notebook)
        self.notebook.add(records_frame, text="📋 Kayıtlar")
        
        # Arama ve filtre
        search_frame = ttk.LabelFrame(records_frame, text="🔍 Arama ve Filtre", padding="10")
        search_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Label(search_frame, text="Etkinlik Ara:").pack(side='left')
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=30)
        search_entry.pack(side='left', padx=5)
        search_entry.bind('<KeyRelease>', lambda e: self.filter_records())
        
        ttk.Button(search_frame, text="🔄 Yenile", 
                  command=self.refresh_records).pack(side='right', padx=5)
        
        # Treeview için frame
        tree_frame = ttk.Frame(records_frame)
        tree_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Treeview oluştur
        columns = ('ID', 'Tarih', 'Etkinlik', 'Süre (dk)', 'Notlar')
        self.records_tree = ttk.Treeview(tree_frame, columns=columns, show='headings', height=20)
        
        # Başlıkları ayarla
        for col in columns:
            self.records_tree.heading(col, text=col)
            self.records_tree.column(col, width=150)
        
        # Scrollbar ekle
        scrollbar = ttk.Scrollbar(tree_frame, orient='vertical', command=self.records_tree.yview)
        self.records_tree.configure(yscrollcommand=scrollbar.set)
        
        self.records_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # Kayıt işlemleri butonları
        buttons_frame = ttk.Frame(records_frame)
        buttons_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Button(buttons_frame, text="✏️ Düzenle", 
                  command=self.edit_record).pack(side='left', padx=5)
        ttk.Button(buttons_frame, text="🗑️ Sil", 
                  command=self.delete_record).pack(side='left', padx=5)
        ttk.Button(buttons_frame, text="📤 CSV Dışa Aktar", 
                  command=self.export_csv).pack(side='right', padx=5)
    
    def create_reports_tab(self):
        """Raporlar sekmesi"""
        reports_frame = ttk.Frame(self.notebook)
        self.notebook.add(reports_frame, text="📊 Raporlar")
        
        # Filtre seçenekleri
        filter_frame = ttk.LabelFrame(reports_frame, text="📅 Rapor Dönemi", padding="10")
        filter_frame.pack(fill='x', padx=10, pady=5)
        
        self.report_period = tk.StringVar(value="Bu Ay")
        periods = ["Son 7 Gün", "Bu Ay", "Son 30 Gün", "Tüm Zamanlar"]
        
        for period in periods:
            ttk.Radiobutton(filter_frame, text=period, variable=self.report_period, 
                           value=period, command=self.generate_report).pack(side='left', padx=10)
        
        # Rapor içeriği
        self.report_text = tk.Text(reports_frame, wrap='word', height=25, font=('Courier', 11))
        self.report_text.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Rapor butonları
        report_buttons_frame = ttk.Frame(reports_frame)
        report_buttons_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Button(report_buttons_frame, text="📋 Panoya Kopyala", 
                  command=self.copy_to_clipboard).pack(side='left', padx=5)
        ttk.Button(report_buttons_frame, text="💾 PDF Kaydet", 
                  command=self.save_as_pdf).pack(side='left', padx=5)
        ttk.Button(report_buttons_frame, text="🔄 Raporu Yenile", 
                  command=self.generate_report).pack(side='right', padx=5)
    
    def create_charts_tab(self):
        """Grafikler sekmesi"""
        charts_frame = ttk.Frame(self.notebook)
        self.notebook.add(charts_frame, text="📈 Grafikler")
        
        # Grafik türü seçimi
        chart_control_frame = ttk.LabelFrame(charts_frame, text="📊 Grafik Türü", padding="10")
        chart_control_frame.pack(fill='x', padx=10, pady=5)
        
        self.chart_type = tk.StringVar(value="line")
        ttk.Radiobutton(chart_control_frame, text="📈 Çizgi Grafik (Son 30 Gün)", 
                       variable=self.chart_type, value="line", 
                       command=self.update_chart).pack(side='left', padx=10)
        ttk.Radiobutton(chart_control_frame, text="🥧 Pasta Grafik (Etkinlik Dağılımı)", 
                       variable=self.chart_type, value="pie", 
                       command=self.update_chart).pack(side='left', padx=10)
        
        # Grafik alanı
        self.chart_frame = ttk.Frame(charts_frame)
        self.chart_frame.pack(fill='both', expand=True, padx=10, pady=5)
    
    def create_settings_tab(self):
        """Ayarlar sekmesi"""
        settings_frame = ttk.Frame(self.notebook)
        self.notebook.add(settings_frame, text="⚙️ Ayarlar")
        
        # Yedekleme bölümü
        backup_frame = ttk.LabelFrame(settings_frame, text="💾 Yedekleme ve Geri Yükleme", padding="20")
        backup_frame.pack(fill='x', padx=20, pady=10)
        
        ttk.Button(backup_frame, text="📤 Veritabanını Yedekle", 
                  command=self.backup_database).pack(side='left', padx=5)
        ttk.Button(backup_frame, text="📥 Yedeği Geri Yükle", 
                  command=self.restore_database).pack(side='left', padx=5)
        
        # Parola değiştirme
        password_frame = ttk.LabelFrame(settings_frame, text="🔒 Güvenlik", padding="20")
        password_frame.pack(fill='x', padx=20, pady=10)
        
        ttk.Button(password_frame, text="🔑 Parolayı Değiştir", 
                  command=self.change_password).pack(side='left', padx=5)
        
        # İstatistikler
        stats_frame = ttk.LabelFrame(settings_frame, text="📊 Genel İstatistikler", padding="20")
        stats_frame.pack(fill='x', padx=20, pady=10)
        
        self.stats_label = tk.Label(stats_frame, text="", justify='left', font=('Arial', 10))
        self.stats_label.pack()
        
        self.update_stats()
    
    def load_activity_suggestions(self):
        """Önceki etkinliklerden öneriler yükle"""
        self.cursor.execute("SELECT DISTINCT activity FROM activities ORDER BY activity")
        activities = [row[0] for row in self.cursor.fetchall()]
        self.activity_combo['values'] = activities
    
    def add_activity(self):
        """Yeni etkinlik ekle"""
        if not self.activity_var.get() or not self.duration_var.get():
            messagebox.showwarning("⚠️ Uyarı", "Etkinlik adı ve süre alanları zorunludur!")
            return
        
        try:
            self.cursor.execute('''
                INSERT INTO activities (date, activity, duration, notes)
                VALUES (?, ?, ?, ?)
            ''', (self.date_var.get(), self.activity_var.get(), 
                  self.duration_var.get(), self.notes_text.get('1.0', 'end-1c')))
            
            self.conn.commit()
            messagebox.showinfo("✅ Başarılı", "Etkinlik başarıyla kaydedildi!")
            
            self.clear_form()
            self.refresh_data()
            self.load_activity_suggestions()
            
        except Exception as e:
            messagebox.showerror("❌ Hata", f"Kayıt sırasında hata oluştu: {str(e)}")
    
    def clear_form(self):
        """Formu temizle"""
        self.date_var.set(datetime.date.today().strftime('%Y-%m-%d'))
        self.activity_var.set("")
        self.duration_var.set(0)
        self.notes_text.delete('1.0', 'end')
        self.update_daily_summary()
    
    def update_daily_summary(self):
        """Günlük özeti güncelle"""
        today = datetime.date.today().strftime('%Y-%m-%d')
        self.cursor.execute("SELECT SUM(duration) FROM activities WHERE date = ?", (today,))
        total = self.cursor.fetchone()[0] or 0
        
        hours = total // 60
        minutes = total % 60
        self.daily_summary_label.config(text=f"📊 Bugünkü Toplam: {hours}s {minutes}dk")
    
    def refresh_data(self):
        """Tüm verileri yenile"""
        self.refresh_records()
        self.update_daily_summary()
        self.generate_report()
        self.update_chart()
        self.update_stats()
    
    def refresh_records(self):
        """Kayıtları yenile"""
        for item in self.records_tree.get_children():
            self.records_tree.delete(item)
        
        query = "SELECT id, date, activity, duration, notes FROM activities ORDER BY date DESC, id DESC"
        params = []
        
        if self.search_var.get():
            query = "SELECT id, date, activity, duration, notes FROM activities WHERE activity LIKE ? ORDER BY date DESC, id DESC"
            params = [f"%{self.search_var.get()}%"]
        
        self.cursor.execute(query, params)
        for row in self.cursor.fetchall():
            self.records_tree.insert('', 'end', values=row)
    
    def filter_records(self):
        """Kayıtları filtrele"""
        self.refresh_records()
    
    def edit_record(self):
        """Seçili kaydı düzenle"""
        selected = self.records_tree.selection()
        if not selected:
            messagebox.showwarning("⚠️ Uyarı", "Düzenlemek için bir kayıt seçin!")
            return
        
        item = self.records_tree.item(selected[0])
        record_id, date, activity, duration, notes = item['values']
        
        # Düzenleme penceresi
        edit_window = tk.Toplevel(self.root)
        edit_window.title("✏️ Kayıt Düzenle")
        edit_window.geometry("400x300")
        
        # Form alanları
        ttk.Label(edit_window, text="Tarih:").grid(row=0, column=0, sticky='w', padx=10, pady=5)
        date_var = tk.StringVar(value=date)
        ttk.Entry(edit_window, textvariable=date_var).grid(row=0, column=1, padx=10, pady=5)
        
        ttk.Label(edit_window, text="Etkinlik:").grid(row=1, column=0, sticky='w', padx=10, pady=5)
        activity_var = tk.StringVar(value=activity)
        ttk.Entry(edit_window, textvariable=activity_var).grid(row=1, column=1, padx=10, pady=5)
        
        ttk.Label(edit_window, text="Süre (dk):").grid(row=2, column=0, sticky='w', padx=10, pady=5)
        duration_var = tk.IntVar(value=duration)
        ttk.Entry(edit_window, textvariable=duration_var).grid(row=2, column=1, padx=10, pady=5)
        
        ttk.Label(edit_window, text="Notlar:").grid(row=3, column=0, sticky='nw', padx=10, pady=5)
        notes_text = tk.Text(edit_window, width=30, height=5)
        notes_text.grid(row=3, column=1, padx=10, pady=5)
        notes_text.insert('1.0', notes)
        
        def save_changes():
            try:
                self.cursor.execute('''
                    UPDATE activities SET date=?, activity=?, duration=?, notes=?
                    WHERE id=?
                ''', (date_var.get(), activity_var.get(), duration_var.get(),
                      notes_text.get('1.0', 'end-1c'), record_id))
                
                self.conn.commit()
                messagebox.showinfo("✅ Başarılı", "Kayıt güncellendi!")
                edit_window.destroy()
                self.refresh_data()
                
            except Exception as e:
                messagebox.showerror("❌ Hata", f"Güncelleme hatası: {str(e)}")
        
        ttk.Button(edit_window, text="💾 Kaydet", command=save_changes).grid(row=4, column=1, pady=20)
    
    def delete_record(self):
        """Seçili kaydı sil"""
        selected = self.records_tree.selection()
        if not selected:
            messagebox.showwarning("⚠️ Uyarı", "Silmek için bir kayıt seçin!")
            return
        
        if messagebox.askyesno("🗑️ Silme Onayı", "Bu kaydı silmek istediğinizden emin misiniz?"):
            item = self.records_tree.item(selected[0])
            record_id = item['values'][0]
            
            self.cursor.execute("DELETE FROM activities WHERE id=?", (record_id,))
            self.conn.commit()
            
            messagebox.showinfo("✅ Başarılı", "Kayıt silindi!")
            self.refresh_data()
    
    def export_csv(self):
        """Kayıtları CSV olarak dışa aktar"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
            title="CSV Dosyasını Kaydet"
        )
        
        if filename:
            try:
                self.cursor.execute("SELECT date, activity, duration, notes FROM activities ORDER BY date DESC")
                data = self.cursor.fetchall()
                
                df = pd.DataFrame(data, columns=['Tarih', 'Etkinlik', 'Süre (dk)', 'Notlar'])
                df.to_csv(filename, index=False, encoding='utf-8-sig')
                
                messagebox.showinfo("✅ Başarılı", f"Veriler {filename} dosyasına aktarıldı!")
                
            except Exception as e:
                messagebox.showerror("❌ Hata", f"Dışa aktarma hatası: {str(e)}")
    
    def generate_report(self):
        """Rapor oluştur"""
        period = self.report_period.get()
        
        # Tarih aralığını belirle
        today = datetime.date.today()
        if period == "Son 7 Gün":
            start_date = today - timedelta(days=7)
        elif period == "Bu Ay":
            start_date = today.replace(day=1)
        elif period == "Son 30 Gün":
            start_date = today - timedelta(days=30)
        else:  # Tüm Zamanlar
            start_date = datetime.date(2000, 1, 1)
        
        # Veri çek
        self.cursor.execute('''
            SELECT activity, SUM(duration) as total_duration, COUNT(*) as count
            FROM activities 
            WHERE date >= ? 
            GROUP BY activity 
            ORDER BY total_duration DESC
        ''', (start_date.strftime('%Y-%m-%d'),))
        
        activities_data = self.cursor.fetchall()
        
        # Rapor metni oluştur
        report = f"📊 {period} Aktivite Raporu\n"
        report += "=" * 50 + "\n\n"
        
        if not activities_data:
            report += "Bu dönemde hiç etkinlik kaydı bulunamadı.\n"
        else:
            total_time = sum([row[1] for row in activities_data])
            total_days = (today - start_date).days + 1
            
            report += f"📅 Rapor Dönemi: {start_date.strftime('%d.%m.%Y')} - {today.strftime('%d.%m.%Y')}\n"
            report += f"📊 Toplam Süre: {total_time//60}s {total_time%60}dk\n"
            report += f"📈 Günlük Ortalama: {total_time//total_days//60}s {(total_time//total_days)%60}dk\n"
            report += f"🎯 Toplam Etkinlik Türü: {len(activities_data)}\n\n"
            
            report += "🏆 Etkinlik Detayları:\n"
            report += "-" * 30 + "\n"
            
            for i, (activity, duration, count) in enumerate(activities_data, 1):
                percentage = (duration / total_time) * 100
                avg_session = duration / count
                report += f"{i:2d}. {activity}\n"
                report += f"    ⏱️  Toplam: {duration//60}s {duration%60}dk ({percentage:.1f}%)\n"
                report += f"    📊 Oturum: {count} kez\n"
                report += f"    📈 Ortalama: {avg_session//60:.0f}s {avg_session%60:.0f}dk\n\n"
        
        report += f"\n📝 Rapor Tarihi: {datetime.datetime.now().strftime('%d.%m.%Y %H:%M')}\n"
        
        # Raporu göster
        self.report_text.delete('1.0', 'end')
        self.report_text.insert('1.0', report)
    
    def copy_to_clipboard(self):
        """Raporu panoya kopyala"""
        report_content = self.report_text.get('1.0', 'end-1c')
        self.root.clipboard_clear()
        self.root.clipboard_append(report_content)
        messagebox.showinfo("✅ Başarılı", "Rapor panoya kopyalandı!")
    
    def save_as_pdf(self):
        """Raporu PDF olarak kaydet (basit metin dosyası)"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt")],
            title="Raporu Kaydet"
        )
        
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(self.report_text.get('1.0', 'end-1c'))
                messagebox.showinfo("✅ Başarılı", f"Rapor {filename} dosyasına kaydedildi!")
            except Exception as e:
                messagebox.showerror("❌ Hata", f"Kaydetme hatası: {str(e)}")
    
    def update_chart(self):
        """Grafikleri güncelle"""
        # Önceki grafikleri temizle
        for widget in self.chart_frame.winfo_children():
            widget.destroy()
        
        try:
            if self.chart_type.get() == "line":
                self.create_line_chart()
            else:
                self.create_pie_chart()
        except Exception as e:
            error_label = tk.Label(self.chart_frame, text=f"Grafik yüklenirken hata: {str(e)}")
            error_label.pack()
    
    def create_line_chart(self):
        """Son 30 günün çizgi grafiği"""
        end_date = datetime.date.today()
        start_date = end_date - timedelta(days=29)
        
        # Günlük toplam süreleri al
        self.cursor.execute('''
            SELECT date, SUM(duration) 
            FROM activities 
            WHERE date >= ? AND date <= ?
            GROUP BY date
            ORDER BY date
        ''', (start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')))
        
        data = dict(self.cursor.fetchall())
        
        # Tüm günleri dahil et (boş günler için 0)
        dates = []
        durations = []
        current_date = start_date
        
        while current_date <= end_date:
            dates.append(current_date)
            durations.append(data.get(current_date.strftime('%Y-%m-%d'), 0))
            current_date += timedelta(days=1)
        
        # Grafik oluştur
        fig, ax = plt.subplots(figsize=(12, 6))
        ax.plot(dates, durations, marker='o', linewidth=2, markersize=4)
        ax.set_title('📈 Son 30 Günün Aktivite Süresi', fontsize=14, fontweight='bold')
        ax.set_xlabel('Tarih')
        ax.set_ylabel('Süre (dakika)')
        ax.grid(True, alpha=0.3)
        
        # Tarihleri döndür
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
        plt.tight_layout()
        
        # Tkinter'a entegre et
        canvas = FigureCanvasTkAgg(fig, self.chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill='both', expand=True)
    
    def create_pie_chart(self):
        """Etkinlik dağılımının pasta grafiği"""
        # Son 30 günün verilerini al
        end_date = datetime.date.today()
        start_date = end_date - timedelta(days=29)
        
        self.cursor.execute('''
            SELECT activity, SUM(duration) 
            FROM activities 
            WHERE date >= ? AND date <= ?
            GROUP BY activity
            ORDER BY SUM(duration) DESC
        ''', (start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')))
        
        data = self.cursor.fetchall()
        
        if not data:
            no_data_label = tk.Label(self.chart_frame, text="📊 Son 30 günde veri bulunamadı", 
                                   font=('Arial', 12))
            no_data_label.pack(expand=True)
            return
        
        activities = [row[0] for row in data]
        durations = [row[1] for row in data]
        
        # En fazla 8 etkinlik göster, diğerlerini "Diğer" olarak grupla
        if len(activities) > 8:
            other_duration = sum(durations[8:])
            activities = activities[:8] + ['Diğer']
            durations = durations[:8] + [other_duration]
        
        # Grafik oluştur
        fig, ax = plt.subplots(figsize=(10, 8))
        colors = plt.cm.Set3(range(len(activities)))
        
        wedges, texts, autotexts = ax.pie(durations, labels=activities, autopct='%1.1f%%',
                                         colors=colors, startangle=90)
        
        ax.set_title('🥧 Son 30 Günün Etkinlik Dağılımı', fontsize=14, fontweight='bold')
        
        # Güzel görünsün diye ayarlamalar
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')
        
        plt.tight_layout()
        
        # Tkinter'a entegre et
        canvas = FigureCanvasTkAgg(fig, self.chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill='both', expand=True)
    
    def backup_database(self):
        """Veritabanını yedekle"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".db",
            filetypes=[("Database files", "*.db"), ("All files", "*.*")],
            title="Veritabanı Yedeğini Kaydet"
        )
        
        if filename:
            try:
                import shutil
                shutil.copy2('activities.db', filename)
                messagebox.showinfo("✅ Başarılı", f"Veritabanı {filename} dosyasına yedeklendi!")
            except Exception as e:
                messagebox.showerror("❌ Hata", f"Yedekleme hatası: {str(e)}")
    
    def restore_database(self):
        """Veritabanını geri yükle"""
        if messagebox.askyesno("⚠️ Uyarı", 
                              "Mevcut veriler silinecek! Devam etmek istediğinizden emin misiniz?"):
            filename = filedialog.askopenfilename(
                filetypes=[("Database files", "*.db"), ("All files", "*.*")],
                title="Yedek Dosyasını Seç"
            )
            
            if filename:
                try:
                    import shutil
                    self.conn.close()
                    shutil.copy2(filename, 'activities.db')
                    self.conn = sqlite3.connect('activities.db')
                    self.cursor = self.conn.cursor()
                    messagebox.showinfo("✅ Başarılı", "Veritabanı geri yüklendi!")
                    self.refresh_data()
                except Exception as e:
                    messagebox.showerror("❌ Hata", f"Geri yükleme hatası: {str(e)}")
    
    def change_password(self):
        """Parolayı değiştir"""
        old_password = simpledialog.askstring("🔐 Eski Parola", 
                                             "Mevcut parolanızı girin:", show='*')
        if not old_password:
            return
        
        # Eski parolayı kontrol et
        self.cursor.execute("SELECT value FROM settings WHERE key = 'password'")
        stored_password = self.cursor.fetchone()[0]
        old_hashed = hashlib.sha256(old_password.encode()).hexdigest()
        
        if old_hashed != stored_password:
            messagebox.showerror("❌ Hata", "Mevcut parola yanlış!")
            return
        
        new_password = simpledialog.askstring("🔑 Yeni Parola", 
                                            "Yeni parolanızı girin:", show='*')
        if new_password:
            confirm_password = simpledialog.askstring("🔑 Parola Onayı", 
                                                     "Yeni parolanızı tekrar girin:", show='*')
            if new_password == confirm_password:
                new_hashed = hashlib.sha256(new_password.encode()).hexdigest()
                self.cursor.execute("UPDATE settings SET value = ? WHERE key = 'password'", 
                                  (new_hashed,))
                self.conn.commit()
                messagebox.showinfo("✅ Başarılı", "Parola başarıyla değiştirildi!")
            else:
                messagebox.showerror("❌ Hata", "Parolalar eşleşmiyor!")
    
    def update_stats(self):
        """Genel istatistikleri güncelle"""
        try:
            # Toplam kayıt sayısı
            self.cursor.execute("SELECT COUNT(*) FROM activities")
            total_records = self.cursor.fetchone()[0]
            
            # Toplam süre
            self.cursor.execute("SELECT SUM(duration) FROM activities")
            total_duration = self.cursor.fetchone()[0] or 0
            
            # Farklı etkinlik sayısı
            self.cursor.execute("SELECT COUNT(DISTINCT activity) FROM activities")
            unique_activities = self.cursor.fetchone()[0]
            
            # İlk kayıt tarihi
            self.cursor.execute("SELECT MIN(date) FROM activities")
            first_record = self.cursor.fetchone()[0]
            
            # En aktif gün
            self.cursor.execute('''
                SELECT date, SUM(duration) as daily_total 
                FROM activities 
                GROUP BY date 
                ORDER BY daily_total DESC 
                LIMIT 1
            ''')
            most_active_day = self.cursor.fetchone()
            
            stats_text = f"📊 Toplam Kayıt: {total_records}\n"
            stats_text += f"⏱️ Toplam Süre: {total_duration//60}s {total_duration%60}dk\n"
            stats_text += f"🎯 Farklı Etkinlik: {unique_activities}\n"
            
            if first_record:
                stats_text += f"📅 İlk Kayıt: {first_record}\n"
            
            if most_active_day:
                date, duration = most_active_day
                stats_text += f"🏆 En Aktif Gün: {date} ({duration//60}s {duration%60}dk)\n"
            
            # Ortalama günlük süre
            if first_record:
                from datetime import datetime
                first_date = datetime.strptime(first_record, '%Y-%m-%d').date()
                days_diff = (datetime.now().date() - first_date).days + 1
                avg_daily = total_duration / days_diff if days_diff > 0 else 0
                stats_text += f"📈 Günlük Ortalama: {avg_daily//60:.0f}s {avg_daily%60:.0f}dk"
            
            self.stats_label.config(text=stats_text)
            
        except Exception as e:
            self.stats_label.config(text=f"İstatistik hatası: {str(e)}")
    
    def __del__(self):
        """Uygulama kapanırken veritabanı bağlantısını kapat"""
        if hasattr(self, 'conn'):
            self.conn.close()
    
    def run(self):
        """Uygulamayı çalıştır"""
        # Otomatik yedekleme (günde bir)
        self.auto_backup()
        
        # Uygulama kapanırken temizlik
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        self.root.mainloop()
    
    def auto_backup(self):
        """Otomatik yedekleme yap"""
        try:
            backup_dir = "backups"
            if not os.path.exists(backup_dir):
                os.makedirs(backup_dir)
            
            today = datetime.date.today().strftime('%Y%m%d')
            backup_file = os.path.join(backup_dir, f"activities_backup_{today}.db")
            
            # Eğer bugünün yedeği yoksa oluştur
            if not os.path.exists(backup_file):
                import shutil
                shutil.copy2('activities.db', backup_file)
                
                # Eski yedekleri temizle (30 günden eski)
                self.cleanup_old_backups(backup_dir)
                
        except Exception as e:
            pass  # Sessizce başarısız ol
    
    def cleanup_old_backups(self, backup_dir):
        """30 günden eski yedekleri sil"""
        try:
            cutoff_date = datetime.date.today() - timedelta(days=30)
            
            for filename in os.listdir(backup_dir):
                if filename.startswith("activities_backup_") and filename.endswith(".db"):
                    try:
                        date_str = filename.replace("activities_backup_", "").replace(".db", "")
                        file_date = datetime.datetime.strptime(date_str, '%Y%m%d').date()
                        
                        if file_date < cutoff_date:
                            os.remove(os.path.join(backup_dir, filename))
                    except:
                        continue
                        
        except Exception as e:
            pass
    
    def on_closing(self):
        """Uygulama kapatılırken çalışır"""
        try:
            self.conn.close()
        except:
            pass
        self.root.destroy()

# Uygulamayı başlat
if __name__ == "__main__":
    try:
        app = ActivityTracker()
        app.run()
    except Exception as e:
        print(f"Uygulama başlatma hatası: {str(e)}")
        input("Devam etmek için Enter'a basın...")