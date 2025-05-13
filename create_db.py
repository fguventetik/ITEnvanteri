import sqlite3

# Veritabanı dosyasını oluştur
conn = sqlite3.connect("C:/Users/Firdevs/Desktop/envanter/envanter.db")
cursor = conn.cursor()

# Bilgisayar tablosunu oluştur
cursor.execute("""
CREATE TABLE IF NOT EXISTS bilgisayarlar (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    proje TEXT,
    mac_adresi TEXT,
    ekipman_kodu TEXT,
    tip TEXT,
    marka TEXT,
    model TEXT,
    cpu TEXT,
    cpu_hizi TEXT,
    ram INTEGER,
    ram_hizi TEXT,
    disk TEXT,
    ekran_karti TEXT,
    monitor TEXT,
    ethernet TEXT,
    optik_surucu TEXT,
    windows_lisans TEXT,
    isletim_sistemi TEXT,
    office_seri TEXT,
    cad_seri TEXT,
    ek_donanim TEXT,
    durum TEXT,
    kullanici TEXT,
    departman TEXT,
    zimmet_tarihi TEXT,
    garanti_suresi TEXT,
    garanti_bitis TEXT,
    kullanim_suresi TEXT,
    logon_password TEXT,
    aciklama TEXT
)
""")

conn.commit()
conn.close()

print("✅ Veritabanı ve tablo başarıyla oluşturuldu!")
