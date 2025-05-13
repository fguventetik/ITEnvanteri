# -*- coding: utf-8 -*-

import os
import sqlite3
from flask import Flask, render_template, request, redirect, jsonify, flash, session, url_for
import json

# Flask-Login için gerekli importlar
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
# Şifre hashing için gerekli importlar
from werkzeug.security import generate_password_hash, check_password_hash


app = Flask(__name__)
# Güvenlik için burayı GERÇEK, GÜÇLÜ ve Rastgele bir anahtarla DEĞİŞTİRİN!
# Bu anahtar oturum yönetimi, flash mesajları ve Flask-Login için kullanılır.
app.secret_key = "buraya_cok_gizli_bir_anahtar_gelecek_kimse_tahmin_edemez_12345_randomstring"

# Flask-Login konfigürasyonu
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login' # Giriş sayfası route'unuzun adı
login_manager.login_message = 'Bu sayfaya erişmek için lütfen giriş yapın.'
login_manager.login_message_category = 'warning'


basedir = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(basedir, "envanter.db")


# --- Kullanıcı Modeli (Flask-Login ile uyumlu) ---
# Kullanicilar tablosuna karşılık gelen sınıf.
# Flask-Login'in UserMixin'inden miras alır.
class User(UserMixin):
    def __init__(self, id, ad, password, is_admin=False):
        self.id = id
        self.ad = ad
        self.password = password # Hashlenmiş şifre
        # Veritabanındaki is_admin değeri 0 veya 1 olabilir, Python'da True/False'a çevir
        self.is_admin = bool(is_admin)

    # Flask-Login'in ihtiyaç duyduğu metot
    def get_id(self):
        return str(self.id)

    # is_active, is_authenticated, is_anonymous UserMixin tarafından sağlanır.
    # İhtiyaç olursa geçersiz kılınabilir (override).
    # Örneğin, is_active kullanıcı hesabının aktif olup olmadığını kontrol edebilir.
    # is_authenticated kullanıcının kimliğinin doğrulandığını belirtir (genellikle login sonrası True olur)
    # is_anonymous kullanıcının anonim (giriş yapmamış) olup olmadığını belirtir.


# --- Flask-Login Kullanıcı Yükleyici Fonksiyonu ---
# Flask-Login, oturumdaki kullanıcı ID'sini kullanarak bu fonksiyonu çağırır
# ve User objesini döndürmesini bekler.
@login_manager.user_loader
def load_user(user_id):
    conn = get_db_connection()
    if conn is None:
        return None # Veritabanı bağlantısı yoksa kullanıcı yüklenemez

    # Veritabanından kullanıcıyı ID'ye göre çek
    user_data = conn.execute("SELECT id, ad, password, is_admin FROM kullanicilar WHERE id = ?", (user_id,)).fetchone()
    conn.close()

    if user_data:
        # User objesi oluştur ve döndür
        return User(user_data['id'], user_data['ad'], user_data['password'], user_data['is_admin'])
    return None # Kullanıcı bulunamazsa None döndür


# Veritabanı başlatma fonksiyonu
def init_db():
    conn = None
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # --- Tablo Oluşturma Sorguları ---
        # Bilgisayarlar (UNIQUE kısıtlama eklendi)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS bilgisayarlar (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bilgisayar_ekipman_kodu TEXT UNIQUE NOT NULL,
            bilgisayar_tip TEXT,
            bilgisayar_marka TEXT,
            bilgisayar_model TEXT,
            cpu TEXT,
            ram TEXT,
            disk TEXT,
            kullanici TEXT
        );
        """)

        # Monitorler (UNIQUE kısıtlama eklendi)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS monitorler (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            monitor_tipi TEXT,
            monitor_boyut TEXT,
            monitor_marka TEXT,
            monitor_model TEXT,
            seri_numarasi TEXT UNIQUE NOT NULL,
            ekipman_kodu TEXT,
            kullanici TEXT
        );
        """)

        # Yazicilar (UNIQUE kısıtlama eklendi)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS yazicilar (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            printer_marka TEXT,
            printer_model TEXT,
            printer_tipi TEXT,
            seri_numarasi TEXT UNIQUE NOT NULL,
            ekipman_kodu TEXT,
            kullanici TEXT
        );
        """)

        # Sistemler (UNIQUE kısıtlamalar eklendi)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS sistemler (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sistem_versiyon TEXT,
            lisans_no TEXT UNIQUE NOT NULL,
            lisans_key TEXT UNIQUE,
            ekipman_kodu TEXT,
            kullanici TEXT
        );
        """)

        # Officeler (UNIQUE kısıtlamalar eklendi)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS officeler (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            office_versiyon TEXT,
            lisans_no TEXT UNIQUE NOT NULL,
            lisans_key TEXT UNIQUE,
            ekipman_kodu TEXT,
            kullanici TEXT
        );
        """)

        # Ayarlar için tablolar (UNIQUE kısıtlamalar eklendi)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS bilgisayar_markalari (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ad TEXT UNIQUE NOT NULL
        );
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS monitor_markalari (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ad TEXT UNIQUE NOT NULL
        );
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS monitor_boyut (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ad TEXT UNIQUE NOT NULL
        );
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS monitor_tipleri (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ad TEXT UNIQUE NOT NULL
        );
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS ms_surumler (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ad TEXT UNIQUE NOT NULL
        );
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS office_surumler (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ad TEXT UNIQUE NOT NULL
        );
        """)

        # Kullanıcı tablosu (Password ve is_admin eklendi, UNIQUE ad kısıtlaması)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS kullanicilar (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ad TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL, -- Kullanıcının hashlenmiş şifresi
            is_admin BOOLEAN DEFAULT FALSE -- Kullanıcının admin olup olmadığını belirten True/False değeri (SQLite'da 0 veya 1 saklanır)
        );
        """)

        # Eğer kullanicilar tablonuz password ve is_admin olmadan oluşturulduysa, ALTER TABLE ile ekleyin.
        # Veritabanını silip yeniden oluşturmak genellikle daha temizdir, ancak mevcut veriyi kaybedersiniz.
        # ALTER TABLE Örneği (Dikkatli Kullanın! Sütunlar zaten varsa hata verir):
        # try:
        #     conn.execute("ALTER TABLE kullanicilar ADD COLUMN password TEXT")
        #     conn.execute("ALTER TABLE kullanicilar ADD COLUMN is_admin BOOLEAN DEFAULT FALSE")
        #     conn.commit()
        #     print("Kullanicilar tablosuna password ve is_admin sütunları eklendi (varsa atlandı).")
        # except sqlite3.Error as e:
        #     # print(f"Kullanicilar tablosuna sütun eklenirken hata oluştu (muhtemelen sütunlar zaten var): {e}")
        #     pass # Hata beklenen bir durum olabilir (sütunlar zaten vardır)


        conn.commit()
        print("Veritabanı tabloları kontrol edildi/oluşturuldu.")

    except Exception as e:
        print(f"Veritabanı başlatılırken hata oluştu: {e}")
    finally:
        if conn:
            conn.close()


# Veritabanı bağlantısı alan yardımcı fonksiyon
# Tek bir bağlantı fonksiyonu kullanmak tutarlılık sağlar.
def get_db_connection():
    conn = None
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row # Sorgu sonuçlarına sütun isimleriyle erişmek için
        # conn.isolation_level = None # Auto-commit için (isteğe bağlı, dikkatli kullanın)
        return conn
    except sqlite3.Error as e:
        print(f"Veritabanı bağlantı hatası: {e}")
        return None # Bağlantı kurulamadıysa None döndür


# --- GİRİŞ (LOGIN) ROUTE'U ---
# Bu route herkese açık olmalıdır.
@app.route('/login', methods=['GET', 'POST'])
def login():
    # Eğer kullanıcı zaten giriş yapmışsa anasayfaya yönlendir
    if current_user.is_authenticated:
        return redirect(url_for('index')) # veya admin_index

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        conn = get_db_connection()
        if conn is None:
            flash("Veritabanı bağlantı hatası.", "error")
            return render_template('login.html')

        # Kullanıcıyı veritabanında adına göre bul
        user_data = conn.execute("SELECT id, ad, password, is_admin FROM kullanicilar WHERE ad = ?", (username,)).fetchone()
        conn.close()

        if user_data:
            # Kullanıcı bulundu, şimdi şifreyi doğrula
            # Kullanıcı objesi oluştur (Hasherken is_admin 0/1 dönebilir, User sınıfı bool'a çevirir)
            user = User(user_data['id'], user_data['ad'], user_data['password'], user_data['is_admin'])

            # Girilen şifreyi hashlenmiş şifre ile karşılaştır
            if check_password_hash(user.password, password):
                 # Şifre doğru, kullanıcının admin olup olmadığını kontrol et
                 if user.is_admin:
                    # Kullanıcı admin, oturumu aç (remember=True ile tarayıcı kapatılsa bile oturum kalır)
                    login_user(user, remember=False) # İsteğe bağlı: remember=True ekleyerek kalıcı oturum sağlayabilirsiniz
                    # Başarılı giriş sonrası kullanıcıyı gitmek istediği sayfaya yönlendir
                    next_page = request.args.get('next') # @login_required yönlendirmesi sonrası gelen 'next' argümanını al
                    flash(f"Hoş geldiniz, {user.ad}!", "success")
                    return redirect(next_page or url_for('index')) # next_page varsa oraya, yoksa index'e git
                 else:
                     # Kullanıcı bulundu ama admin değil
                     flash("Bu panele erişim yetkiniz yok.", "danger")
            else:
                # Şifre yanlış
                flash("Geçersiz kullanıcı adı veya şifre.", "danger")
        else:
            # Kullanıcı bulunamadı
            flash("Geçersiz kullanıcı adı veya şifre.", "danger")

    # GET isteği veya POST hatası durumunda login formunu göster
    return render_template('login.html')

# --- ÇIKIŞ (LOGOUT) ROUTE'U ---
# Giriş yapmış kullanıcılar erişebilir
@app.route('/logout')
@login_required # Sadece giriş yapmış kullanıcılar çıkış yapabilir
def logout():
    logout_user() # Kullanıcının oturumunu kapat
    flash("Başarıyla çıkış yapıldı.", "info")
    return redirect(url_for('login')) # Çıkış sonrası giriş sayfasına yönlendir

# --- ROUTE'LARI KORUMA (@login_required eklendi) ---
# Bu decorator eklenen route'lara sadece giriş yapmış kullanıcılar erişebilir.

# Ana Sayfa (Listeleme)
@app.route("/")
@login_required # Anasayfayı sadece giriş yapmış kullanıcılar görebilir
def index():
    # Kullanıcının admin olup olmadığını kontrol etmeye gerek yok, zaten @login_required ile giriş yapmış demektir.
    # Ancak sadece adminlerin görmesini istiyorsanız burada ekstra is_admin kontrolü yapabilirsiniz.
    # if not current_user.is_admin:
    #     flash("Bu sayfaya erişim yetkiniz yok.", "danger")
    #     return redirect(url_for('admin_index')) # veya başka bir yere yönlendir

    conn = get_db_connection()
    if conn is None:
        flash("Veritabanı bağlantısı kurulamadı.", "error")
        return render_template("index.html", bilgisayarlar=[], monitorler=[], yazicilar=[], sistemler=[], officeler=[])

    bilgisayarlar = conn.execute("SELECT * FROM bilgisayarlar").fetchall()
    monitorler = conn.execute("SELECT * FROM monitorler").fetchall()
    yazicilar = conn.execute("SELECT * FROM yazicilar").fetchall()
    sistemler = conn.execute("SELECT * FROM sistemler").fetchall()
    officeler = conn.execute("SELECT * FROM officeler").fetchall()
    conn.close()
    return render_template("index.html", bilgisayarlar=bilgisayarlar, monitorler=monitorler, yazicilar=yazicilar, sistemler=sistemler, officeler=officeler)

# Arama Sayfası (Eğer kullanılıyorsa)
@app.route("/ara")
@login_required # Arama sayfasını sadece giriş yapmış kullanıcılar görebilir
def ara():
    # ... (Arama mantığı - mevcut kodunuzdaki gibi) ...
    conn = get_db_connection()
    if conn is None:
         flash("Veritabanı bağlantısı kurulamadı.", "error")
         return render_template("index.html", bilgisayarlar=[], monitorler=[], yazicilar=[], sistemler=[], officeler=[])

    # Mevcut kodunuz sadece tüm veriyi çekiyor, eğer server-side arama yapacaksanız burayı değiştirmelisiniz.
    bilgisayarlar = conn.execute("SELECT * FROM bilgisayarlar").fetchall()
    monitorler = conn.execute("SELECT * FROM monitorler").fetchall()
    yazicilar = conn.execute("SELECT * FROM yazicilar").fetchall()
    sistemler = conn.execute("SELECT * FROM sistemler").fetchall()
    officeler = conn.execute("SELECT * FROM officeler").fetchall()

    conn.close()

    return render_template("index.html", # Normalde ayrı bir arama sonuç şablonu olabilir
        bilgisayarlar=bilgisayarlar,
        monitorler=monitorler,
        yazicilar=yazicilar,
        sistemler=sistemler,
        officeler=officeler
    )

# Ayarlar JSON endpoint'i
@app.route("/ayarlar.json")
@login_required # JSON endpoint'ine sadece giriş yapmış kullanıcılar erişebilir
def get_ayarlar_json():
    # ... (Mevcut kodunuzdaki gibi) ...
    try:
        conn = get_db_connection()
        if conn is None:
            return jsonify({"error": "Veritabanı bağlantısı kurulamadı."}), 500

        bilgisayar_markalari = [dict(row) for row in conn.execute("SELECT * FROM bilgisayar_markalari")]
        monitor_markalari = [dict(row) for row in conn.execute("SELECT * FROM monitor_markalari")]
        monitor_boyut = [dict(row) for row in conn.execute("SELECT * FROM monitor_boyut")]
        monitor_tipleri = [dict(row) for row in conn.execute("SELECT * FROM monitor_tipleri")]
        ms_surumler = [dict(row) for row in conn.execute("SELECT * FROM ms_surumler")]
        office_surumler = [dict(row) for row in conn.execute("SELECT * FROM office_surumler")]
        conn.close()
        return jsonify({
            "bilgisayar_markalari": bilgisayar_markalari,
            "monitor_markalari": monitor_markalari,
            "monitor_boyut": monitor_boyut,
            "monitor_tipleri": monitor_tipleri,
            "ms_surumler": ms_surumler,
            "office_surumler": office_surumler,
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Ayarlar Sayfası
@app.route("/ayarlar", methods=["GET", "POST"])
@login_required # Ayarlar sayfasına sadece giriş yapmış kullanıcılar erişebilir
# İsteğe bağlı: Sadece adminlerin ayarları değiştirmesini istiyorsanız burada ekstra is_admin kontrolü yapın.
# if not current_user.is_admin:
#     flash("Ayarları düzenleme yetkiniz yok.", "danger")
#     return redirect(url_for('index')) # veya admin_index
def ayarlar():
    # ... (Mevcut kodunuzdaki gibi) ...
    conn = get_db_connection()
    if conn is None:
        flash("Veritabanı bağlantısı kurulamadı.", "error")
        return render_template("ayarlar.html", bilgisayar_markalari=[], monitor_markalari=[], monitor_boyut=[], monitor_tipleri=[], ms_surumler=[], office_surumler=[])


    if request.method == "POST":
        tablo = request.form.get("tablo")
        deger = request.form.get("deger")

        if tablo and deger:
            try:
                # SQL Injection'a karşı dikkatli olun! İzin verilen tabloları kontrol edin.
                izin_verilen_tablolar = ["bilgisayar_markalari", "monitor_markalari", "monitor_boyut", "monitor_tipleri", "ms_surumler", "office_surumler", "kullanicilar"]
                if tablo in izin_verilen_tablolar:
                    conn.execute(f"INSERT INTO {tablo} (ad) VALUES (?)", (deger,))
                    conn.commit()
                    flash(f"'{deger}' değeri '{tablo}' tablosuna eklendi.", "success")
                else:
                    flash(f"Geçersiz tablo adı: {tablo}", "error")
            except sqlite3.IntegrityError:
                 flash(f"'{deger}' değeri zaten '{tablo}' tablosunda mevcut.", "warning")
                 conn.rollback()
            except Exception as e:
                flash(f"Ekleme sırasında hata oluştu: {str(e)}", "error")
                conn.rollback()
        else:
            flash("Tablo adı veya değer boş olamaz.", "warning")


    try:
        bilgisayar_markalari = conn.execute("SELECT * FROM bilgisayar_markalari").fetchall()
        monitor_markalari = conn.execute("SELECT * FROM monitor_markalari").fetchall()
        monitor_boyut = conn.execute("SELECT * FROM monitor_boyut").fetchall()
        monitor_tipleri = conn.execute("SELECT * FROM monitor_tipleri").fetchall()
        ms_surumler = conn.execute("SELECT * FROM ms_surumler").fetchall()
        office_surumler = conn.execute("SELECT * FROM office_surumler").fetchall()
    except Exception as e:
        flash(f"Ayarlar verileri çekilirken hata oluştu: {str(e)}", "error")
        bilgisayar_markalari, monitor_markalari, monitor_boyut, monitor_tipleri, ms_surumler, office_surumler = [], [], [], [], [], []
    finally:
         conn.close()


    return render_template("ayarlar.html",
                           bilgisayar_markalari=bilgisayar_markalari,
                           monitor_markalari=monitor_markalari,
                           monitor_boyut=monitor_boyut,
                           monitor_tipleri=monitor_tipleri,
                           ms_surumler=ms_surumler,
                           office_surumler=office_surumler)


# Genel Ekleme Route'u (Eğer admin panelinden farklı olarak kullanılacaksa)
# Eğer ekleme işlemlerini sadece admin panelinden yapacaksanız bu route'u kaldırabilirsiniz.
@app.route('/ekle', methods=['GET', 'POST'])
@login_required # Ekleme sayfasını sadece giriş yapmış kullanıcılar görebilir
def ekle():
    # ... (Mevcut kodunuzdaki gibi - POST kısmındaki bilgisayar ekleme mantığı /admin/add/bilgisayar'a taşındı) ...
    conn = get_db_connection()
    if conn is None:
         flash("Veritabanı bağlantısı kurulamadı.", "error")
         return render_template("ekle.html", bilgisayar_markalari=[], monitor_markalari=[], monitor_boyut=[], monitor_tipleri=[], ms_surumler=[], office_surumler=[])

    if request.method == 'POST':
        form = request.form
        cihaz_turu = form.get("cihaz_turu")
        flash_message = "Bir hata oluştu!"
        flash_category = "error"

        try:
            # --- BURADAKİ BİLGİSAYAR KISMI ARTIK /admin/add/bilgisayar ROUTE'UNDA DA VAR ---
            # Eğer sadece admin ekleme route'larını kullanacaksanız bu 'bilgisayar' bloğunu silebilirsiniz.
            if cihaz_turu == "bilgisayar":
                conn.execute("""
                    INSERT INTO bilgisayarlar
                    (ekipman_kodu, bilgisayar_tip, bilgisayar_marka, bilgisayar_model, cpu, ram, disk, kullanici)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    form.get("ekipman kodu"),
                    form.get("bilgisayar_tip"),
                    form.get("bilgisayar_marka"),
                    form.get("bilgisayar_model"),
                    form.get("cpu"),
                    form.get("ram"),
                    form.get("disk"),
                    form.get("kullanici")
                ))
                flash_message = "Yeni bilgisayar başarıyla eklendi (Genel Ekle)."
                flash_category = "success"

            elif cihaz_turu == "monitor":
                conn.execute("""
                    INSERT INTO monitorler
                    (monitor_tipi, monitor_boyut, monitor_marka, monitor_model, seri_numarasi, ekipman_kodu, kullanici)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    form.get("monitor_tipi"),
                    form.get("monitor_boyut"),
                    form.get("monitor_marka"),
                    form.get("monitor_model"),
                    form.get("seri_numarasi"),
                    form.get("ekipman_kodu"),
                    form.get("kullanici")
                ))
                flash_message = "Yeni monitör başarıyla eklendi!"
                flash_category = "success"

            elif cihaz_turu == "printer":
                conn.execute("""
                    INSERT INTO yazicilar
                    (printer_marka, printer_model, printer_tipi, seri_numarasi, ekipman_kodu, kullanici)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    form.get("printer_marka"),
                    form.get("printer_model"),
                    form.get("printer_tipi"),
                    form.get("seri_numarasi"),
                    form.get("ekipman_kodu"),
                    form.get("kullanici")
                ))
                flash_message = "Yeni yazıcı başarıyla eklendi!"
                flash_category = "success"

            elif cihaz_turu == "isletim_sistemi":
                conn.execute("""
                    INSERT INTO sistemler
                    (sistem_versiyon, lisans_no, lisans_key, ekipman_kodu, kullanici)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    form.get("sistem_versiyon"),
                    form.get("lisans_no"),
                    form.get("lisans_key"),
                    form.get("ekipman_kodu"),
                    form.get("kullanici")
                ))
                flash_message = "Yeni işletim sistemi lisansı başarıyla eklendi!"
                flash_category = "success"

            elif cihaz_turu == "office":
                conn.execute("""
                    INSERT INTO officeler
                    (office_versiyon, lisans_no, lisans_key, ekipman_kodu, kullanici)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    form.get("office_versiyon"),
                    form.get("lisans_no"),
                    form.get("lisans_key"),
                    form.get("ekipman_kodu"),
                    form.get("kullanici")
                ))
                flash_message = "Yeni Office lisansı başarıyla eklendi!"
                flash_category = "success"
            else:
                 flash_message = "Bilinmeyen cihaz türü!"
                 flash_category = "warning"


            conn.commit()
            flash(flash_message, flash_category)
            return redirect(url_for('index'))


        except sqlite3.IntegrityError as e:
            if "UNIQUE constraint failed" in str(e):
                flash_message = f"Bu {cihaz_turu} zaten kayıtlı! (Benzersiz kısıtlama ihlali)"
                flash_category = "error"
            else:
                flash_message = f"Veritabanı hatası: {str(e)}"
                flash_category = "error"
            flash(flash_message, flash_category)
            conn.rollback()

        except Exception as e:
            flash(f"Beklenmeyen bir hata oluştu: {str(e)}", "error")
            conn.rollback()

        finally:
            conn.close()

        # POST hatası durumunda GET formunu tekrar göstermek için gerekli verileri çek
        conn = get_db_connection()
        if conn is None:
             flash("Veritabanı bağlantısı kurulamadı.", "error")
             return render_template("ekle.html", bilgisayar_markalari=[], monitor_markalari=[], monitor_boyut=[], monitor_tipleri=[], ms_surumler=[], office_surumler=[], form_data=request.form)


        bilgisayar_markalari = conn.execute("SELECT * FROM bilgisayar_markalari").fetchall()
        monitor_markalari = conn.execute("SELECT * FROM monitor_markalari").fetchall()
        monitor_boyut = conn.execute("SELECT * FROM monitor_boyut").fetchall()
        monitor_tipleri = conn.execute("SELECT * FROM monitor_tipleri").fetchall()
        ms_surumler = conn.execute("SELECT * FROM ms_surumler").fetchall()
        office_surumler = conn.execute("SELECT * FROM office_surumler").fetchall()
        conn.close()
        return render_template("ekle.html",
                               bilgisayar_markalari=bilgisayar_markalari,
                               monitor_markalari=monitor_markalari,
                               monitor_boyut=monitor_boyut,
                               monitor_tipleri=monitor_tipleri,
                               ms_surumler=ms_surumler,
                               office_surumler=office_surumler,
                               form_data=request.form)


    # GET isteği (Formu göstermek için)
    try:
        bilgisayar_markalari = conn.execute("SELECT * FROM bilgisayar_markalari").fetchall()
        monitor_markalari = conn.execute("SELECT * FROM monitor_markalari").fetchall()
        monitor_boyut= conn.execute("SELECT * FROM monitor_boyut").fetchall()
        monitor_tipleri = conn.execute("SELECT * FROM monitor_tipleri").fetchall()
        ms_surumler = conn.execute("SELECT * FROM ms_surumler").fetchall()
        office_surumler = conn.execute("SELECT * FROM office_surumler").fetchall()
    except Exception as e:
         flash(f"Form verileri çekilirken hata oluştu: {str(e)}", "error")
         bilgisayar_markalari, monitor_markalari, monitor_boyut, monitor_tipleri, ms_surumler, office_surumler = [], [], [], [], [], []
    finally:
        conn.close()

    return render_template("ekle.html",
                           bilgisayar_markalari=bilgisayar_markalari,
                           monitor_markalari=monitor_markalari,
                           monitor_boyut=monitor_boyut,
                           monitor_tipleri=monitor_tipleri,
                           ms_surumler=ms_surumler,
                           office_surumler=office_surumler)


# Silme Route'u
@app.route('/sil/<cihaz_turu>/<int:id>', methods=['GET', 'POST'])
@login_required # Silme route'una sadece giriş yapmış kullanıcılar erişebilir
# İsteğe bağlı: Sadece adminlerin silmesini istiyorsanız burada ekstra is_admin kontrolü yapın.
# if not current_user.is_admin:
#     flash("Silme yetkiniz yok.", "danger")
#     return redirect(url_for('index')) # veya admin_index
def sil(cihaz_turu, id):
    # ... (Mevcut kodunuzdaki gibi) ...
    conn = get_db_connection()
    if conn is None:
        flash("Veritabanı bağlantısı kurulamadı.", "error")
        return redirect(url_for('index'))

    cursor = conn.cursor()
    # Silme sonrası nereye yönlendirileceği (Admin panelinde liste sayfası varsa oraya yönlendirebilirsiniz)
    redirect_url = url_for('index') # Varsayılan: Ana sayfa

    if request.method == 'POST':
        try:
            if cihaz_turu == 'bilgisayar':
                cursor.execute('DELETE FROM bilgisayarlar WHERE id = ?', (id,))
            elif cihaz_turu == 'monitor':
                cursor.execute('DELETE FROM monitorler WHERE id = ?', (id,))
            elif cihaz_turu == 'yazici':
                cursor.execute('DELETE FROM yazicilar WHERE id = ?', (id,))
            elif cihaz_turu == 'sistem':
                cursor.execute('DELETE FROM sistemler WHERE id = ?', (id,))
            elif cihaz_turu == 'office':
                cursor.execute('DELETE FROM officeler WHERE id = ?', (id,))
            else:
                flash(f"Geçersiz cihaz türü: {cihaz_turu}", "error")
                conn.close()
                return redirect(redirect_url)


            conn.commit()
            flash(f"{cihaz_turu.capitalize()} başarıyla silindi!", "success")
            return redirect(redirect_url)

        except Exception as e:
            flash(f"Silme sırasında hata oluştu: {str(e)}", "error")
            conn.rollback()
            return redirect(url_for('sil', cihaz_turu=cihaz_turu, id=id))


        finally:
            conn.close()

    elif request.method == 'GET': # GET isteği silme onay sayfasını gösterir
        veri = None
        try:
            if cihaz_turu == 'bilgisayar':
                veri = conn.execute('SELECT * FROM bilgisayarlar WHERE id = ?', (id,)).fetchone()
            elif cihaz_turu == 'monitor':
                veri = conn.execute('SELECT * FROM monitorler WHERE id = ?', (id,)).fetchone()
            elif cihaz_turu == 'yazici':
                veri = conn.execute('SELECT * FROM yazicilar WHERE id = ?', (id,)).fetchone()
            elif cihaz_turu == 'sistem':
                veri = conn.execute('SELECT * FROM sistemler WHERE id = ?', (id,)).fetchone()
            elif cihaz_turu == 'office':
                veri = conn.execute('SELECT * FROM officeler WHERE id = ?', (id,)).fetchone()
            else:
                 flash(f"Geçersiz cihaz türü: {cihaz_turu}", "error")
                 conn.close()
                 return redirect(redirect_url)

            if veri is None:
                 flash(f"Silinecek {cihaz_turu} bulunamadı (ID: {id}).", "warning")
                 conn.close()
                 return redirect(redirect_url)


        except Exception as e:
            flash(f"Silme onay sayfası verileri çekilirken hata oluştu: {str(e)}", "error")
            conn.close()
            return redirect(redirect_url)


        conn.close()
        return render_template('sil.html', cihaz_turu=cihaz_turu, veri=veri)


# Düzenleme Route'u
@app.route('/duzenle/<cihaz_turu>/<int:id>', methods=['GET', 'POST'])
@login_required # Düzenleme route'una sadece giriş yapmış kullanıcılar erişebilir
# İsteğe bağlı: Sadece adminlerin düzenlemesini istiyorsanız burada ekstra is_admin kontrolü yapın.
# if not current_user.is_admin:
#     flash("Düzenleme yetkiniz yok.", "danger")
#     return redirect(url_for('index')) # veya admin_index
def duzenle(cihaz_turu, id):
    # ... (Mevcut kodunuzdaki gibi) ...
    conn = get_db_connection()
    if conn is None:
        flash("Veritabanı bağlantısı kurulamadı.", "error")
        return redirect(url_for('index'))

    cursor = conn.cursor()
    # Düzenleme sonrası nereye yönlendirileceği
    redirect_url = url_for('index')

    if request.method == 'POST':
        form_data = request.form
        veri = dict(form_data) # Hata durumunda formu yeniden render etmek için veriyi sakla

        try:
            if cihaz_turu == 'bilgisayar':
                cursor.execute('''UPDATE bilgisayarlar SET bilgisayar_ekipman_kodu = ?, bilgisayar_marka = ?, bilgisayar_model = ?, bilgisayar_tip = ?, cpu = ?, ram = ?, disk = ?, kullanici = ? WHERE id = ?''',
                               (form_data.get('ekipman_kodu'), form_data.get('bilgisayar_marka'), form_data.get('bilgisayar_model'), form_data.get('bilgisayar_tip'),
                                form_data.get('cpu'), form_data.get('ram'), form_data.get('disk'), form_data.get('kullanici'), id))

            elif cihaz_turu == 'monitor':
                cursor.execute('''UPDATE monitorler SET ekipman_kodu = ?, monitor_marka = ?, monitor_model = ?, monitor_tipi = ?, monitor_boyut = ?, seri_numarasi = ?, kullanici = ? WHERE id = ?''',
                               (form_data.get('ekipman_kodu'), form_data.get('monitor_marka'), form_data.get('monitor_model'), form_data.get('monitor_tipi'),
                                form_data.get('monitor_boyut'), form_data.get('seri_numarasi'), form_data.get('kullanici'), id))

            elif cihaz_turu == 'yazici':
                cursor.execute('''UPDATE yazicilar SET ekipman_kodu = ?, printer_marka = ?, printer_model = ?, printer_tipi = ?, seri_numarasi = ?, kullanici = ? WHERE id = ?''',
                               (form_data.get('ekipman_kodu'), form_data.get('printer_marka'), form_data.get('printer_model'), form_data.get('printer_tipi'),
                                form_data.get('seri_numarasi'), form_data.get('kullanici'), id))

            elif cihaz_turu == 'sistem':
                cursor.execute('''UPDATE sistemler SET ekipman_kodu = ?, sistem_versiyon = ?, lisans_no = ?, lisans_key = ?, kullanici = ? WHERE id = ?''',
                               (form_data.get('ekipman_kodu'), form_data.get('sistem_versiyon'), form_data.get('lisans_no'), form_data.get('lisans_key'),
                                form_data.get('kullanici'), id))

            elif cihaz_turu == 'office':
                cursor.execute('''UPDATE officeler SET ekipman_kodu = ?, office_versiyon = ?, lisans_no = ?, lisans_key = ?, kullanici = ? WHERE id = ?''',
                               (form_data.get('ekipman_kodu'), form_data.get('office_versiyon'), form_data.get('lisans_no'),
                                form_data.get('lisans_key'), form_data.get('kullanici'), id))
            else:
                flash(f"Geçersiz cihaz türü: {cihaz_turu}", "error")
                conn.close()
                return redirect(redirect_url)


            conn.commit()
            flash(f"{cihaz_turu.capitalize()} başarıyla güncellendi!", "success")
            return redirect(redirect_url)

        except sqlite3.IntegrityError:
             flash(f"Hata: Güncellenen veriler başka bir kayıttaki benzersiz alanlarla çakışıyor olabilir.", "error")
             conn.rollback()
             # Hata durumunda formu girilen verilerle tekrar göstermek için select kutuları için veriyi çek
             conn = get_db_connection() # Tekrar bağlantı aç
             if conn is None:
                  flash("Veritabanı bağlantısı kurulamadı.", "error")
                  return render_template('duzenle.html', cihaz_turu=cihaz_turu, veri=veri,
                                         bilgisayar_markalari=[], monitor_markalari=[], monitor_boyut=[], monitor_tipleri=[], ms_surumler=[], office_surumler=[])

             bilgisayar_markalari = conn.execute("SELECT * FROM bilgisayar_markalari").fetchall()
             monitor_markalari = conn.execute("SELECT * FROM monitor_markalari").fetchall()
             monitor_boyut= conn.execute("SELECT * FROM monitor_boyut").fetchall()
             monitor_tipleri = conn.execute("SELECT * FROM monitor_tipleri").fetchall()
             ms_surumler = conn.execute("SELECT * FROM ms_surumler").fetchall()
             office_surumler = conn.execute("SELECT * FROM office_surumler").fetchall()
             conn.close()
             return render_template('duzenle.html',
                                    cihaz_turu=cihaz_turu,
                                    veri=veri, # Hata olduğunda form_data kullanılır
                                    bilgisayar_markalari=bilgisayar_markalari,
                                    monitor_markalari=monitor_markalari,
                                    monitor_boyut=monitor_boyut,
                                    monitor_tipleri=monitor_tipleri,
                                    ms_surumler=ms_surumler,
                                    office_surumler=office_surumler)


        except Exception as e:
            flash(f"Düzenleme sırasında hata oluştu: {str(e)}", "error")
            conn.rollback()
            # Hata durumunda formu girilen verilerle tekrar göstermek için select kutuları için veriyi çek
            conn = get_db_connection() # Tekrar bağlantı aç
            if conn is None:
                 flash("Veritabanı bağlantısı kurulamadı.", "error")
                 return render_template('duzenle.html', cihaz_turu=cihaz_turu, veri=veri,
                                        bilgisayar_markalari=[], monitor_markalari=[], monitor_boyut=[], monitor_tipleri=[], ms_surumler=[], office_surumler=[])

            bilgisayar_markalari = conn.execute("SELECT * FROM bilgisayar_markalari").fetchall()
            monitor_markalari = conn.execute("SELECT * FROM monitor_markalari").fetchall()
            monitor_boyut= conn.execute("SELECT * FROM monitor_boyut").fetchall()
            monitor_tipleri = conn.execute("SELECT * FROM monitor_tipleri").fetchall()
            ms_surumler = conn.execute("SELECT * FROM ms_surumler").fetchall()
            office_surumler = conn.execute("SELECT * FROM office_surumler").fetchall()
            conn.close()
            return render_template('duzenle.html',
                                   cihaz_turu=cihaz_turu,
                                   veri=veri, # Hata olduğunda form_data kullanılır
                                   bilgisayar_markalari=bilgisayar_markalari,
                                   monitor_markalari=monitor_markalari,
                                   monitor_boyut=monitor_boyut,
                                   monitor_tipleri=monitor_tipleri,
                                   ms_surumler=ms_surumler,
                                   office_surumler=office_surumler)


        finally:
            conn.close() # Bağlantıyı kapat


    # GET işlemi için mevcut veriyi ve select kutuları için seçenekleri getir
    veri = None
    bilgisayar_markalari, monitor_markalari, monitor_boyut, monitor_tipleri, ms_surumler, office_surumler = [], [], [], [], [], []
    try:
        conn = get_db_connection()
        if conn is None:
             flash("Veritabanı bağlantısı kurulamadı.", "error")
             return redirect(redirect_url) # Hata durumunda ana sayfaya dön


        if cihaz_turu == 'bilgisayar':
            veri = conn.execute('SELECT * FROM bilgisayarlar WHERE id = ?', (id,)).fetchone()
        elif cihaz_turu == 'monitor':
            veri = conn.execute('SELECT * FROM monitorler WHERE id = ?', (id,)).fetchone()
        elif cihaz_turu == 'yazici':
            veri = conn.execute('SELECT * FROM yazicilar WHERE id = ?', (id,)).fetchone()
        elif cihaz_turu == 'sistem':
            veri = conn.execute('SELECT * FROM sistemler WHERE id = ?', (id,)).fetchone()
        elif cihaz_turu == 'office':
            veri = conn.execute('SELECT * FROM officeler WHERE id = ?', (id,)).fetchone()
        else:
             flash(f"Geçersiz cihaz türü: {cihaz_turu}", "error")
             conn.close()
             return redirect(redirect_url)

        if veri is None:
             flash(f"Düzenlenecek {cihaz_turu} bulunamadı (ID: {id}).", "warning")
             conn.close()
             return redirect(redirect_url) # Veri yoksa ana sayfaya dön

        # Düzenleme formunda select kutuları varsa, seçenekleri çek
        bilgisayar_markalari = conn.execute("SELECT * FROM bilgisayar_markalari").fetchall()
        monitor_markalari = conn.execute("SELECT * FROM monitor_markalari").fetchall()
        monitor_boyut= conn.execute("SELECT * FROM monitor_boyut").fetchall()
        monitor_tipleri = conn.execute("SELECT * FROM monitor_tipleri").fetchall()
        ms_surumler = conn.execute("SELECT * FROM ms_surumler").fetchall()
        office_surumler = conn.execute("SELECT * FROM office_surumler").fetchall()


    except Exception as e:
        flash(f"Düzenleme formu verileri çekilirken hata oluştu: {str(e)}", "error")
        veri = None # Hata olursa formu boş göster veya yönlendir


    finally:
        if conn: conn.close() # Bağlantıyı kapat


    # Veri çekildiyse düzenleme formunu göster
    if veri:
        return render_template('duzenle.html',
                               cihaz_turu=cihaz_turu,
                               veri=veri,
                               bilgisayar_markalari=bilgisayar_markalari,
                               monitor_markalari=monitor_markalari,
                               monitor_boyut=monitor_boyut,
                               monitor_tipleri=monitor_tipleri,
                               ms_surumler=ms_surumler,
                               office_surumler=office_surumler)
    else:
        # Veri çekilemediyse veya hata oluştuysa yönlendirildiği için buraya muhtemelen düşmez.
        return redirect(redirect_url)


# --- Admin Sayfası Ana Route ---
@app.route('/admin')
@login_required # Admin panelini sadece giriş yapmış kullanıcılar görebilir
# İsteğe bağlı: Sadece admin yetkisi olanların admin panelini görmesini istiyorsanız bu kontrolü ekleyin.
# if not current_user.is_admin:
#     flash("Bu sayfaya erişim yetkiniz yok.", "danger")
#     return redirect(url_for('index'))
def admin_index():
    # Admin paneli ana sayfasını gösterir.
    return render_template('admin.html')

# --- Admin Bilgisayar Ekle Route ve İşlemi ---
@app.route('/admin/add/bilgisayar', methods=['GET', 'POST'])
@login_required # Bu sayfaya sadece giriş yapmış kullanıcılar erişebilir
# İsteğe bağlı: Sadece admin yetkisi olanların bu işlemi yapmasını istiyorsanız bu kontrolü ekleyin.
# if not current_user.is_admin:
#     flash("Ekleme yetkiniz yok.", "danger")
#     return redirect(url_for('admin_index')) # veya index
def admin_add_bilgisayar():
    conn = get_db_connection()
    if conn is None:
        flash("Veritabanı bağlantısı kurulamadı.", "error")
        return redirect(url_for('admin_index'))

    if request.method == 'POST':
        try:
            ekipman_kodu = request.form.get('ekipman_kodu')
            bilgisayar_tip = request.form.get('bilgisayar_tip')
            bilgisayar_marka = request.form.get('bilgisayar_marka')
            bilgisayar_model = request.form.get('bilgisayar_model')
            cpu = request.form.get('cpu')
            ram = request.form.get('ram')
            disk = request.form.get('disk')
            kullanici = request.form.get('kullanici')

            if not ekipman_kodu or not bilgisayar_marka or not bilgisayar_tip:
                 flash("Ekipman Kodu, Marka ve Tip zorunludur.", "warning")
                 return render_template('admin_add_bilgisayar.html', form_data=request.form)


            conn.execute("""
                INSERT INTO bilgisayarlar
                (ekipman_kodu, bilgisayar_tip, bilgisayar_marka, bilgisayar_model, cpu, ram, disk, kullanici)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (ekipman_kodu, bilgisayar_tip, bilgisayar_marka, bilgisayar_model, cpu, ram, disk, kullanici))

            conn.commit()
            flash("Yeni bilgisayar başarıyla eklendi!", "success")
            return redirect(url_for('admin_index'))

        except sqlite3.IntegrityError:
            flash(f"Hata: '{ekipman_kodu}' ekipman kodu zaten kayıtlı.", "error")
            conn.rollback()

        except Exception as e:
            flash(f"Bir hata oluştu: {str(e)}", "error")
            conn.rollback()

        finally:
            conn.close()

        return render_template('admin_add_bilgisayar.html', form_data=request.form)


    conn.close()
    return render_template('admin_add_bilgisayar.html')

# --- Diğer Admin Ekleme Route'ları (Benzer Şekilde Mantığı Kurulmalı ve @login_required eklenmeli) ---

@app.route('/admin/add/monitor', methods=['GET', 'POST'])
@login_required
def admin_add_monitor():
    flash("Monitör Ekleme Sayfası Yapım Aşamasında", "info")
    return redirect(url_for('admin_index'))

@app.route('/admin/add/yazici', methods=['GET', 'POST'])
@login_required
def admin_add_yazici():
     flash("Yazıcı Ekleme Sayfası Yapım Aşamasında", "info")
     return redirect(url_for('admin_index'))

@app.route('/admin/add/sistem', methods=['GET', 'POST'])
@login_required
def admin_add_sistem():
     flash("İşletim Sistemi Lisansı Ekleme Sayfası Yapım Aşamasında", "info")
     return redirect(url_for('admin_index'))

@app.route('/admin/add/office', methods=['GET', 'POST'])
@login_required
def admin_add_office():
    flash("Office Lisansı Ekleme Sayfası Yapım Aşamasında", "info")
    return redirect(url_for('admin_index'))


# Uygulamayı çalıştır
if __name__ == "__main__":
    init_db()
    # debug=True sadece geliştirme aşamasında kullanılmalı, canlıya alırken False yapın
    app.run(debug=True)