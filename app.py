# -*- coding: utf-8 -*-

import os
import sqlite3
from flask import Flask, render_template, request, redirect, jsonify, flash, session, url_for
import json

app = Flask(__name__)
app.secret_key = "gizli_anahtar"  # Güvenlik için gerçek bir key ile değiştir
basedir = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(basedir, "envanter.db")


def init_db():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS bilgisayarlar (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        bilgisayar_ekipman_kodu TEXT NOT NULL,
        bilgisayar_tip TEXT NOT NULL,
        bilgisayar_marka TEXT NOT NULL,
        bilgisayar_model TEXT NOT NULL,
        cpu TEXT NOT NULL,
        ram TEXT NOT NULL,
        disk TEXT NOT NULL,
        kullanici TEXT NOT NULL
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS monitorler (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        monitor_tipi TEXT NOT NULL,
        monitor_boyut INTEGER NOT NULL,
        monitor_marka TEXT NOT NULL,
        monitor_model TEXT NOT NULL,
        seri_numarasi TEXT NOT NULL,
        ekipman_kodu TEXT NOT NULL,
        kullanici TEXT NOT NULL
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS yazicilar (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        printer_marka TEXT NOT NULL,
        printer_model TEXT NOT NULL,
        printer_tipi TEXT NOT NULL,
        seri_numarasi TEXT NOT NULL,
        ekipman_kodu TEXT NOT NULL,
        kullanici TEXT NOT NULL
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sistemler (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sistem_versiyon TEXT NOT NULL,
        lisans_no TEXT NOT NULL,
        lisans_key TEXT NOT NULL,
        ekipman_kodu TEXT NOT NULL,
        kullanici TEXT NOT NULL
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS officeler (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        office_versiyon TEXT NOT NULL,
        lisans_no TEXT NOT NULL,
        lisans_key TEXT NOT NULL,
        ekipman_kodu TEXT NOT NULL,
        kullanici TEXT NOT NULL
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS bilgisayar_markalari (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ad TEXT NOT NULL
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS monitor_markalari (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ad TEXT NOT NULL
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS monitor_boyut (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ad TEXT NOT NULL
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS monitor_tipleri (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ad TEXT NOT NULL
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ms_surumler (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ad TEXT NOT NULL
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS office_surumler (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ad TEXT NOT NULL
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS kullanicilar (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ad TEXT NOT NULL
    );
    """)

    conn.commit()
    conn.close()


def get_db():
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn




@app.route("/ayarlar.json")
def get_ayarlar_json():
    try:
        conn = get_db()
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


@app.route("/ayarlar", methods=["GET", "POST"])
def ayarlar():
    conn = get_db()
    if request.method == "POST":
        tablo = request.form["tablo"]
        deger = request.form["deger"]
        conn.execute(f"INSERT INTO {tablo} (ad) VALUES (?)", (deger,))
        conn.commit()
    bilgisayar_markalari = conn.execute("SELECT * FROM bilgisayar_markalari").fetchall()
    monitor_markalari = conn.execute("SELECT * FROM monitor_markalari").fetchall()
    monitor_boyut = conn.execute("SELECT * FROM monitor_boyut").fetchall()
    monitor_tipleri = conn.execute("SELECT * FROM monitor_tipleri").fetchall()
    ms_surumler = conn.execute("SELECT * FROM ms_surumler").fetchall()
    office_surumler = conn.execute("SELECT * FROM office_surumler").fetchall()
        
    conn.close()
    return render_template("ayarlar.html", bilgisayar_markalari=bilgisayar_markalari, monitor_markalari=monitor_markalari, monitor_boyut=monitor_boyut, monitor_tipleri=monitor_tipleri, ms_surumler=ms_surumler, office_surumler=office_surumler )


@app.route("/")
def index():
    conn = get_db()
    bilgisayarlar = conn.execute("SELECT * FROM bilgisayarlar").fetchall()
    monitorler = conn.execute("SELECT * FROM monitorler").fetchall()
    yazicilar = conn.execute("SELECT * FROM yazicilar").fetchall()
    sistemler = conn.execute("SELECT * FROM sistemler").fetchall()
    officeler = conn.execute("SELECT * FROM officeler").fetchall()
    conn.close()
    return render_template("index.html", bilgisayarlar=bilgisayarlar, monitorler=monitorler, yazicilar=yazicilar, sistemler=sistemler, officeler=officeler)

@app.route("/ara")
def ara():
    conn = sqlite3.connect("envanter.db")
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    bilgisayarlar = cur.execute("SELECT * FROM bilgisayarlar").fetchall()
    monitorler = cur.execute("SELECT * FROM monitorler").fetchall()
    yazicilar = cur.execute("SELECT * FROM yazicilar").fetchall()
    sistemler = cur.execute("SELECT * FROM sistemler").fetchall()
    officeler = cur.execute("SELECT * FROM officeler").fetchall()

    conn.close()

    return render_template("ara.html",
        bilgisayarlar=bilgisayarlar,
        monitorler=monitorler,
        yazicilar=yazicilar,
        sistemler=sistemler,
        officeler=officeler
    )


@app.route('/ekle', methods=['GET', 'POST'])
def ekle():
    conn = get_db()
    if request.method == 'GET':
        bilgisayar_markalari = conn.execute("SELECT * FROM bilgisayar_markalari").fetchall()
        monitor_markalari = conn.execute("SELECT * FROM monitor_markalari").fetchall()
        monitor_boyut= conn.execute("SELECT * FROM monitor_boyut").fetchall()
        monitor_tipleri = conn.execute("SELECT * FROM monitor_tipleri").fetchall()
        ms_surumler = conn.execute("SELECT * FROM ms_surumler").fetchall()
        office_surumler = conn.execute("SELECT * FROM office_surumler").fetchall()
        
        conn.close()
        return render_template("ekle.html", bilgisayar_markalari=bilgisayar_markalari, monitor_markalari=monitor_markalari, monitor_boyut=monitor_boyut, monitor_tipleri=monitor_tipleri, ms_surumler=ms_surumler, office_surumler=office_surumler)
    #post kısmı zaten vardı
    elif request.method == 'POST':
        form = request.form
        cihaz_turu = form["cihaz_turu"]
        #... (ekleme işlemleri)
        try:
            if cihaz_turu == "bilgisayar":
                conn.execute("""
                    INSERT INTO bilgisayarlar 
                    (ekipman_kodu, bilgisayar_tip, bilgisayar_marka, bilgisayar_model, cpu, ram, disk, kullanici)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    form["ekipman_kodu"],
                    form["bilgisayar_tip"],
                    form["bilgisayar_marka"],
                    form["bilgisayar_model"],
                    form["cpu"],
                    form["ram"],
                    form["disk"],
                    form["kullanici"]
                ))
            elif cihaz_turu == "monitor":
                conn.execute("""
                    INSERT INTO monitorler 
                    (monitor_tipi, monitor_boyut, monitor_marka, monitor_model, seri_numarasi, ekipman_kodu, kullanici)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    form["monitor_tipi"],
                    form["monitor_boyut"],
                    form["monitor_marka"],
                    form["monitor_model"],
                    form["seri_numarasi"],
                    form["ekipman_kodu"],
                    form["kullanici"]
                ))
            elif cihaz_turu == "printer":
                conn.execute("""
                    INSERT INTO yazicilar 
                    (printer_marka, printer_model, printer_tipi, seri_numarasi, ekipman_kodu, kullanici)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    form["printer_marka"],
                    form["printer_model"],
                    form["printer_tipi"],
                    form["seri_numarasi"],
                    form["ekipman_kodu"],
                    form["kullanici"]
                ))
            elif cihaz_turu == "isletim_sistemi":
                conn.execute("""
                    INSERT INTO sistemler 
                    (sistem_versiyon, lisans_no, lisans_key, ekipman_kodu, kullanici)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    form["sistem_versiyon"],
                    form["lisans_no"],
                    form["lisans_key"],
                    form["ekipman_kodu"],
                    form["kullanici"]
                ))
            elif cihaz_turu == "office":
                conn.execute("""
                    INSERT INTO officeler 
                    (office_versiyon, lisans_no, lisans_key, ekipman_kodu, kullanici)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    form["office_versiyon"],
                    form["lisans_no"],
                    form["lisans_key"],
                    form["ekipman_kodu"],
                    form["kullanici"]
                ))

            flash("Ekleme başarılı!", "success")
            conn.commit()
        except sqlite3.IntegrityError as e:
            if "UNIQUE constraint failed" in str(e):
                flash(f"Bu {cihaz_turu} zaten kayıtlı!", "error")
            else:
                flash(f"Bir hata oluştu: {str(e)}", "error")
            conn.rollback()
        finally:
            conn.close()
        return redirect("/")


@app.route('/sil/<cihaz_turu>/<int:id>', methods=['GET', 'POST'])
def sil(cihaz_turu, id):
    conn = get_db_connection()
    cursor = conn.cursor()

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

            conn.commit()
            flash("Silme Başarılı!", "success")
            return redirect(url_for('index'))
        except Exception as e:
            flash(f"Silme sırasında hata oluştu: {str(e)}", "error")
            conn.rollback()
            return redirect(url_for('sil', cihaz_turu=cihaz_turu, id=id))
        finally:
            conn.close()
    elif request.method == 'GET':  #Eğer GET isteği ise silme onay sayfasına yönlendir
        veri = None
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
        conn.close()
        return render_template('sil.html', cihaz_turu=cihaz_turu, veri=veri)

    


def get_db_connection():
    conn = sqlite3.connect('envanter.db')
    conn.row_factory = sqlite3.Row
    return conn


@app.route('/duzenle/<cihaz_turu>/<int:id>', methods=['GET', 'POST'])
def duzenle(cihaz_turu, id):
    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        try: #try bloğu eklendi
            if cihaz_turu == 'bilgisayar':
                cursor.execute('''UPDATE bilgisayarlar SET ekipman_kodu = ?, bilgisayar_marka = ?, bilgisayar_model = ?, bilgisayar_tip = ?, cpu = ?, ram = ?, disk = ?, kullanici = ? WHERE id = ?''',
                                (request.form['ekipman_kodu'], request.form['bilgisayar_marka'], request.form['bilgisayar_model'], request.form['bilgisayar_tip'],
                                 request.form['cpu'], request.form['ram'], request.form['disk'], request.form['kullanici'], id))

            elif cihaz_turu == 'monitor':
                cursor.execute('''UPDATE monitorler SET ekipman_kodu = ?, monitor_marka = ?, monitor_model = ?, monitor_tipi = ?, monitor_boyut = ?, seri_numarasi = ?, kullanici = ? WHERE id = ?''',
                                (request.form['ekipman_kodu'], request.form['monitor_marka'], request.form['monitor_model'], request.form['monitor_tipi'],
                                 request.form['monitor_boyut'], request.form['seri_numarasi'], request.form['kullanici'], id))

            elif cihaz_turu == 'yazici':
                cursor.execute('''UPDATE yazicilar SET ekipman_kodu = ?, printer_marka = ?, printer_model = ?, printer_tipi = ?, seri_numarasi = ?, kullanici = ? WHERE id = ?''',
                                (request.form['ekipman_kodu'], request.form['printer_marka'], request.form['printer_model'], request.form['printer_tipi'],
                                 request.form['seri_numarasi'], request.form['kullanici'], id))

            elif cihaz_turu == 'sistem':
                cursor.execute('''UPDATE sistemler SET ekipman_kodu = ?, sistem_versiyon = ?, lisans_no = ?, lisans_key = ?, kullanici = ? WHERE id = ?''',  
                                (request.form['ekipman_kodu'], request.form['sistem_versiyon'], request.form['lisans_no'], request.form['lisans_key'],
                                 request.form['kullanici'], id))

            elif cihaz_turu == 'office':
                cursor.execute('''UPDATE officeler SET ekipman_kodu = ?, office_versiyon = ?, lisans_no = ?, lisans_key = ?, kullanici = ? WHERE id = ?''', 
                                (request.form['ekipman_kodu'], request.form['office_versiyon'], request.form['lisans_no'],
                                 request.form['lisans_key'], request.form['kullanici'], id))
            

            
            conn.commit() #buraya alındı
            flash("Düzenleme Başarılı!", "success")  # Flash mesajı buraya alındı
            return redirect(url_for('index'))
        except Exception as e: #hata yakalama
            flash(f"Düzenleme sırasında hata oluştu: {str(e)}", "error")
            conn.rollback()
            return redirect(url_for('duzenle', cihaz_turu=cihaz_turu, id=id))
        finally:
            conn.close() #finally blogu eklendi




            

    # GET işlemi için mevcut veriyi getir
    veri = None
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

    conn.close()
    return render_template('duzenle.html', cihaz_turu=cihaz_turu, veri=veri)




    # GET isteği geldiğinde markaları çek
    bilgisayar_markalari = conn.execute("SELECT * FROM bilgisayar_markalari").fetchall()
    monitor_markalari = conn.execute("SELECT * FROM monitor_markalari").fetchall()
    monitor_boyut = conn.execute("SELECT * FROM monitor_boyut").fetchall()
    monitor_tipleri = conn.execute("SELECT * FROM monitor_tipleri").fetchall()
    ms_surumler = conn.execute("SELECT * FROM ms_surumler").fetchall()
    office_surumler = conn.execute("SELECT * FROM office_surumler").fetchall()
    
    
    conn.close()
    return render_template("ekle.html", bilgisayar_markalari=bilgisayar_markalari, monitor_markalari=monitor_markalari, monitor_boyut=monitor_boyut, monitor_tipleri=monitor_tipleri, ms_surumler=ms_surumler, office_surumler=office_surumler)



if __name__ == "__main__":
    init_db()
    app.run(debug=True)
