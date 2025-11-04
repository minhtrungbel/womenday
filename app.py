# appwomenday.py
from flask import Flask, render_template, request, jsonify
import os
import sqlite3
import unicodedata
import cloudinary
import cloudinary.uploader
from dotenv import load_dotenv

# Load .env
load_dotenv()

# Cấu hình Cloudinary
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
    secure=True
)

app = Flask(__name__, template_folder='templates', static_folder='static')

# Chuẩn hóa tên
def normalize_name(name):
    name = name.strip().lower()
    name = ''.join(c for c in unicodedata.normalize('NFD', name) if unicodedata.category(c) != 'Mn')
    replacements = {'đ': 'd', 'ơ': 'o', 'ư': 'u', 'ă': 'a', 'â': 'a', 'ê': 'e', 'ô': 'o'}
    name = ''.join(replacements.get(c, c) for c in name)
    name = name.replace(" ", "")
    mapping = {
        "vbt": "vobaotran", "lnbt": "lenguyenbaotran", "bka": "buikieuanh",
        "tngl": "trinhngocgialinh", "hnkn": "huynhnguyenkimngan", "lnk": "lengocnhaky",
        "tnntt": "trannguyenngocthienthanh", "nnb": "nguyenngocbich", "thtn": "tranhatuyetnhu",
        "dtta": "dothithanhan", "tth": "tranthihanh", "dka": "dokhanhan",
        "lnh": "lieunhuhien", "nttv": "nguyenthithuyvan"
    }
    return mapping.get(name, name)

# Khởi tạo DB + thêm dữ liệu
def init_db():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS updates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            image_url TEXT,
            content TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            short_name TEXT UNIQUE,
            full_name TEXT,
            bio TEXT,
            image_url TEXT,
            audio_url TEXT
        )
    ''')
    cursor.execute('DELETE FROM profiles')

    # THAY 28 URL DƯỚI ĐÂY BẰNG URL THẬT TỪ CLOUDINARY
    # Giữ nguyên nội dung gốc cho tên, bio, và cấu trúc
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
        ("trinhngocgialinh", "Trịnh Ngọc Gia Linh", "Trịnh Ngọc Gia Linh đam mê công nghệ và có khả năng lãnh đạo tuyệt vời.", 
         "https://res.cloudinary.com/dxxx/image/upload/v123/womenday/uploads/trinh_ngoc_gia_linh.jpg",
         "https://res.cloudinary.com/dxxx/video/upload/v123/womenday/audio/4_music.mp3"),
        ("huynhnguyenkimngan", "Huỳnh Nguyễn Kim Ngân", "Huỳnh Nguyễn Kim Ngân là một người yêu thích văn hóa và nghệ thuật truyền thống.", 
         "https://res.cloudinary.com/dxxx/image/upload/v123/womenday/uploads/huynh_nguyen_kim_ngan.jpg",
         "https://res.cloudinary.com/dxxx/video/upload/v123/womenday/audio/5_music.mp3"),
        ("lengocnhaky", "Lê Ngọc Nhã Kỳ", "Lê Ngọc Nhã Kỳ có niềm đam mê với âm nhạc và sáng tác.", 
         "https://res.cloudinary.com/dxxx/image/upload/v123/womenday/uploads/le_ngoc_nha_ky.jpg",
         "https://res.cloudinary.com/dxxx/video/upload/v123/womenday/audio/6_music.mp3"),
        ("trannguyenngocthienthanh", "Trần Nguyễn Ngọc Thiên Thanh", "Trần Nguyễn Ngọc Thiên Thanh là một người yêu thiên nhiên và môi trường.", 
         "https://res.cloudinary.com/dxxx/image/upload/v123/womenday/uploads/tran_nguyen_ngoc_thien_thanh.jpg",
         "https://res.cloudinary.com/dxxx/video/upload/v123/womenday/audio/7_music.mp3"),
        ("lungocbich", "Lữ Ngọc Bích", "Lữ Ngọc Bích là một người có tâm hồn nghệ sĩ, yêu thích hội họa.", 
         "https://res.cloudinary.com/dxxx/image/upload/v123/womenday/uploads/lu_ngoc_bich.jpg",
         "https://res.cloudinary.com/dxxx/video/upload/v123/womenday/audio/8_music.mp3"),
        ("tranhatuyetnhu", "Trần Hà Tuyết Như", "Trần Hà Tuyết Như luôn tìm tòi và sáng tạo trong lĩnh vực thời trang.", 
         "https://res.cloudinary.com/dxxx/image/upload/v123/womenday/uploads/tran_ha_tuyet_nhu.jpg",
         "https://res.cloudinary.com/dxxx/video/upload/v123/womenday/audio/9_music.mp3"),
        ("dothithanhan", "Đỗ Thị Thanh An", "Đỗ Thị Thanh An là một cá nhân nhiệt huyết, yêu thích các hoạt động cộng đồng.", 
         "https://res.cloudinary.com/dxxx/image/upload/v123/womenday/uploads/do_thi_thanh_an.jpg",
         "https://res.cloudinary.com/dxxx/video/upload/v123/womenday/audio/10_music.mp3"),
        ("tranthihanh", "Trần Thị Hạnh", "Trần Thị Hạnh có niềm đam mê với giáo dục và chia sẻ tri thức.", 
         "https://res.cloudinary.com/dxxx/image/upload/v123/womenday/uploads/tran_thi_hanh.jpg",
         "https://res.cloudinary.com/dxxx/video/upload/v123/womenday/audio/11_music.mp3"),
        ("dokhanhan", "Đỗ Khánh An", "Đỗ Khánh An là một người yêu sách và có sở thích viết lách.", 
         "https://res.cloudinary.com/dxxx/image/upload/v123/womenday/uploads/do_khanh_an.jpg",
         "https://res.cloudinary.com/dxxx/video/upload/v123/womenday/audio/12_music.mp3"),
        ("lieunhuhien", "Liêu Như Hiền", "Liêu Như Hiền là một cá nhân đầy năng lượng, đam mê sáng tạo nội dung số.", 
         "https://res.cloudinary.com/dxxx/image/upload/v123/womenday/uploads/lieu_nhu_hien.jpg",
         "https://res.cloudinary.com/dxxx/video/upload/v123/womenday/audio/13_music.mp3"),
        ("nguyenthithuyvan", "Nguyễn Thị Thúy Vân", "Nguyễn Thị Thúy Vân yêu thích viết lách và chia sẻ câu chuyện truyền cảm hứng.", 
         "https://res.cloudinary.com/dxxx/image/upload/v123/womenday/uploads/nguyen_thi_thuy_van.jpg",
         "https://res.cloudinary.com/dxxx/video/upload/v123/womenday/audio/14_music.mp3")
    ]
    cursor.executemany("INSERT OR IGNORE INTO profiles VALUES (NULL, ?, ?, ?, ?, ?)", profiles)
    conn.commit()
    conn.close()

init_db()

# Trang chủ
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
                    result = cloudinary.uploader.upload(file, folder="womenday/uploads", resource_type="image")
                    image_url = result['secure_url']
                except Exception as e:
                    print(f"Upload error: {e}")

        if name or image_url or content:
            conn = sqlite3.connect('database.db')
            cursor = conn.cursor()
            cursor.execute('INSERT INTO updates (name, image_url, content) VALUES (?, ?, ?)', (name, image_url, content))
            conn.commit()
            conn.close()

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT name, image_url, content, timestamp FROM updates ORDER BY timestamp DESC')
    updates = cursor.fetchall()
    conn.close()
    return render_template('home.html', updates=updates)

# Profile
@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        norm = normalize_name(name)
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute("SELECT full_name, bio, image_url, audio_url FROM profiles WHERE short_name = ?", (norm,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return render_template('profile.html', profile={'name': row[0], 'bio': row[1], 'image': row[2], 'audio': row[3]})
        else:
            return render_template('profile.html', profile=None, error="Không tìm thấy")
    return render_template('profile.html', profile=None)

@app.route('/source')
def source(): return render_template('source.html')

@app.route('/link')
def link(): return render_template('link.html')

@app.route('/api/names')
def get_names():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT full_name FROM profiles")
    names = [row[0] for row in cursor.fetchall()]
    conn.close()
    return jsonify({'names': names})

if __name__ == '__main__':
    app.run(debug=True)

