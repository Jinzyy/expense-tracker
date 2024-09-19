from flask import Flask, render_template, request, redirect, url_for, jsonify
import psycopg2

app = Flask(__name__)

# Fungsi untuk membuat koneksi ke PostgreSQL
def get_db_connection():
    conn = psycopg2.connect(
        host="iffan.online",
        database="postgres",
        user="postgres",
        password="1234"
    )
    return conn

@app.route('/')
def index():
    conn = get_db_connection()
    cur = conn.cursor()

    # Ambil semua transaksi
    cur.execute("""
        SELECT riwayat_transaksi.deskripsi, ms_kategori.nama_kategori, sub_kategori.nama_subkategori, riwayat_transaksi.nominal 
        FROM coro.riwayat_transaksi
        LEFT JOIN coro.ms_kategori ON riwayat_transaksi.id_kategori = ms_kategori.id
        LEFT JOIN coro.sub_kategori ON riwayat_transaksi.id_subkategori = sub_kategori.id;
    """)
    expenses = cur.fetchall()

    # Ambil total pengeluaran per kategori
    cur.execute("""
        SELECT ms_kategori.nama_kategori, SUM(riwayat_transaksi.nominal)
        FROM coro.riwayat_transaksi
        LEFT JOIN coro.ms_kategori ON riwayat_transaksi.id_kategori = ms_kategori.id
        GROUP BY ms_kategori.nama_kategori;
    """)
    category_totals = cur.fetchall()

    # Ambil uang pengguna
    cur.execute("SELECT jumlah_uang FROM coro.uang_pengguna ORDER BY tanggal DESC LIMIT 1;")
    user_money = cur.fetchone()
    user_money = user_money[0] if user_money else 0

    # Hitung total pengeluaran
    total_expenses = sum([expense[3] for expense in expenses])
    remaining_money = user_money - total_expenses

    conn.close()

    categories_list = [cat[0] for cat in category_totals]
    amounts = [cat[1] for cat in category_totals]

    return render_template('index.html', expenses=expenses, categories=categories_list, amounts=amounts, remaining_money=remaining_money)

@app.route('/subcategories/<main_category>')
def get_subcategories(main_category):
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT sub_kategori.nama_subkategori 
        FROM coro.sub_kategori
        LEFT JOIN coro.ms_kategori ON sub_kategori.id_kategori = ms_kategori.id
        WHERE ms_kategori.nama_kategori = %s;
    """, (main_category,))
    
    subcategories = cur.fetchall()
    conn.close()
    
    return jsonify(subcategories=[sub[0] for sub in subcategories])

@app.route('/add', methods=['POST'])
def add_expense():
    description = request.form.get('description')
    main_category = request.form.get('main_category')
    sub_category = request.form.get('sub_category')
    amount = request.form.get('amount')

    conn = get_db_connection()
    cur = conn.cursor()

    # Ambil id kategori
    cur.execute("SELECT id FROM coro.ms_kategori WHERE nama_kategori = %s", (main_category,))
    kategori = cur.fetchone()

    # Ambil id sub kategori
    cur.execute("SELECT id FROM coro.sub_kategori WHERE nama_subkategori = %s", (sub_category,))
    subkategori = cur.fetchone()

    # Masukkan transaksi baru
    cur.execute("""
        INSERT INTO coro.riwayat_transaksi (deskripsi, id_kategori, id_subkategori, nominal) 
        VALUES (%s, %s, %s, %s)
    """, (description, kategori[0], subkategori[0], amount))

    conn.commit()
    conn.close()

    return redirect(url_for('index'))

@app.route('/add_money', methods=['POST'])
def add_money():
    amount = request.form.get('amount')

    conn = get_db_connection()
    cur = conn.cursor()

    # Masukkan jumlah uang pengguna baru
    cur.execute("INSERT INTO coro.uang_pengguna (jumlah_uang) VALUES (%s)", (amount,))
    conn.commit()
    conn.close()

    return redirect(url_for('index'))

@app.route('/add_category', methods=['POST'])
def add_category():
    new_category = request.form.get('new_category')

    conn = get_db_connection()
    cur = conn.cursor()

    # Masukkan kategori baru
    cur.execute("INSERT INTO coro.ms_kategori (nama_kategori) VALUES (%s)", (new_category,))
    conn.commit()
    conn.close()

    return redirect(url_for('index'))

@app.route('/add_subcategory', methods=['POST'])
def add_subcategory():
    new_subcategory = request.form.get('new_subcategory')
    main_category = request.form.get('main_category')

    conn = get_db_connection()
    cur = conn.cursor()

    # Ambil id kategori untuk subkategori baru
    cur.execute("SELECT id FROM coro.ms_kategori WHERE nama_kategori = %s", (main_category,))
    kategori = cur.fetchone()

    # Masukkan subkategori baru
    cur.execute("INSERT INTO coro.sub_kategori (id_kategori, nama_subkategori) VALUES (%s, %s)", (kategori[0], new_subcategory))
    conn.commit()
    conn.close()

    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
