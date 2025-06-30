# 📊 Günlük Aktivite Takip Uygulaması | Daily Activity Tracker (Python + Tkinter)

## 📌 Açıklama | Description

**TR:**  
Bu masaüstü uygulaması, günlük aktivitelerinizi kaydetmenizi, analiz etmenizi ve grafiklerle görselleştirmenizi sağlar. Python'un Tkinter kütüphanesi ile tasarlanmış, SQLite veritabanı kullanan yerel bir üretkenlik uygulamasıdır.

**EN:**  
This desktop app lets you track, analyze, and visualize your daily activities using charts and reports. Built with Python Tkinter and SQLite, it's a personal productivity tool that runs locally on your computer.

---

## 🎯 Özellikler | Features

- 📝 Etkinlik ekleme (tarih, süre, açıklama) | Add activities with date, duration, and notes  
- 🔐 Parola korumalı giriş | Password-protected login (SHA-256)  
- 📋 Kayıt görüntüleme, düzenleme, silme | View, edit, delete entries  
- 📤 CSV dışa aktarım | Export data to CSV  
- 📊 Otomatik rapor üretimi | Auto-generated activity reports  
- 📈 Grafikler (Çizgi & Pasta) | Line and pie charts  
- 💾 Yedekleme & geri yükleme | Backup & restore database  
- 🧮 Günlük toplam/ortalama istatistik | Daily total and average stats  
- 🔁 Otomatik günlük yedekleme | Daily auto-backup system

---

## ⚙️ Gereksinimler | Requirements

- Python 3.7+  
- Kurulması gereken kütüphaneler | Install with:

```bash
pip install matplotlib pandas
```

---

## 🚀 Kullanım | Usage

```bash
python app.py
```

İlk kullanımda parola belirlemeniz istenir. Sonraki girişlerde aynı parola ile oturum açılır.  
You’ll be prompted to set a password on first use. Use it to login next time.

---

## 🧠 Veritabanı Bilgisi | Database Info

- Yerel dosya: `activities.db`  
- Otomatik yedekler: `/backups/activities_backup_YYYYMMDD.db`

---

## 📤 Raporlama | Reporting

- 📄 Metin tabanlı raporlar `.txt` olarak kaydedilebilir  
- 📊 Grafikler son 30 günü temel alır (çizgi ve pasta grafik)  
- 📋 CSV dışa aktarım mevcuttur

---

## 🛡️ Güvenlik | Security

- SHA-256 şifrelenmiş parola  
- Parola değiştirme imkanı  
- Yetkisiz erişime karşı güvenlik kontrolleri

---

## 📌 Geliştirici Notu | Developer Note

**TR:**  
Uygulama tamamen yereldir. Verileriniz size aittir. Geliştirmeye açıktır.  
**EN:**  
App is fully local. Your data stays with you. Open for customization and improvements.

---