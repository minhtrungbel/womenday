# app.py
from flask import Flask, render_template, request, jsonify
import os
import sqlite3
import unicodedata
import cloudinary
import cloudinary.uploader
from dotenv import load_dotenv

# Load .env (tạo file .env ở root repo)
load_dotenv()

# Cấu hình Cloudinary từ .env
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
    secure=True
)

app = Flask(__name__, template_folder='templates', static_folder='static')
app.config['UPLOAD_FOLDER'] = os.path.join(app.static_folder, 'Uploads')
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# === DB PATH (Render Disk) ===
DB_PATH = os.environ.get('DB_PATH', 'database.db')  # Render: /data/database.db

def get_db():
    return sqlite3.connect(DB_PATH)

# === NORMALIZE NAME ===
def normalize_name(name):
    name = name.strip().lower()
    name = ''.join(c for c in unicodedata.normalize('NFD', name) if unicodedata.category(c) != 'Mn')
    replacements = {'đ':'d','ơ':'o','ư':'u','ă':'a','â':'a','ê':'e','ô':'o'}
    name = ''.join(replacements.get(c, c) for c in name).replace(" ", "")
    mapping = {
        "vbt":"vobaotran","lnbt":"lenguyenbaotran","bka":"buikieuanh",
        "tngl":"trinhngocgialinh","hnkn":"huynhnguyenkimngan","lnk":"lengocnhaky",
        "tnntt":"trannguyenngocthienthanh","nnb":"nguyenngocbich","thtn":"tranhatuyetnhu",
        "dtta":"dothithanhan","tth":"tranthihanh","dka":"dokhanhan",
        "lnh":"lieunhuhien","nttv":"nguyenthithuyvan"
    }
    return mapping.get(name, name)

# === INIT DB – CHỈ INSERT NẾU CHƯA CÓ ===
def init_db():
    conn = get_db()
    cur = conn.cursor()

    # Bảng updates
    cur.execute('''
        CREATE TABLE IF NOT EXISTS updates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            image_url TEXT,
            content TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Bảng profiles
    cur.execute('''
        CREATE TABLE IF NOT EXISTS profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            short_name TEXT UNIQUE,
            full_name TEXT,
            bio TEXT,
            image_url TEXT,
            audio_url TEXT
        )
    ''')

    # Chỉ insert nếu chưa có dữ liệu
    cur.execute("SELECT COUNT(*) FROM profiles")
    if cur.fetchone()[0] == 0:
        profiles = [
            ("vobaotran", "Võ Bảo Trân", "Võ Bảo Trân là một nhà thiết kế xuất sắc, đam mê nghệ thuật và màu sắc.",
             "https://res.cloudinary.com/dxxx/image/upload/v123/womenday/uploads/vo_bao_tran.jpg",
             "https://res.cloudinary.com/dxxx/video/upload/v123/womenday/audio/1_music.mp3"),
            ("lenguyenbaotran", "Lê Nguyễn Bảo Trân", "Lê Nguyễn Bảo Trân là một người sáng tạo, yêu thích khám phá những điều mới mẻ.",
             "https://res.cloudinary.com/dxxx/image/upload/v123/womenday/uploads/le_nguyen_bao_tran.jpg",
             "https://res.cloudinary.com/dxxx/video/upload/v123/womenday/audio/2_music.mp3"),
            ("buikieuanh", "Bùi Kiều Anh", "Bùi Kiều Anh là một cá nhân năng động, luôn truyền cảm hứng cho mọi người xung quanh.",
             "https://res.cloudinary.com/dxxx/image/upload/v123/womenday/uploads/bui_kieu_anh.jpg",
             "https://res.cloudinary.com/dogyjotxv/video/upload/v1762270650/1_zuziql.mp3"),
            # ... (các dòng còn lại giữ nguyên URL Cloudinary của bạn)
            ("nguyenthithuyvan", "Nguyễn Thị Thúy Vân", "Nguyễn Thị Thúy Vân yêu thích viết lách và chia sẻ câu chuyện truyền cảm hứng.",
             "https://res.cloudinary.com/dxxx/image/upload/v123/womenday/uploads/nguyen_thi_thuy_van.jpg",
             "https://res.cloudinary.com/dxxx/video/upload/v123/womenday/audio/14_music.mp3")
        ]
        cur.executemany(
            "INSERT INTO profiles (short_name, full_name, bio, image_url, audio_url) VALUES (?, ?, ?, ?, ?)",
            profiles
        )
    conn.commit()
    conn.close()

# Gọi init_db() 1 lần khi app khởi động
init_db()

# === ROUTES ===
@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        content = request.form.get('content', '').strip()
        image_url = None
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename:
                try:
                    result = cloudinary.uploader.upload(
                        file,
                        folder="womenday/uploads",
                        resource_type="image"
                    )
                    image_url = result['secure_url']
                except Exception as e:
                    print(f"Cloudinary upload error: {e}")
        if name or image_url or content:
            conn = get_db()
            cur = conn.cursor()
            cur.execute('INSERT INTO updates (name, image_url, content) VALUES (?, ?, ?)', (name, image_url, content))
            conn.commit()
            conn.close()

    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT name, image_url, content, timestamp FROM updates ORDER BY timestamp DESC')
    updates = cur.fetchall()
    conn.close()
    return render_template('home.html', updates=updates)

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        norm = normalize_name(name)
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT full_name, bio, image_url, audio_url FROM profiles WHERE short_name = ?", (norm,))
        row = cur.fetchone()
        conn.close()
        if row:
            return render_template('profile.html', profile={
                'name': row[0], 'bio': row[1], 'image': row[2], 'audio': row[3]
            })
        else:
            return render_template('profile.html', profile=None, error="Không tìm thấy profile")
    return render_template('profile.html', profile=None)

@app.route('/source')
def source():
    return render_template('source.html')

@app.route('/link')
def link():
    return render_template('link.html')

@app.route('/api/names')
def get_names():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT full_name FROM profiles")
    names = [row[0] for row in cur.fetchall()]
    conn.close()
    return jsonify({'names': names})

# === PRODUCTION RUN (GUNICORN) ===
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
