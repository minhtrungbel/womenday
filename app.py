from flask import Flask, render_template, request, jsonify
import os
import sqlite3
import unicodedata
import cloudinary
import cloudinary.uploader
from dotenv import load_dotenv
import socket
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

load_dotenv()

cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
    secure=True
)

app = Flask(__name__, template_folder='templates', static_folder='static')

# Gioi han API: 100 request / phut / IP
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=[],
    storage_uri="memory://"
)

def normalize_name(name):
    name = name.strip().lower()
    name = ''.join(c for c in unicodedata.normalize('NFD', name) if unicodedata.category(c) != 'Mn')
    replacements = {'\u0111': 'd', '\u01a1': 'o', '\u01b0': 'u', '\u0103': 'a', '\u00e2': 'a', '\u00ea': 'e', '\u00f4': 'o'}
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

    # Migration an toan: tu them cot moi neu DB cu chua co
    existing_columns = [row[1] for row in cursor.execute("PRAGMA table_info(profiles)").fetchall()]
    for col, col_type in [
        ("nickname",         "TEXT"),
        ("favorite_song",    "TEXT"),
        ("things_we_love",   "TEXT"),
        ("song",             "TEXT"),
        ("letter_content",   "TEXT"),   # noi dung thu — dung trong trang letter
        ("letter_image_url", "TEXT"),   # anh thu — dung trong trang letter
        ("gif_up",           "TEXT"),   # gif di chuyen len
        ("gif_down",         "TEXT"),   # gif di chuyen xuong
        ("gif_left",         "TEXT"),   # gif di chuyen ngang trai
        ("gif_right",        "TEXT"),   # gif di chuyen ngang phai
        ("gift_password",    "TEXT"),   # [15] mat khau mo hop qua trang /letter
        ("gift_image",       "TEXT"),   # [16] URL anh ruot hop qua (lop duoi nap)
    ]:
        if col not in existing_columns:
            cursor.execute(f"ALTER TABLE profiles ADD COLUMN {col} {col_type} DEFAULT ''")

    # ==============================================================
    # THU TU COT TRONG TUPLE (17 gia tri, theo dung thu tu INSERT):
    #   [0]  short_name        -- ten viet lien khong dau, dung trong URL (?name=...)
    #   [1]  full_name         -- ho ten day du hien thi trong info card & thu
    #   [2]  nickname          -- biet danh (de trong "" neu chua co)
    #   [3]  favorite_song     -- bai nhac yeu thich hien thi trong info card
    #   [4]  things_we_love    -- dieu tui minh thich ve cau (info card)
    #   [5]  layer_url         -- URL anh layer nen avatar (Cloudinary PNG)
    #   [6]  audio_url         -- URL file nhac MP3 (Cloudinary video)
    #   [7]  avatar_url        -- URL anh avatar chinh (Cloudinary PNG)
    #   [8]  song              -- ten bai chay tren music bar, vd: "Ten bai . Ca si"
    #   [9]  letter_content    -- noi dung thu tay (hien thi trang /letter)
    #   [10] letter_image_url  -- URL anh minh hoa trong thu (de trong neu khong dung)
    #   [11] gif_up            -- URL gif di chuyen len (animation tren profile)
    #   [12] gif_down          -- URL gif di chuyen xuong
    #   [13] gif_left          -- URL gif di chuyen sang trai
    #   [14] gif_right         -- URL gif di chuyen sang phai
    #   [15] gift_password     -- mat khau mo hop qua tren trang /letter
    #   [16] gift_image        -- URL anh ruot hop qua (lop duoi nap, Cloudinary PNG)
    # ==============================================================
    profiles = [
        (
            "vobaotran",          # [0]  short_name
            "Võ Bảo Trân",          # [1]  full_name
            "",          # [2]  nickname
            "",          # [3]  favorite_song
            "",          # [4]  things_we_love
            "https://res.cloudinary.com/dogyjotxv/image/upload/v1771951780/votran2_rcmb4w.png",          # [5]  layer_url
            "https://res.cloudinary.com/dogyjotxv/video/upload/v1772207141/VSTRA_-_Ai_Ngo%C3%A0i_Anh_Official_Audio_j8abwy.mp3",          # [6]  audio_url
            "https://res.cloudinary.com/dogyjotxv/image/upload/v1772022864/votran1_bgdgxr.png",          # [7]  avatar_url
            "Ai Ngoài Anh ∙ VSTRA",          # [8]  song
            "",          # [9]  letter_content
            "",          # [10] letter_image_url
            "",          # [11] gif_up
            "",          # [12] gif_down
            "",          # [13] gif_left
            "",          # [14] gif_right
            "0308",          # [15] gift_password
            "https://res.cloudinary.com/dogyjotxv/image/upload/v1772539394/qua1_ko17hc.png",          # [16] gift_image
        ),
        (
            "lenguyenbaotran",          # [0]  short_name
            "Lê Nguyễn Bảo Trân",          # [1]  full_name
            "",          # [2]  nickname
            "",          # [3]  favorite_song
            "",          # [4]  things_we_love
            "https://res.cloudinary.com/dogyjotxv/image/upload/v1771954229/letran2_epjgp6.png",          # [5]  layer_url
            "https://res.cloudinary.com/dogyjotxv/video/upload/v1772206464/Ph%C3%A1o_Northside-M%E1%BB%99t_Ng%C3%A0y_Ch%E1%BA%B3ng_N%E1%BA%AFng_ft.thobaymauofficial_Official_MV_hwkpvk.mp3",          # [6]  audio_url
            "https://res.cloudinary.com/dogyjotxv/image/upload/v1772036653/letran1_xkztjc.png",          # [7]  avatar_url
            "Một Ngày Chẳng Nắng ∙ Pháo Northside",          # [8]  song
            "",          # [9]  letter_content
            "",          # [10] letter_image_url
            "",          # [11] gif_up
            "",          # [12] gif_down
            "",          # [13] gif_left
            "",          # [14] gif_right
            "0308",          # [15] gift_password
            "https://res.cloudinary.com/dogyjotxv/image/upload/v1772539394/qua1_ko17hc.png",          # [16] gift_image
        ),
        (
            "buikieuanh",          # [0]  short_name
            "Bùi Kiều Anh",          # [1]  full_name
            "",          # [2]  nickname
            "https://res.cloudinary.com/dogyjotxv/video/upload/v1772454983/Nghe_nh%C6%B0_t%C3%ACnh_y%C3%AAu_-_MCK_remixx_prod_mp3cut.net_wppsbw.mp3",          # [3]  favorite_song
            "",          # [4]  things_we_love
            "https://res.cloudinary.com/dogyjotxv/image/upload/v1771954223/kieuanh2_qlujkd.png",          # [5]  layer_url
            "https://res.cloudinary.com/dogyjotxv/video/upload/v1772454983/Nghe_nh%C6%B0_t%C3%ACnh_y%C3%AAu_-_MCK_remixx_prod_mp3cut.net_wppsbw.mp3",          # [6]  audio_url
            "https://res.cloudinary.com/dogyjotxv/image/upload/v1772036650/kieuanh1_tcql5x.png",          # [7]  avatar_url
            "Nghe Như Tình Yêu ∙ MCK",          # [8]  song
            "",          # [9]  letter_content
            "",          # [10] letter_image_url
            "https://res.cloudinary.com/dogyjotxv/image/upload/v1772294406/Buoc_Toc_-_Up_fekvlr.gif",          # [11] gif_up
            "https://res.cloudinary.com/dogyjotxv/image/upload/v1772294406/Buoc_Toc_-_Down_gpwews.gif",          # [12] gif_down
            "https://res.cloudinary.com/dogyjotxv/image/upload/v1772725128/Xoa_Toc_-_Left_wezif7.gif",          # [13] gif_left
            "https://res.cloudinary.com/dogyjotxv/image/upload/v1772725128/Xoa_Toc_-_Right_pljrjz.gif",          # [14] gif_right
            "0308",          # [15] gift_password
            "https://res.cloudinary.com/dogyjotxv/image/upload/v1772539394/qua1_ko17hc.png",          # [16] gift_image
        ),
        (
            "trinhngocgialinh",          # [0]  short_name
            "Trịnh Ngọc Gia Linh",          # [1]  full_name
            "",          # [2]  nickname
            "",          # [3]  favorite_song
            "",          # [4]  things_we_love
            "https://res.cloudinary.com/dogyjotxv/image/upload/v1772113738/gialinh2_1_k4bes6.png",          # [5]  layer_url
            "https://res.cloudinary.com/dogyjotxv/video/upload/v1772212283/GO-CORTIS_yfqtlh.mp3",          # [6]  audio_url
            "https://res.cloudinary.com/dogyjotxv/image/upload/v1772036650/gialinh1_nfsmt0.png",          # [7]  avatar_url
            "GO ∙ CORTIS",          # [8]  song
            "",          # [9]  letter_content
            "",          # [10] letter_image_url
            "",          # [11] gif_up
            "",          # [12] gif_down
            "",          # [13] gif_left
            "",          # [14] gif_right
            "0308",          # [15] gift_password
            "https://res.cloudinary.com/dogyjotxv/image/upload/v1772539394/qua1_ko17hc.png",          # [16] gift_image
        ),
        (
            "huynhnguyenkimngan",          # [0]  short_name
            "Huỳnh Nguyễn Kim Ngân",          # [1]  full_name
            "",          # [2]  nickname
            "",          # [3]  favorite_song
            "",          # [4]  things_we_love
            "https://res.cloudinary.com/dogyjotxv/image/upload/v1771954221/kimngan2_tsqlkc.png",          # [5]  layer_url
            "https://res.cloudinary.com/dogyjotxv/video/upload/v1772210869/PUPPY_DANGRANGTO_-_WRONG_TIMES_Live_at_LAB_RADAR_ZLAB_fp0cc6.mp3",          # [6]  audio_url
            "https://res.cloudinary.com/dogyjotxv/image/upload/v1772036653/kimngan1_lbbfmu.png",          # [7]  avatar_url
            "Wrong Times ∙ Young Puppy x DANGRANGTO",          # [8]  song
            "",          # [9]  letter_content
            "",          # [10] letter_image_url
            "",          # [11] gif_up
            "",          # [12] gif_down
            "",          # [13] gif_left
            "",          # [14] gif_right
            "10082009hnkn",          # [15] gift_password
            "https://res.cloudinary.com/dogyjotxv/image/upload/v1772539394/qua1_ko17hc.png",          # [16] gift_image
        ),
        (
            "lengocnhaky",          # [0]  short_name
            "Lê Ngọc Nhã Kỳ",          # [1]  full_name
            "",          # [2]  nickname
            "",          # [3]  favorite_song
            "",          # [4]  things_we_love
            "https://res.cloudinary.com/dogyjotxv/image/upload/v1772003999/nhaky2_yubc2h.png",          # [5]  layer_url
            "https://res.cloudinary.com/dogyjotxv/video/upload/v1772207799/D%C3%B9_Cho_Mai_V%E1%BB%81_Sau_Official_Music_Video_buitruonglinh_z2cxcm.mp3",          # [6]  audio_url
            "https://res.cloudinary.com/dogyjotxv/image/upload/v1772036596/nhaky1_ce1jio.png",          # [7]  avatar_url
            "Dù Cho Mai Về Sau ∙ Bùi Trường Linh",          # [8]  song
            "",          # [9]  letter_content
            "",          # [10] letter_image_url
            "",          # [11] gif_up
            "",          # [12] gif_down
            "",          # [13] gif_left
            "",          # [14] gif_right
            "0308",          # [15] gift_password
            "https://res.cloudinary.com/dogyjotxv/image/upload/v1772539394/qua1_ko17hc.png",          # [16] gift_image
        ),
        (
            "trannguyenngocthienthanh",          # [0]  short_name
            "Trần Nguyễn Ngọc Thiên Thanh",          # [1]  full_name
            "",          # [2]  nickname
            "",          # [3]  favorite_song
            "",          # [4]  things_we_love
            "https://res.cloudinary.com/dogyjotxv/image/upload/v1771954084/thienthanh2_rhec6l.png",          # [5]  layer_url
            "https://res.cloudinary.com/dogyjotxv/video/upload/v1772210416/MASHUP_ROCK_THI%E1%BB%86P_H%E1%BB%92NG_T%C3%93C_TI%C3%8AN_MAIQUINN_MU%E1%BB%98II_YEOLAN_%C4%90%C3%80O_T%E1%BB%AC_A1J_x_DTAP_LSX_2025_ryzvda.mp3",          # [6]  audio_url
            "https://res.cloudinary.com/dogyjotxv/image/upload/v1772036596/thienthanh1_pizmpn.png",          # [7]  avatar_url
            "Mashup Rock Thiệp Hổng ∙ Tóc Tiên x MaiQuinn x Yeolan x Đào Tử A1J",          # [8]  song
            "",          # [9]  letter_content
            "",          # [10] letter_image_url
            "",          # [11] gif_up
            "",          # [12] gif_down
            "",          # [13] gif_left
            "",          # [14] gif_right
            "0308",          # [15] gift_password
            "https://res.cloudinary.com/dogyjotxv/image/upload/v1772539394/qua1_ko17hc.png",          # [16] gift_image
        ),
        (
            "lungocbich",          # [0]  short_name
            "Lữ Ngọc Bích",          # [1]  full_name
            "",          # [2]  nickname
            "",          # [3]  favorite_song
            "",          # [4]  things_we_love
            "https://res.cloudinary.com/dogyjotxv/image/upload/v1771954086/ngocbich2_jyiiqf.png",          # [5]  layer_url
            "https://res.cloudinary.com/dogyjotxv/video/upload/v1772209832/Simple_Love_-_Obito_x_Seachains_x_Davis_x_Lena_Official_MV_dkr0vw.mp3",          # [6]  audio_url
            "https://res.cloudinary.com/dogyjotxv/image/upload/v1772036596/ngocbich1_picblc.png",          # [7]  avatar_url
            "Simple Love ∙ Obito x Seachains",          # [8]  song
            "",          # [9]  letter_content
            "",          # [10] letter_image_url
            "",          # [11] gif_up
            "",          # [12] gif_down
            "",          # [13] gif_left
            "",          # [14] gif_right
            "0308",          # [15] gift_password
            "https://res.cloudinary.com/dogyjotxv/image/upload/v1772539394/qua1_ko17hc.png",          # [16] gift_image
        ),
        (
            "tranhatuyetnhu",          # [0]  short_name
            "Trần Hà Tuyết Như",          # [1]  full_name
            "",          # [2]  nickname
            "",          # [3]  favorite_song
            "",          # [4]  things_we_love
            "https://res.cloudinary.com/dogyjotxv/image/upload/v1771954085/tuyetnhu2_ptkhyr.png",          # [5]  layer_url
            "https://res.cloudinary.com/dogyjotxv/video/upload/v1772209373/RIO_-_v%E1%BA%A1n_v%E1%BA%ADt_nh%C6%B0_mu%E1%BB%91n_ta_b%C3%AAn_nhau_Official_MV_csfksl.mp3",          # [6]  audio_url
            "https://res.cloudinary.com/dogyjotxv/image/upload/v1772030901/tuyetnhu1_dlwi9z.png",          # [7]  avatar_url
            "Vạn Vật Như Muốn Ta Bên Nhau ∙ RIO",          # [8]  song
            "",          # [9]  letter_content
            "",          # [10] letter_image_url
            "",          # [11] gif_up
            "",          # [12] gif_down
            "",          # [13] gif_left
            "",          # [14] gif_right
            "0308",          # [15] gift_password
            "https://res.cloudinary.com/dogyjotxv/image/upload/v1772539394/qua1_ko17hc.png",          # [16] gift_image
        ),
        (
            "dothithanhan",          # [0]  short_name
            "Đỗ Thị Thanh An",          # [1]  full_name
            "",          # [2]  nickname
            "",          # [3]  favorite_song
            "",          # [4]  things_we_love
            "https://res.cloudinary.com/dogyjotxv/image/upload/v1771954329/cothanhan2_zcahg1.png",          # [5]  layer_url
            "https://res.cloudinary.com/dogyjotxv/video/upload/v1772213432/Maroon_5-_Sugar_de74hs.mp3",          # [6]  audio_url
            "https://res.cloudinary.com/dogyjotxv/image/upload/v1772036649/cothanhan1_qohuyz.png",          # [7]  avatar_url
            "Sugar ∙ Maroon5",          # [8]  song
            "",          # [9]  letter_content
            "",          # [10] letter_image_url
            "",          # [11] gif_up
            "",          # [12] gif_down
            "",          # [13] gif_left
            "",          # [14] gif_right
            "0308",          # [15] gift_password
            "https://res.cloudinary.com/dogyjotxv/image/upload/v1772539394/qua1_ko17hc.png",          # [16] gift_image
        ),
        (
            "tranthihanh",          # [0]  short_name
            "Trần Thị Hạnh",          # [1]  full_name
            "",          # [2]  nickname
            "",          # [3]  favorite_song
            "",          # [4]  things_we_love
            "",          # [5]  layer_url
            "https://res.cloudinary.com/dxxx/video/upload/v123/womenday/audio/11_music.mp3",          # [6]  audio_url
            "",          # [7]  avatar_url
            "",          # [8]  song
            "",          # [9]  letter_content
            "",          # [10] letter_image_url
            "",          # [11] gif_up
            "",          # [12] gif_down
            "",          # [13] gif_left
            "",          # [14] gif_right
            "0308",          # [15] gift_password
            "https://res.cloudinary.com/dogyjotxv/image/upload/v1772539394/qua1_ko17hc.png",          # [16] gift_image
        ),
        (
            "dokhanhan",          # [0]  short_name
            "Đỗ Khánh An",          # [1]  full_name
            "",          # [2]  nickname
            "",          # [3]  favorite_song
            "",          # [4]  things_we_love
            "",          # [5]  layer_url
            "https://res.cloudinary.com/dxxx/video/upload/v123/womenday/audio/12_music.mp3",          # [6]  audio_url
            "",          # [7]  avatar_url
            "",          # [8]  song
            "",          # [9]  letter_content
            "",          # [10] letter_image_url
            "",          # [11] gif_up
            "",          # [12] gif_down
            "",          # [13] gif_left
            "",          # [14] gif_right
            "0308",          # [15] gift_password
            "https://res.cloudinary.com/dogyjotxv/image/upload/v1772539394/qua1_ko17hc.png",          # [16] gift_image
        ),
        (
            "lieunhuhien",          # [0]  short_name
            "Liêu Như Hiền",          # [1]  full_name
            "",          # [2]  nickname
            "",          # [3]  favorite_song
            "",          # [4]  things_we_love
            "https://res.cloudinary.com/dogyjotxv/image/upload/v1772201008/nhuhien2_ue8uc0.png",          # [5]  layer_url
            "https://res.cloudinary.com/dogyjotxv/video/upload/v1772211507/Low_G_In_Love_ft._JustaTee_L2K_The_Album_szcc8e.mp3",          # [6]  audio_url
            "https://res.cloudinary.com/dogyjotxv/image/upload/v1772201013/nhuhien1_eyfkzu.png",          # [7]  avatar_url
            "In Love ∙ Low G x JustaTee",          # [8]  song
            "",          # [9]  letter_content
            "",          # [10] letter_image_url
            "",          # [11] gif_up
            "",          # [12] gif_down
            "",          # [13] gif_left
            "",          # [14] gif_right
            "0308",          # [15] gift_password
            "https://res.cloudinary.com/dogyjotxv/image/upload/v1772539394/qua1_ko17hc.png",          # [16] gift_image
        ),
        (
            "tranyenphuong",          # [0]  short_name
            "Trần Yến Phương",          # [1]  full_name
            "",          # [2]  nickname
            "",          # [3]  favorite_song
            "",          # [4]  things_we_love
            "https://res.cloudinary.com/dogyjotxv/image/upload/v1772199597/coyenphuong2_tykgpk.png",          # [5]  layer_url
            "https://res.cloudinary.com/dogyjotxv/video/upload/v1772213306/M%E1%BA%B7t_M%E1%BB%99c-VAnh_hqdv3t.mp3",          # [6]  audio_url
            "https://res.cloudinary.com/dogyjotxv/image/upload/v1772199593/coyenphuong1_jkkpvx.png",          # [7]  avatar_url
            "Mặt Mộc ∙ VAnh x Phạm Nguyên Ngọc",          # [8]  song
            "",          # [9]  letter_content
            "",          # [10] letter_image_url
            "",          # [11] gif_up
            "",          # [12] gif_down
            "",          # [13] gif_left
            "",          # [14] gif_right
            "0308",          # [15] gift_password
            "https://res.cloudinary.com/dogyjotxv/image/upload/v1772539394/qua1_ko17hc.png",          # [16] gift_image
        ),
    ]

    cursor.executemany(
        """INSERT INTO profiles
               (short_name, full_name, nickname, favorite_song, things_we_love,
                layer_url, audio_url, avatar_url, song, letter_content, letter_image_url,
                gif_up, gif_down, gif_left, gif_right,
                gift_password, gift_image)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
               gif_right        = excluded.gif_right,
               gift_password    = excluded.gift_password,
               gift_image       = excluded.gift_image""",
        profiles
    )
    conn.commit()
    conn.close()

init_db()

@app.errorhandler(429)
def ratelimit_handler(e):
    return jsonify(error="Quá nhiều yêu cầu, vui lòng thử lại sau.", retry_after=60), 429

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
        """SELECT full_name, letter_content, letter_image_url,
                  gift_password, gift_image
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
            'gift_password':    row[3],   # [15] mat khau mo hop qua
            'gift_image':       row[4],   # [16] anh ruot hop qua
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
@limiter.limit("100 per minute")
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
        print("       TRANG A13 DA CHAY THANH CONG!")
        print("=" * 60)
        print(f"   Local (tren may ban):     http://127.0.0.1:5000")
        print(f"   Tu dien thoai/may khac:   http://{local_ip}:5000")
        print("=" * 60)
        print("   Nho cung ket noi mot Wi-Fi nhe ")
        print("   Tat server: Ctrl + C")
        print("=" * 60)
    app.run(
        host='0.0.0.0',
        port=int(os.getenv("PORT", 5000)),
        debug=(os.getenv("PORT") is None),
        use_reloader=(os.getenv("PORT") is None)
    )

