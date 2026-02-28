from flask import Flask, render_template, request, jsonify
import os
import sqlite3
import unicodedata
import cloudinary
import cloudinary.uploader
from dotenv import load_dotenv
import socket

load_dotenv()

cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
    secure=True
)

app = Flask(__name__, template_folder='templates', static_folder='static')

def normalize_name(name):
    name = name.strip().lower()
    name = ''.join(c for c in unicodedata.normalize('NFD', name) if unicodedata.category(c) != 'Mn')
    replacements = {'đ': 'd', 'ơ': 'o', 'ư': 'u', 'ă': 'a', 'â': 'a', 'ê': 'e', 'ô': 'o'}
    name = ''.join(replacements.get(c, c) for c in name)
    name = name.replace(" ", "")
    mapping = {
        "vbt": "vobaotran",
        "lnbt": "lenguyenbaotran",
        "bka": "buikieuanh",
        "tngl": "trinhngocgialinh",
        "hnkn": "huynhnguyenkimngan",
        "lnk": "lengocnhaky",
        "tnntt": "trannguyenngocthienthanh",
        "nnb": "nguyenngocbich",
        "thtn": "tranhatuyetnhu",
        "dtta": "dothithanhan",
        "tth": "tranthihanh",
        "dka": "dokhanhan",
        "lnh": "lieunhuhien",
        "typ": "tranyenphuong",
    }
    return mapping.get(name, name)

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
            nickname TEXT,
            favorite_song TEXT,
            things_we_love TEXT,
            layer_url TEXT,
            audio_url TEXT,
            avatar_url TEXT
        )
    ''')

    # Migration an toàn: tự thêm cột mới nếu DB cũ chưa có
    existing_columns = [row[1] for row in cursor.execute("PRAGMA table_info(profiles)").fetchall()]
    for col, col_type in [
        ("nickname", "TEXT"),
        ("favorite_song", "TEXT"),
        ("things_we_love", "TEXT"),
        ("song", "TEXT"),
        ("letter_content", "TEXT"),   # nội dung thư — dùng trong trang letter
        ("letter_image_url", "TEXT"), # ảnh thư — dùng trong trang letter
        ("gif_up", "TEXT"),           # gif di chuyển lên
        ("gif_down", "TEXT"),         # gif di chuyển xuống
        ("gif_left", "TEXT"),         # gif di chuyển ngang trái
        ("gif_right", "TEXT"),        # gif di chuyển ngang phải
    ]:
        if col not in existing_columns:
            cursor.execute(f"ALTER TABLE profiles ADD COLUMN {col} {col_type} DEFAULT ''")

    # ==============================================================
    # THỨ TỰ CỘT:
    # short_name | full_name | nickname | favorite_song | things_we_love
    # | layer_url | audio_url | avatar_url | song | letter_content | letter_image_url
    # | gif_up | gif_down | gif_left | gif_right
    #
    # Điền nội dung vào các chuỗi "" bên dưới mỗi profile:
    #   "" thứ 1 = biệt danh
    #   "" thứ 2 = bài nhạc yêu thích (hiển thị trong info card)
    #   "" thứ 3 = điều tụi mình thích về cậu
    #   "" thứ 4 = tên bài nhạc chạy trên music bar (vd: "Chìm Sâu - MCK")
    #   "" thứ 5 = nội dung thư (dùng trong trang letter)
    #   "" thứ 6 = URL ảnh thư (dùng trong trang letter)
    #   "" thứ 7 = URL gif up (di chuyển lên xuống)
    #   "" thứ 8 = URL gif down (di chuyển lên xuống)
    #   "" thứ 9 = URL gif left (di chuyển ngang)
    #   "" thứ 10 = URL gif right (di chuyển ngang)
    # ==============================================================
    profiles = [
        (
            "vobaotran", "Võ Bảo Trân",
            "",   # biệt danh
            "",   # bài nhạc yêu thích
            "",   # điều tụi mình thích về cậu
            "https://res.cloudinary.com/dogyjotxv/image/upload/v1771951780/votran2_rcmb4w.png",
            "https://res.cloudinary.com/dogyjotxv/video/upload/v1772207141/VSTRA_-_Ai_Ngo%C3%A0i_Anh_Official_Audio_j8abwy.mp3",
            "https://res.cloudinary.com/dogyjotxv/image/upload/v1772022864/votran1_bgdgxr.png",
            "Ai Ngoài Anh ∙ VSTRA",   # tên bài trên music bar (vd: "Tên bài - Tác giả")
            "",   # nội dung thư (letter)
            "",   # URL ảnh thư (letter)
            "",   # gif up
            "",   # gif down
            "",   # gif left
            "",   # gif right
        ),
        (
            "lenguyenbaotran", "Lê Nguyễn Bảo Trân",
            "",   # biệt danh
            "",   # bài nhạc yêu thích
            "",   # điều tụi mình thích về cậu
            "https://res.cloudinary.com/dogyjotxv/image/upload/v1771954229/letran2_epjgp6.png",
            "https://res.cloudinary.com/dogyjotxv/video/upload/v1772206464/Ph%C3%A1o_Northside-M%E1%BB%99t_Ng%C3%A0y_Ch%E1%BA%B3ng_N%E1%BA%AFng_ft.thobaymauofficial_Official_MV_hwkpvk.mp3",
            "https://res.cloudinary.com/dogyjotxv/image/upload/v1772036653/letran1_xkztjc.png",
            "Một Ngày Chẳng Nắng ∙ Pháo Northside",   # tên bài trên music bar
            "",   # nội dung thư (letter)
            "",   # URL ảnh thư (letter)
            "",   # gif up
            "",   # gif down
            "",   # gif left
            "",   # gif right
        ),
        (
            "buikieuanh", "Bùi Kiều Anh",
            "",   # biệt danh
            "",   # bài nhạc yêu thích
            "",   # điều tụi mình thích về cậu
            "https://res.cloudinary.com/dogyjotxv/image/upload/v1771954223/kieuanh2_qlujkd.png",
            "https://res.cloudinary.com/dogyjotxv/video/upload/v1772211147/06._Ch%E1%BB%89_M%E1%BB%99t_%C4%90%C3%AAm_N%E1%BB%AFa_Th%C3%B4i_-_RPT_MCK_ft._tlinh_99_the_album_slzrxh.mp3",
            "https://res.cloudinary.com/dogyjotxv/image/upload/v1772036650/kieuanh1_tcql5x.png",
            "Chỉ Một Đêm Nữa Thôi ∙ MCK",   # tên bài trên music bar
            "",   # nội dung thư (letter)
            "",   # URL ảnh thư (letter)
            "https://res.cloudinary.com/dogyjotxv/image/upload/v1772294406/Buoc_Toc_-_Up_fekvlr.gif",     # gif up
            "https://res.cloudinary.com/dogyjotxv/image/upload/v1772294406/Buoc_Toc_-_Down_gpwews.gif",   # gif down
            "",   # gif left
            "",   # gif right
        ),
        (
            "trinhngocgialinh", "Trịnh Ngọc Gia Linh",
            "",   # biệt danh
            "",   # bài nhạc yêu thích
            "",   # điều tụi mình thích về cậu
            "https://res.cloudinary.com/dogyjotxv/image/upload/v1772113738/gialinh2_1_k4bes6.png",
            "https://res.cloudinary.com/dogyjotxv/video/upload/v1772212283/GO-CORTIS_yfqtlh.mp3",
            "https://res.cloudinary.com/dogyjotxv/image/upload/v1772036650/gialinh1_nfsmt0.png",
            "GO ∙ CORTIS",   # tên bài trên music bar
            "",   # nội dung thư (letter)
            "",   # URL ảnh thư (letter)
            "",   # gif up
            "",   # gif down
            "",   # gif left
            "",   # gif right
        ),
        (
            "huynhnguyenkimngan", "Huỳnh Nguyễn Kim Ngân",
            "",   # biệt danh
            "",   # bài nhạc yêu thích
            "",   # điều tụi mình thích về cậu
            "https://res.cloudinary.com/dogyjotxv/image/upload/v1771954221/kimngan2_tsqlkc.png",
            "https://res.cloudinary.com/dogyjotxv/video/upload/v1772210869/PUPPY_DANGRANGTO_-_WRONG_TIMES_Live_at_LAB_RADAR_ZLAB_fp0cc6.mp3",
            "https://res.cloudinary.com/dogyjotxv/image/upload/v1772036653/kimngan1_lbbfmu.png",
            "Wrong Times ∙ Young Puppy x DANGRANGTO",   # tên bài trên music bar
            "",   # nội dung thư (letter)
            "",   # URL ảnh thư (letter)
            "",   # gif up
            "",   # gif down
            "",   # gif left
            "",   # gif right
        ),
        (
            "lengocnhaky", "Lê Ngọc Nhã Kỳ",
            "",   # biệt danh
            "",   # bài nhạc yêu thích
            "",   # điều tụi mình thích về cậu
            "https://res.cloudinary.com/dogyjotxv/image/upload/v1772003999/nhaky2_yubc2h.png",
            "https://res.cloudinary.com/dogyjotxv/video/upload/v1772207799/D%C3%B9_Cho_Mai_V%E1%BB%81_Sau_Official_Music_Video_buitruonglinh_z2cxcm.mp3",
            "https://res.cloudinary.com/dogyjotxv/image/upload/v1772036596/nhaky1_ce1jio.png",
            "Dù Cho Mai Về Sau ∙ Bùi Trường Linh",   # tên bài trên music bar
            "",   # nội dung thư (letter)
            "",   # URL ảnh thư (letter)
            "",   # gif up
            "",   # gif down
            "",   # gif left
            "",   # gif right
        ),
        (
            "trannguyenngocthienthanh", "Trần Nguyễn Ngọc Thiên Thanh",
            "",   # biệt danh
            "",   # bài nhạc yêu thích
            "",   # điều tụi mình thích về cậu
            "https://res.cloudinary.com/dogyjotxv/image/upload/v1771954084/thienthanh2_rhec6l.png",
            "https://res.cloudinary.com/dogyjotxv/video/upload/v1772210416/MASHUP_ROCK_THI%E1%BB%86P_H%E1%BB%92NG_T%C3%93C_TI%C3%8AN_MAIQUINN_MU%E1%BB%98II_YEOLAN_%C4%80O_T%E1%BB%AC_A1J_x_DTAP_LSX_2025_ryzvda.mp3",
            "https://res.cloudinary.com/dogyjotxv/image/upload/v1772036596/thienthanh1_pizmpn.png",
            "Mashup Rock Thiệp Hổng∙Tóc Tiên x MaiQuinn x Yeolan x Đào Tử A1J",   # tên bài trên music bar
            "",   # nội dung thư (letter)
            "",   # URL ảnh thư (letter)
            "",   # gif up
            "",   # gif down
            "",   # gif left
            "",   # gif right
        ),
        (
            "lungocbich", "Lữ Ngọc Bích",
            "",   # biệt danh
            "",   # bài nhạc yêu thích
            "",   # điều tụi mình thích về cậu
            "https://res.cloudinary.com/dogyjotxv/image/upload/v1771954086/ngocbich2_jyiiqf.png",
            "https://res.cloudinary.com/dogyjotxv/video/upload/v1772209832/Simple_Love_-_Obito_x_Seachains_x_Davis_x_Lena_Official_MV_dkr0vw.mp3",
            "https://res.cloudinary.com/dogyjotxv/image/upload/v1772036596/ngocbich1_picblc.png",
            "Simple Love ∙ Obito x Seachains",   # tên bài trên music bar
            "",   # nội dung thư (letter)
            "",   # URL ảnh thư (letter)
            "",   # gif up
            "",   # gif down
            "",   # gif left
            "",   # gif right
        ),
        (
            "tranhatuyetnhu", "Trần Hà Tuyết Như",
            "",   # biệt danh
            "",   # bài nhạc yêu thích
            "",   # điều tụi mình thích về cậu
            "https://res.cloudinary.com/dogyjotxv/image/upload/v1771954085/tuyetnhu2_ptkhyr.png",
            "https://res.cloudinary.com/dogyjotxv/video/upload/v1772209373/RIO_-_v%E1%BA%A1n_v%E1%BA%ADt_nh%C6%B0_mu%E1%BB%91n_ta_b%C3%AAn_nhau_Official_MV_csfksl.mp3",
            "https://res.cloudinary.com/dogyjotxv/image/upload/v1772030901/tuyetnhu1_dlwi9z.png",
            "Vạn Vật Như Muốn Ta Bên Nhau ∙ RIO",   # tên bài trên music bar
            "",   # nội dung thư (letter)
            "",   # URL ảnh thư (letter)
            "",   # gif up
            "",   # gif down
            "",   # gif left
            "",   # gif right
        ),
        (
            "dothithanhan", "Đỗ Thị Thanh An",
            "",   # biệt danh
            "",   # bài nhạc yêu thích
            "",   # điều tụi mình thích về cậu
            "https://res.cloudinary.com/dogyjotxv/image/upload/v1771954329/cothanhan2_zcahg1.png",
            "https://res.cloudinary.com/dogyjotxv/video/upload/v1772213432/Maroon_5-_Sugar_de74hs.mp3",
            "https://res.cloudinary.com/dogyjotxv/image/upload/v1772036649/cothanhan1_qohuyz.png",
            "Sugar ∙ Maroon5",   # tên bài trên music bar
            "",   # nội dung thư (letter)
            "",   # URL ảnh thư (letter)
            "",   # gif up
            "",   # gif down
            "",   # gif left
            "",   # gif right
        ),
        (
            "tranthihanh", "Trần Thị Hạnh",
            "",   # biệt danh
            "",   # bài nhạc yêu thích
            "",   # điều tụi mình thích về cậu
            "",
            "https://res.cloudinary.com/dxxx/video/upload/v123/womenday/audio/11_music.mp3",
            "",
            "",   # tên bài trên music bar
            "",   # nội dung thư (letter)
            "",   # URL ảnh thư (letter)
            "",   # gif up
            "",   # gif down
            "",   # gif left
            "",   # gif right
        ),
        (
            "dokhanhan", "Đỗ Khánh An",
            "",   # biệt danh
            "",   # bài nhạc yêu thích
            "",   # điều tụi mình thích về cậu
            "",
            "https://res.cloudinary.com/dxxx/video/upload/v123/womenday/audio/12_music.mp3",
            "",
            "",   # tên bài trên music bar
            "",   # nội dung thư (letter)
            "",   # URL ảnh thư (letter)
            "",   # gif up
            "",   # gif down
            "",   # gif left
            "",   # gif right
        ),
        (
            "lieunhuhien", "Liêu Như Hiền",
            "",   # biệt danh
            "",   # bài nhạc yêu thích
            "",   # điều tụi mình thích về cậu
            "https://res.cloudinary.com/dogyjotxv/image/upload/v1772201008/nhuhien2_ue8uc0.png",
            "https://res.cloudinary.com/dogyjotxv/video/upload/v1772211507/Low_G_In_Love_ft._JustaTee_L2K_The_Album_szcc8e.mp3",
            "https://res.cloudinary.com/dogyjotxv/image/upload/v1772201013/nhuhien1_eyfkzu.png",
            "In Love ∙ Low G x JustaTee",   # tên bài trên music bar
            "",   # nội dung thư (letter)
            "",   # URL ảnh thư (letter)
            "",   # gif up
            "",   # gif down
            "",   # gif left
            "",   # gif right
        ),
        (
            "tranyenphuong", "Trần Yến Phương",
            "",   # biệt danh
            "",   # bài nhạc yêu thích
            "",   # điều tụi mình thích về cậu
            "https://res.cloudinary.com/dogyjotxv/image/upload/v1772199597/coyenphuong2_tykgpk.png",
            "https://res.cloudinary.com/dogyjotxv/video/upload/v1772213306/M%E1%BA%B7t_M%E1%BB%99c-VAnh_hqdv3t.mp3",
            "https://res.cloudinary.com/dogyjotxv/image/upload/v1772199593/coyenphuong1_jkkpvx.png",
            "Mặt Mộc ∙ VAnh x Phạm Nguyên Ngọc",   # tên bài trên music bar
            "",   # nội dung thư (letter)
            "",   # URL ảnh thư (letter)
            "",   # gif up
            "",   # gif down
            "",   # gif left
            "",   # gif right
        ),
    ]

    cursor.executemany(
        """INSERT INTO profiles
               (short_name, full_name, nickname, favorite_song, things_we_love,
                layer_url, audio_url, avatar_url, song, letter_content, letter_image_url,
                gif_up, gif_down, gif_left, gif_right)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
           ON CONFLICT(short_name) DO UPDATE SET
               full_name        = excluded.full_name,
               nickname         = excluded.nickname,
               favorite_song    = excluded.favorite_song,
               things_we_love   = excluded.things_we_love,
               layer_url        = excluded.layer_url,
               audio_url        = excluded.audio_url,
               avatar_url       = excluded.avatar_url,
               song             = excluded.song,
               letter_content   = excluded.letter_content,
               letter_image_url = excluded.letter_image_url,
               gif_up           = excluded.gif_up,
               gif_down         = excluded.gif_down,
               gif_left         = excluded.gif_left,
               gif_right        = excluded.gif_right""",
        profiles
    )
    conn.commit()
    conn.close()

init_db()

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

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    name = ''
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
    elif request.method == 'GET':
        name = request.args.get('name', '').strip()

    if not name:
        return render_template('profile.html', profile=None, error="Vui lòng nhập tên")

    norm = normalize_name(name)
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute(
        """SELECT full_name, nickname, favorite_song, things_we_love,
                  layer_url, audio_url, avatar_url, song,
                  gif_up, gif_down, gif_left, gif_right
           FROM profiles WHERE short_name = ?""",
        (norm,)
    )
    row = cursor.fetchone()
    conn.close()

    if row:
        profile_data = {
            'name':           row[0],
            'nickname':       row[1],
            'favorite_song':  row[2],
            'things_we_love': row[3],
            'layer':          row[4],
            'audio':          row[5],
            'avatar':         row[6],
            'song':           row[7],
            'gif_up':         row[8],
            'gif_down':       row[9],
            'gif_left':       row[10],
            'gif_right':      row[11],
        }
        return render_template('profile.html', profile=profile_data)
    else:
        return render_template('profile.html', profile=None, error="Không tìm thấy profile")

@app.route('/letter', methods=['GET'])
def letter():
    name = request.args.get('name', '').strip()

    if not name:
        return render_template('letter.html', profile=None)

    norm = normalize_name(name)
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute(
        """SELECT full_name, letter_content, letter_image_url
           FROM profiles WHERE short_name = ?""",
        (norm,)
    )
    row = cursor.fetchone()
    conn.close()

    if row:
        profile_data = {
            'name':             row[0],
            'letter_content':   row[1],
            'letter_image_url': row[2],
        }
        return render_template('letter.html', profile=profile_data)
    else:
        return render_template('letter.html', profile=None)

@app.route('/source')
def source():
    return render_template('source.html')

@app.route('/link')
def link():
    return render_template('link.html')

@app.route('/api/names')
def get_names():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT full_name FROM profiles")
    names = [row[0] for row in cursor.fetchall()]
    conn.close()
    return jsonify({'names': names})

if __name__ == '__main__':
    try:
        local_ip = socket.gethostbyname(socket.gethostname())
    except:
        local_ip = "127.0.0.1"
    if os.getenv("PORT") is None:
        print("=" * 60)
        print("       TRANG A13 ĐÃ CHẠY THÀNH CÔNG!")
        print("=" * 60)
        print(f"   Local (trên máy bạn):     http://127.0.0.1:5000")
        print(f"   Từ điện thoại/máy khác:   http://{local_ip}:5000")
        print("=" * 60)
        print("   Nhớ cùng kết nối một Wi-Fi nhé ")
        print("   Tắt server: Ctrl + C")
        print("=" * 60)
    app.run(
        host='0.0.0.0',
        port=int(os.getenv("PORT", 5000)),
        debug=(os.getenv("PORT") is None),
        use_reloader=(os.getenv("PORT") is None)
    )
