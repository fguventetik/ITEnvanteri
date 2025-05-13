# create_admin_user.py
import sqlite3
import os
# Şifre hashleme fonksiyonları için werkzeug.security kütüphanesini kullanıyoruz
from werkzeug.security import generate_password_hash, check_password_hash # pip install Werkzeug

# app.py dosyanızdaki gibi veritabanı yolunu belirleyin
basedir = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(basedir, "envanter.db")

def add_admin_user(username, password):
    conn = None
    try:
        # Veritabanına bağlan
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Kullanıcının zaten var olup olmadığını kontrol et
        cursor.execute("SELECT id FROM kullanicilar WHERE ad = ?", (username,))
        existing_user = cursor.fetchone()

        if existing_user:
            print(f"'{username}' kullanıcısı zaten mevcut.")
            # İsterseniz burada mevcut kullanıcının şifresini veya admin durumunu güncelleyebilirsiniz
            cursor.execute("UPDATE kullanicilar SET is_admin = ? WHERE id = ?", (True, existing_user[0]))
            conn.commit()
            print(f"'{username}' kullanıcısının admin durumu True olarak güncellendi.")
        else:
            # Kullanıcı yoksa, şifreyi hashle
            hashed_password = generate_password_hash(password)

            # Yeni admin kullanıcısını veritabanına ekle
            cursor.execute("INSERT INTO kullanicilar (ad, password, is_admin) VALUES (?, ?, ?)", (username, hashed_password, True))
            conn.commit()
            print(f"'{username}' adında yeni bir admin kullanıcısı başarıyla eklendi.")

    except FileNotFoundError:
        print(f"Hata: Veritabanı dosyası bulunamadı: {db_path}")
        print("Lütfen önce app.py'yi bir kez çalıştırarak veritabanını oluşturun veya yolu kontrol edin.")
    except sqlite3.IntegrityError as e:
        print(f"Veritabanı hatası (IntegrityError): {e}")
        print(f"'{username}' kullanıcısı zaten mevcut.")
        if conn:
            conn.rollback()
    except ImportError:
        # Werkzeug kurulu değilse bu hata yakalanır ve bilgilendirme mesajı basılır
        print("Hata: 'Werkzeug' kütüphanesi kurulu değil.")
        print("Lütfen terminalde 'pip install Werkzeug' komutu ile kurun.")
    except Exception as e:
        print(f"Bir hata oluştu: {e}")

    finally:
        if conn:
            conn.close()

# Betiği doğrudan Python ile çalıştırdığınızda aşağıdaki kod çalışır
if __name__ == "__main__":
    # --- BURAYI DÜZENLEYİN ---
    # Eklemek istediğiniz admin kullanıcı adını ve şifresini buraya yazın.
    # Şifrenin GÜÇLÜ ve SİZE ÖZEL olduğundan emin olun.
    # '123456' SADECE BİR ÖRNEKTİR, BUNU KULLANMAYIN!
    admin_username = 'Admin' # İstediğiniz kullanıcı adını yazabilirsiniz
    admin_password = '123456' # BURAYI KESİNLİKLE GÜÇLÜ BİR ŞİFRE İLE DEĞİŞTİRİN!

    print(f"'{admin_username}' kullanıcısını admin olarak eklemeye çalışılıyor...")
    add_admin_user(admin_username, admin_password)