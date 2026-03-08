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
        ("profile_password", "TEXT"),   # [17] mat khau mo trang profile (bao ve profile)
    ]:
        if col not in existing_columns:
            cursor.execute(f"ALTER TABLE profiles ADD COLUMN {col} {col_type} DEFAULT ''")

    # ==============================================================
    # THU TU COT TRONG TUPLE (17 gia tri, theo dung thu tu INSERT):
    #   [0]  short_name        -- ten viet lien khong dau, dung trong URL (?name=...)
    #   [1]  full_name         -- ho ten day du hien thi trong info card & thu
    #   [2]  nickname          -- biet danh (de trong "" neu chua co)
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
    #                             RONG ("") = khong can mat khau, mo thang nap
    #   [16] gift_image        -- URL anh ruot hop qua (lop duoi nap, Cloudinary PNG)
    #   [17] profile_password  -- mat khau bao ve trang /profile (hien popup ngay khi vao)
    #                             RONG ("") = khong can mat khau de xem profile
    # ==============================================================
    profiles = [
        (
            "vobaotran",          # [0]  short_name
            "Võ Bảo Trân",          # [1]  full_name
            "Biệt danh: UwU",          # [2]  nickname
            "Điều chúng tớ thích về cậu:thân thiện,hòa đồng,luôn hỗ trợ các bạn trong học tập",          # [4]  things_we_love
            "https://res.cloudinary.com/dogyjotxv/image/upload/v1771951780/votran2_rcmb4w.png",          # [5]  layer_url
            "https://res.cloudinary.com/dogyjotxv/video/upload/v1772207141/VSTRA_-_Ai_Ngo%C3%A0i_Anh_Official_Audio_j8abwy.mp3",          # [6]  audio_url
            "https://res.cloudinary.com/dogyjotxv/image/upload/v1772022864/votran1_bgdgxr.png",          # [7]  avatar_url
            "Ai Ngoài Anh ∙ VSTRA",          # [8]  song
            "Tụi mình muốn gửi lời cảm ơn chân thành đến Trân vì đã luôn là một mảnh ghép tuyệt vời trong tình bạn của chúng mình. Bà là một người rất dễ gần và vui tính. Chúc Võ Trân luôn cố gắng, học tập thật “siêu cấp” và lúc nào cũng gặp nhiều may mắn trên con đường sắp tới.",          # [9]  letter_content
            "",          # [10] letter_image_url
            "https://res.cloudinary.com/dogyjotxv/image/upload/v1772986569/Buoc_Toc_-_Up_1_muf6le.gif",          # [11] gif_up
            "https://res.cloudinary.com/dogyjotxv/image/upload/v1772986569/Buoc_Toc_-_Down_1_bamcqb.gif",          # [12] gif_down
            "https://res.cloudinary.com/dogyjotxv/image/upload/v1772986489/Buoc_Toc_alt_-_Left_1_mscldt.gif",          # [13] gif_left
            "https://res.cloudinary.com/dogyjotxv/image/upload/v1772986489/Buoc_Toc_alt_-_Right_a3bc2i.gif",          # [14] gif_right
            "@27112009uwu@",          # [15] gift_password
            "https://res.cloudinary.com/dogyjotxv/image/upload/v1772539394/qua1_ko17hc.png",          # [16] gift_image
            "",          # [17] profile_password
        ),
        (
            "lenguyenbaotran",          # [0]  short_name
            "Lê Nguyễn Bảo Trân",          # [1]  full_name
            "Biệt danh: Mai Lê",          # [2]  nickname
            "Điều chúng tớ thích về cậu:sự cá tính, hoạt bát và tự tin của cậu",          # [4]  things_we_love
            "https://res.cloudinary.com/dogyjotxv/image/upload/v1771954229/letran2_epjgp6.png",          # [5]  layer_url
            "https://res.cloudinary.com/dogyjotxv/video/upload/v1772206464/Ph%C3%A1o_Northside-M%E1%BB%99t_Ng%C3%A0y_Ch%E1%BA%B3ng_N%E1%BA%AFng_ft.thobaymauofficial_Official_MV_hwkpvk.mp3",          # [6]  audio_url
            "https://res.cloudinary.com/dogyjotxv/image/upload/v1772036653/letran1_xkztjc.png",          # [7]  avatar_url
            "Một Ngày Chẳng Nắng ∙ Pháo Northside",          # [8]  song
            "Tụi mình muốn gửi lời cảm ơn chân thành đến Lê trân  vì đã luôn là một người bạn dễ thương và chân thành trong lớp. Những khoảnh khắc học tập và sinh hoạt cùng nhau đều là những kỷ niệm rất đáng quý. Chúc Lê Trân luôn vui vẻ, tự tin với bản thân mình và đạt được thật nhiều thành công trong học tập cũng như trong những dự định sắp tới nhé!",          # [9]  letter_content
            "",          # [10] letter_image_url
            "https://res.cloudinary.com/dogyjotxv/image/upload/v1772986569/Buoc_Toc_-_Up_1_muf6le.gif",          # [11] gif_up
            "https://res.cloudinary.com/dogyjotxv/image/upload/v1772986569/Buoc_Toc_-_Down_1_bamcqb.gif",          # [12] gif_down
            "https://res.cloudinary.com/dogyjotxv/image/upload/v1772987842/Buoc_Toc_-_Left_1_yifu8x.gif",          # [13] gif_left
            "https://res.cloudinary.com/dogyjotxv/image/upload/v1772987842/Buoc_Toc_-_Right_brceuy.gif",          # [14] gif_right
            "@29012009maile@",          # [15] gift_password
            "https://res.cloudinary.com/dogyjotxv/image/upload/v1772539394/qua1_ko17hc.png",          # [16] gift_image
            "",          # [17] profile_password
        ),
        (
            "buikieuanh",          # [0]  short_name
            "Bùi Kiều Anh",          # [1]  full_name
            "Biệt danh: pie",          # [2]  nickname
            "Điều chúng tớ thích về cậu: sự vui tính, học giỏi, dễ thương của cậu",          # [4]  things_we_love
            "https://res.cloudinary.com/dogyjotxv/image/upload/v1771954223/kieuanh2_qlujkd.png",          # [5]  layer_url
            "https://res.cloudinary.com/dogyjotxv/video/upload/v1772454983/Nghe_nh%C6%B0_t%C3%ACnh_y%C3%AAu_-_MCK_remixx_prod_mp3cut.net_wppsbw.mp3",          # [6]  audio_url
            "https://res.cloudinary.com/dogyjotxv/image/upload/v1772036650/kieuanh1_tcql5x.png",          # [7]  avatar_url
            "Nghe Như Tình Yêu ∙ MCK",          # [8]  song
            "Tụi mình muốn gửi lời cảm ơn chân thành đến Kiều Anh vì đã luôn là một người bạn dễ mến và hòa đồng trong lớp, lúc nào cũng cảm thấy không khí nhẹ nhàng và vui vẻ hơn hẳn. Chúc Kiều Anh luôn tự tin, học tập thật tốt và lúc nào cũng giữ được năng lượng tích cực của mình. Mong là trong những bài kiểm tra sắp tới, sẽ có thể “thu hoạch” thật nhiều điểm cao để còn khoe với cả lớp nữa nha!",          # [9]  letter_content
            "",          # [10] letter_image_url
            "https://res.cloudinary.com/dogyjotxv/image/upload/v1772989988/Xoa_Toc_-_Up_lmg6qu.gif",          # [11] gif_up
            "https://res.cloudinary.com/dogyjotxv/image/upload/v1772989988/Xoa_Toc_-_Down_vsmfgx.gif",          # [12] gif_down
            "https://res.cloudinary.com/dogyjotxv/image/upload/v1772725128/Xoa_Toc_-_Left_wezif7.gif",          # [13] gif_left
            "https://res.cloudinary.com/dogyjotxv/image/upload/v1772725128/Xoa_Toc_-_Right_pljrjz.gif",          # [14] gif_right
            "@10052009pie@",          # [15] gift_password
            "https://res.cloudinary.com/dogyjotxv/image/upload/v1772539394/qua1_ko17hc.png",          # [16] gift_image
            "",          # [17] profile_password
        ),
        (
            "trinhngocgialinh",          # [0]  short_name
            "Trịnh Ngọc Gia Linh",          # [1]  full_name
            "Biệt danh: chocosusu",          # [2]  nickname
            "Điều chúng tớ thích về cậu:sự thân thiện vui vẻ hòa đồng và hay chơi game cùng chúng tớ",          # [4]  things_we_love
            "https://res.cloudinary.com/dogyjotxv/image/upload/v1772113738/gialinh2_1_k4bes6.png",          # [5]  layer_url
            "https://res.cloudinary.com/dogyjotxv/video/upload/v1772212283/GO-CORTIS_yfqtlh.mp3",          # [6]  audio_url
            "https://res.cloudinary.com/dogyjotxv/image/upload/v1772036650/gialinh1_nfsmt0.png",          # [7]  avatar_url
            "GO ∙ CORTIS",          # [8]  song
            "Tụi mình muốn gửi lời cảm ơn chân thành Linh vì sự thẳng thắn và luôn hết mình với bạn bè. Những lời góp ý hay sự cổ vũ của bà có ý nghĩa rất lớn . Chúc Gia Linh luôn thông minh, nhạy bén và ngày càng tỏa sáng với những thế mạnh riêng của bản thân nha!",          # [9]  letter_content
            "",          # [10] letter_image_url
            "https://res.cloudinary.com/dogyjotxv/image/upload/v1772989988/Xoa_Toc_-_Up_lmg6qu.gif",          # [11] gif_up
            "https://res.cloudinary.com/dogyjotxv/image/upload/v1772989988/Xoa_Toc_-_Down_vsmfgx.gif",          # [12] gif_down
            "https://res.cloudinary.com/dogyjotxv/image/upload/v1772725128/Xoa_Toc_-_Left_wezif7.gif",          # [13] gif_left
            "https://res.cloudinary.com/dogyjotxv/image/upload/v1772725128/Xoa_Toc_-_Right_pljrjz.gif",          # [14] gif_right
            "@13022009chocosusu@",          # [15] gift_password
            "https://res.cloudinary.com/dogyjotxv/image/upload/v1772539394/qua1_ko17hc.png",          # [16] gift_image
            "",          # [17] profile_password
        ),
        (
            "huynhnguyenkimngan",          # [0]  short_name
            "Huỳnh Nguyễn Kim Ngân",          # [1]  full_name
            "Biệt danh: nolan, con bò đầu cọ",          # [2]  nickname
            "Điều chúng tớ thích về cậu:năng động,dễ thương,luôn giúp đỡ tích cực mọi người trong công việc ",          # [4]  things_we_love
            "https://res.cloudinary.com/dogyjotxv/image/upload/v1771954221/kimngan2_tsqlkc.png",          # [5]  layer_url
            "https://res.cloudinary.com/dogyjotxv/video/upload/v1772210869/PUPPY_DANGRANGTO_-_WRONG_TIMES_Live_at_LAB_RADAR_ZLAB_fp0cc6.mp3",          # [6]  audio_url
            "https://res.cloudinary.com/dogyjotxv/image/upload/v1772036653/kimngan1_lbbfmu.png",          # [7]  avatar_url
            "Wrong Times ∙ Young Puppy x DANGRANGTO",          # [8]  song
            " Tụi mình muốn gửi lời cảm ơn chân thành đến Ngân vì đã luôn thân thiện và nhiệt tình với mọi người trong lớp. Bà không chỉ là thủ quỹ đầy cẩn thận của lớp mà còn là một kỹ sư vô cùng chăm chỉ. Chúc Kim Ngân luôn vui vẻ, học hành thuận lợi và ngày càng phát huy được những điểm mạnh của bản thân. Mong là sắp tới bà sẽ tiếp tục “tỏa sáng” trong lớp mình nha!",          # [9]  letter_content
            "",          # [10] letter_image_url
            "https://res.cloudinary.com/dogyjotxv/image/upload/v1772989988/Xoa_Toc_-_Up_lmg6qu.gif",          # [11] gif_up
            "https://res.cloudinary.com/dogyjotxv/image/upload/v1772989988/Xoa_Toc_-_Down_vsmfgx.gif",          # [12] gif_down
            "https://res.cloudinary.com/dogyjotxv/image/upload/v1772725128/Xoa_Toc_-_Left_wezif7.gif",          # [13] gif_left
            "https://res.cloudinary.com/dogyjotxv/image/upload/v1772725128/Xoa_Toc_-_Right_pljrjz.gif",          # [14] gif_right
            "@10082009nolanchris@",          # [15] gift_password
            "https://res.cloudinary.com/dogyjotxv/image/upload/v1772539394/qua1_ko17hc.png",          # [16] gift_image
            "",          # [17] profile_password
        ),
        (
            "lengocnhaky",          # [0]  short_name
            "Lê Ngọc Nhã Kỳ",          # [1]  full_name
            "Biệt danh: lowkỳ(lowkey)",          # [2]  nickname
            "Điều chúng tớ thích về cậu:sự điềm đạm trầm tính,vui vẻ thân thiện của cậu khi làm việc nhóm cùng cậu",          # [4]  things_we_love
            "https://res.cloudinary.com/dogyjotxv/image/upload/v1772003999/nhaky2_yubc2h.png",          # [5]  layer_url
            "https://res.cloudinary.com/dogyjotxv/video/upload/v1772207799/D%C3%B9_Cho_Mai_V%E1%BB%81_Sau_Official_Music_Video_buitruonglinh_z2cxcm.mp3",          # [6]  audio_url
            "https://res.cloudinary.com/dogyjotxv/image/upload/v1772036596/nhaky1_ce1jio.png",          # [7]  avatar_url
            "Dù Cho Mai Về Sau ∙ Bùi Trường Linh",          # [8]  song
            "Tụi mình muốn gửi lời cảm ơn chân thành đến Kỳ vì đã luôn là một người bạn điềm đạm và đáng tin cậy. Không chỉ bà luôn là người giữ vững kết quả hoc tập tốt trong lớp mà còn là người rất thân thiện và hài hước. Chúc Nhã Kỳ luôn giữ được sự nhẹ nhàng, tự tin và gặt hái được thật nhiều điểm 10 trong các bài kiểm tra sắp tới.",          # [9]  letter_content
            "",          # [10] letter_image_url
            "https://res.cloudinary.com/dogyjotxv/image/upload/v1772986569/Buoc_Toc_-_Up_1_muf6le.gif",          # [11] gif_up
            "https://res.cloudinary.com/dogyjotxv/image/upload/v1772986569/Buoc_Toc_-_Down_1_bamcqb.gif",          # [12] gif_down
            "https://res.cloudinary.com/dogyjotxv/image/upload/v1772987842/Buoc_Toc_-_Left_1_yifu8x.gif ",          # [13] gif_left
            "https://res.cloudinary.com/dogyjotxv/image/upload/v1772987842/Buoc_Toc_-_Right_brceuy.gif",          # [14] gif_right
            "@20102009lnnk@",          # [15] gift_password
            "https://res.cloudinary.com/dogyjotxv/image/upload/v1772539394/qua1_ko17hc.png",          # [16] gift_image
            "",          # [17] profile_password
        ),
        (
            "trannguyenngocthienthanh",          # [0]  short_name
            "Trần Nguyễn Ngọc Thiên Thanh",          # [1]  full_name
            "Biệt danh: Trần Meo",          # [2]  nickname
            "Điều chúng tớ thích về cậu:sự hài hước và vui tính của cậu",          # [4]  things_we_love
            "https://res.cloudinary.com/dogyjotxv/image/upload/v1771954084/thienthanh2_rhec6l.png",          # [5]  layer_url
            "https://res.cloudinary.com/dogyjotxv/video/upload/v1772210416/MASHUP_ROCK_THI%E1%BB%86P_H%E1%BB%92NG_T%C3%93C_TI%C3%8AN_MAIQUINN_MU%E1%BB%98II_YEOLAN_%C4%90%C3%80O_T%E1%BB%AC_A1J_x_DTAP_LSX_2025_ryzvda.mp3",          # [6]  audio_url
            "https://res.cloudinary.com/dogyjotxv/image/upload/v1772036596/thienthanh1_pizmpn.png",          # [7]  avatar_url
            "Mashup Rock Thiệp Hổng ∙ Tóc Tiên x MaiQuinn x Yeolan x Đào Tử A1J",          # [8]  song
            "Tụi mình muốn gửi lời cảm ơn chân thành đến Thanh vì nguồn năng lượng tích cực mà cậu mang lại cho cả nhóm. Bà là một mảnh ghép rất cá tính trong lớp và đó cũng là thứ giúp lớp chúng ta đoàn kết hơn . Mong Thiên Thanh lúc nào cũng giữ được tinh thần lạc quan và chinh phục được mọi mục tiêu mà cậu đang ấp ủ!",          # [9]  letter_content
            "",          # [10] letter_image_url
            "https://res.cloudinary.com/dogyjotxv/image/upload/v1772986569/Buoc_Toc_-_Up_1_muf6le.gif",          # [11] gif_up
            "https://res.cloudinary.com/dogyjotxv/image/upload/v1772986569/Buoc_Toc_-_Down_1_bamcqb.gif",          # [12] gif_down
            "https://res.cloudinary.com/dogyjotxv/image/upload/v1772986489/Buoc_Toc_alt_-_Left_1_mscldt.gif",          # [13] gif_left
            "https://res.cloudinary.com/dogyjotxv/image/upload/v1772986489/Buoc_Toc_alt_-_Right_a3bc2i.gif",          # [14] gif_right
            "@10052009tranmeo@",          # [15] gift_password
            "https://res.cloudinary.com/dogyjotxv/image/upload/v1772539394/qua1_ko17hc.png",          # [16] gift_image
            "",          # [17] profile_password
        ),
        (
            "lungocbich",          # [0]  short_name
            "Lữ Ngọc Bích",          # [1]  full_name
            "Biệt danh: Su",          # [2]  nickname
            "Điều chúng tớ thích về cậu:vì cậu là một lớp phó học tập gương mẫu luôn có tinh thần và trách nhiệm giúp đỡ mọi người trong lớp",          # [4]  things_we_love
            "https://res.cloudinary.com/dogyjotxv/image/upload/v1771954086/ngocbich2_jyiiqf.png",          # [5]  layer_url
            "https://res.cloudinary.com/dogyjotxv/video/upload/v1772209832/Simple_Love_-_Obito_x_Seachains_x_Davis_x_Lena_Official_MV_dkr0vw.mp3",          # [6]  audio_url
            "https://res.cloudinary.com/dogyjotxv/image/upload/v1772036596/ngocbich1_picblc.png",          # [7]  avatar_url
            "Simple Love ∙ Obito x Seachains",          # [8]  song
            "Tụi mình muốn gửi lời cảm ơn chân thành đến Bích vì sự giúp đỡ nhiệt tình trong suốt thời gian qua  bọn mình rất trân trọng những lúc báo bài rất đúng giờ, một người lớp phó học tập gương mẫu. Ngoài ra cũng là người chịu rất nhìu áp lực từ thầy cô.  Chúc Bích luôn rạng rỡ, học tốt và mọi dự định cá nhân đều thành công rực rỡ nha!",          # [9]  letter_content
            "",          # [10] letter_image_url
            "https://res.cloudinary.com/dogyjotxv/image/upload/v1772986569/Buoc_Toc_-_Up_1_muf6le.gif",          # [11] gif_up
            "https://res.cloudinary.com/dogyjotxv/image/upload/v1772986569/Buoc_Toc_-_Down_1_bamcqb.gif",          # [12] gif_down
            "https://res.cloudinary.com/dogyjotxv/image/upload/v1772987842/Buoc_Toc_-_Left_1_yifu8x.gif",          # [13] gif_left
            "https://res.cloudinary.com/dogyjotxv/image/upload/v1772987842/Buoc_Toc_-_Right_brceuy.gif",          # [14] gif_right
            "@16102009su@",          # [15] gift_password
            "https://res.cloudinary.com/dogyjotxv/image/upload/v1772539394/qua1_ko17hc.png",          # [16] gift_image
            "",          # [17] profile_password
        ),
        (
            "tranhatuyetnhu",          # [0]  short_name
            "Trần Hà Tuyết Như",          # [1]  full_name
            "Biệt danh: Bé Như",          # [2]  nickname
            "Điều chúng tớ thích về cậu:luôn mang lại năng lượng tích cực cho mọi người xung quanh",          # [4]  things_we_love
            "https://res.cloudinary.com/dogyjotxv/image/upload/v1771954085/tuyetnhu2_ptkhyr.png",          # [5]  layer_url
            "https://res.cloudinary.com/dogyjotxv/video/upload/v1772209373/RIO_-_v%E1%BA%A1n_v%E1%BA%ADt_nh%C6%B0_mu%E1%BB%91n_ta_b%C3%AAn_nhau_Official_MV_csfksl.mp3",          # [6]  audio_url
            "https://res.cloudinary.com/dogyjotxv/image/upload/v1772030901/tuyetnhu1_dlwi9z.png",          # [7]  avatar_url
            "Vạn Vật Như Muốn Ta Bên Nhau ∙ RIO",          # [8]  song
            "Tụi mình muốn gửi lời cảm ơn chân thành đến Như vì đã luôn góp phần làm cho lớp mình trở nên vui vẻ và nhiều tiếng cười hơn. Khi có bà  lúc nào cũng cảm thấy có thêm động lực học tập (và đôi khi cũng có thêm động lực… nói chuyện một chút xíu). Chúc Tuyết Như luôn giữ được sự lạc quan, học thật tốt và đạt được nhiều thành tích đáng tự hào trong thời gian tới!",          # [9]  letter_content
            "",          # [10] letter_image_url
            "https://res.cloudinary.com/dogyjotxv/image/upload/v1772989988/Xoa_Toc_-_Up_lmg6qu.gif",          # [11] gif_up
            "https://res.cloudinary.com/dogyjotxv/image/upload/v1772989988/Xoa_Toc_-_Down_vsmfgx.gif",          # [12] gif_down
            "https://res.cloudinary.com/dogyjotxv/image/upload/v1772725128/Xoa_Toc_-_Left_wezif7.gif",          # [13] gif_left
            "https://res.cloudinary.com/dogyjotxv/image/upload/v1772725128/Xoa_Toc_-_Right_pljrjz.gif",          # [14] gif_right
            "@1102009benhu@",          # [15] gift_password
            "https://res.cloudinary.com/dogyjotxv/image/upload/v1772539394/qua1_ko17hc.png",          # [16] gift_image
            "",          # [17] profile_password
        ),
        (
            "dothithanhan",          # [0]  short_name
            "Đỗ Thị Thanh An",          # [1]  full_name
            "Biệt danh: Alice, Ariel",          # [2]  nickname
            "Điều chúng con thích về cô:Cô luôn cho chúng em những lời khuyên chân thành,những lỗi sai của chúng em dù khiến cô không vui cô vẫn rộng lòng tha thứ",          # [4]  things_we_love
            "https://res.cloudinary.com/dogyjotxv/image/upload/v1771954329/cothanhan2_zcahg1.png",          # [5]  layer_url
            "https://res.cloudinary.com/dogyjotxv/video/upload/v1772213432/Maroon_5-_Sugar_de74hs.mp3",          # [6]  audio_url
            "https://res.cloudinary.com/dogyjotxv/image/upload/v1772036649/cothanhan1_qohuyz.png",          # [7]  avatar_url
            "Sugar ∙ Maroon5",          # [8]  song
            "Nhân ngày Quốc tế Phụ nữ 8/3, em xin gửi đến cô Thanh An những lời chúc tốt đẹp và chân thành nhất. Chúc cô luôn mạnh khỏe, vui vẻ và hạnh phúc trong cuộc sống. Cảm ơn cô vì đã luôn tận tâm giảng dạy, truyền đạt kiến thức và quan tâm đến chúng em.Chúc cô luôn giữ được sự nhiệt huyết với nghề và có thật nhiều niềm vui trong công việc cũng như trong cuộc sống.",          # [9]  letter_content
            "",          # [10] letter_image_url
            "https://res.cloudinary.com/dogyjotxv/image/upload/v1772986295/TANup_pturcn.gif",          # [11] gif_up
            "https://res.cloudinary.com/dogyjotxv/image/upload/v1772986295/Tan_down_fpecom.gif",          # [12] gif_down
            "https://res.cloudinary.com/dogyjotxv/image/upload/v1772986295/Tan_Left_fcfxux.gif",          # [13] gif_left
            "https://res.cloudinary.com/dogyjotxv/image/upload/v1772986295/Tan_Right_1_m7leq8.gif",          # [14] gif_right
            "5/4cothanhan18tuoialice",          # [15] gift_password
            "https://res.cloudinary.com/dogyjotxv/image/upload/v1772539394/qua1_ko17hc.png",          # [16] gift_image
            "",          # [17] profile_password
        ),
        (
            "tranthihanh",                   # [0]  short_name
            "Trần Thị Hạnh",                 # [1]  full_name
            "Biệt danh: Mẹ Hạnh",         # [2]  nickname
            "Điều chúng con thích về mẹ:mẹ luôn tha thứ cho con dù con đã nhiều lần mắc phải những lỗi lầm quá đáng, luôn ân cần chỉ bảo cho con nên người",                              # [4]  things_we_love
            "",                              # [5]  layer_url
            "https://res.cloudinary.com/dogyjotxv/video/upload/v1772993030/C%E1%BA%A3m_%C6%A1n_ng%C6%B0%E1%BB%9Di_%C4%91%C3%A3_th%E1%BB%A9c_gi%E1%BA%A5c_c%C3%B9ng_t%C3%B4i-_Ph%C3%B9ng_Kh%C3%A1nh_Linh_f4nl5e.mp3",  # [6]  audio_url
            "",                              # [7]  avatar_url
            "Cảm ơn người thức giấc cùng tôi ∙ Phòng Khánh Linh",                              # [8]  song
            "Con muốn nhân ngày 8/3 này có thể gửi cho mẹ những lời chúc tốt đẹp nhất,cảm ơn mẹ vì đã là người phụ nữ của gia đình lúc nào cũng chăm lo cho 2 cha con con, không bao giờ la mắng con dù cho ba hay con có làm cho mẹ giận,có những ngày hành mẹ làm lên làm xuống nhưng mẹ lúc nào cũng dịu dàng và hết mình vì chúng con,con xin mượn ngày 8/3 để cảm ơn cho những gì mẹ đã làm cho con.",                              # [9]  letter_content
            "",                              # [10] letter_image_url
            "https://res.cloudinary.com/dogyjotxv/image/upload/v1772989988/Xoa_Toc_-_Up_lmg6qu.gif",                              # [11] gif_up
            "https://res.cloudinary.com/dogyjotxv/image/upload/v1772989988/Xoa_Toc_-_Down_vsmfgx.gif",                              # [12] gif_down
            "https://res.cloudinary.com/dogyjotxv/image/upload/v1772725128/Xoa_Toc_-_Left_wezif7.gif",                              # [13] gif_left
            "https://res.cloudinary.com/dogyjotxv/image/upload/v1772725128/Xoa_Toc_-_Right_pljrjz.gif   ",                              # [14] gif_right
            "",                              # [15] gift_password — RONG: khong popup o /letter
            "https://res.cloudinary.com/dogyjotxv/image/upload/v1772539394/qua1_ko17hc.png",  # [16] gift_image
            "@12111982mehanh@",                          # [17] profile_password — CO: popup khi vao /profile
        ),
        (
            "dokhanhan",                     # [0]  short_name
            "Đỗ Khánh An",                   # [1]  full_name
            "Biệt danh: Bống",                              # [2]  nickname
            "Điều chúng anh thích về em:em luôn nghe theo những yêu cầu của anh dù nó có quá đáng và luôn vui vẻ dù cho anh có chọc em giận",                              # [4]  things_we_love
            "",                              # [5]  layer_url
            "https://res.cloudinary.com/dogyjotxv/video/upload/v1772211507/Low_G_In_Love_ft._JustaTee_L2K_The_Album_szcc8e.mp3",  # [6]  audio_url
            "",                              # [7]  avatar_url
            "In Love ∙ Low G x JustaTee",                              # [8]  song
            "Nhân ngày 8/3 chúc Bống có một ngày quốc tế phụ nữ vui vẻ, lúc nào cũng có nhiều niềm vui trong cuộc sống và đặc biệt sớm có bồ nhe, cảm ơn bống vì đã chịu đựng những lần nhờ vả vô lý hay những yêu cầu khó hiểu của anh trong suốt những năm qua, chúc em có 1 ngày 8/3 thật vui vẻ nha",                              # [9]  letter_content
            "",                              # [10] letter_image_url
            "https://res.cloudinary.com/dogyjotxv/image/upload/v1772986569/Buoc_Toc_-_Up_1_muf6le.gif",                              # [11] gif_up
            "https://res.cloudinary.com/dogyjotxv/image/upload/v1772986569/Buoc_Toc_-_Down_1_bamcqb.gif",                              # [12] gif_down
            "https://res.cloudinary.com/dogyjotxv/image/upload/v1772986489/Buoc_Toc_alt_-_Left_1_mscldt.gif",                              # [13] gif_left
            "https://res.cloudinary.com/dogyjotxv/image/upload/v1772986489/Buoc_Toc_alt_-_Right_a3bc2i.gif",                              # [14] gif_right
            "",                              # [15] gift_password — RONG: khong popup o /letter
            "https://res.cloudinary.com/dogyjotxv/image/upload/v1772539394/qua1_ko17hc.png",  # [16] gift_image
            "@07122013bong@",                          # [17] profile_password — CO: popup khi vao /profile
        ),
        (
            "lieunhuhien",                   # [0]  short_name
            "Liêu Như Hiền",                 # [1]  full_name
            "Biệt danh: hi píc",                              # [2]  nickname
            "Điều mà anh thích về em:dễ thương dễ thương và dthw",                              # [4]  things_we_love
            "https://res.cloudinary.com/dogyjotxv/image/upload/v1772201008/nhuhien2_ue8uc0.png",  # [5]  layer_url
            "https://res.cloudinary.com/dogyjotxv/video/upload/v1772211507/Low_G_In_Love_ft._JustaTee_L2K_The_Album_szcc8e.mp3",  # [6]  audio_url
            "https://res.cloudinary.com/dogyjotxv/image/upload/v1772201013/nhuhien1_eyfkzu.png",  # [7]  avatar_url
            "In Love ∙ Low G x JustaTee",    # [8]  song
            "Anh biết em đã trải qua nhiều khó khăn và từng rất tự ti, điều đó làm anh nhớ đến chính mình ngày trước – từng nghĩ thành công chỉ là may mắn. Nhưng theo anh, ai rồi cũng có lúc rực rỡ, quan trọng là có đủ kiên nhẫn để chờ đến lúc đó. Anh mong em luôn tự tin theo đuổi ước mơ của mình. Món quà 8/3 này tuy trễ một ngày, nhưng anh mong nó sẽ khiến em vui hơn. Hãy luôn tự tin, xinh đẹp và vui vẻ nhé. Yêu em! ",                              # [9]  letter_content
            "",                              # [10] letter_image_url
            "https://res.cloudinary.com/dogyjotxv/image/upload/v1772989988/Xoa_Toc_-_Up_lmg6qu.gif ",                              # [11] gif_up
            "https://res.cloudinary.com/dogyjotxv/image/upload/v1772989988/Xoa_Toc_-_Down_vsmfgx.gif",                              # [12] gif_down
            "https://res.cloudinary.com/dogyjotxv/image/upload/v1772725128/Xoa_Toc_-_Left_wezif7.gif",                              # [13] gif_left
            "https://res.cloudinary.com/dogyjotxv/image/upload/v1772725128/Xoa_Toc_-_Right_pljrjz.gif",                              # [14] gif_right
            "",                              # [15] gift_password — RONG: khong popup o /letter
            "https://res.cloudinary.com/dogyjotxv/image/upload/v1772539394/qua1_ko17hc.png",  # [16] gift_image
            "@16062009@",                          # [17] profile_password — CO: popup khi vao /profile
        ),
        (
            "tranyenphuong",          # [0]  short_name
            "Trần Yến Phương",          # [1]  full_name
            "Biệt danh: Ms Phương",          # [2]  nickname
            "Điều chúng em thích về cô:Sự nhiệt tình, năng nổ và hòa đồng của cô giống như một người chị đối với chúng em,chúng em rất quý điều đó ạ",          # [4]  things_we_love
            "https://res.cloudinary.com/dogyjotxv/image/upload/v1772199597/coyenphuong2_tykgpk.png",          # [5]  layer_url
            "https://res.cloudinary.com/dogyjotxv/video/upload/v1772213306/M%E1%BA%B7t_M%E1%BB%99c-VAnh_hqdv3t.mp3",          # [6]  audio_url
            "https://res.cloudinary.com/dogyjotxv/image/upload/v1772199593/coyenphuong1_jkkpvx.png",          # [7]  avatar_url
            "Mặt Mộc ∙ VAnh x Phạm Nguyên Ngọc",          # [8]  song
            "Tụi em xin cảm ơn cô vì đã luôn tận tâm giảng dạy, truyền đạt kiến thức và quan tâm đến học sinh, kiên nhẫn với lớp dù đôi lúc tụi em hơi… ồn ào có tổ chức. Chúc cô luôn giữ được sự nhiệt huyết với nghề và có thật nhiều niềm vui trong công việc cũng như trong cuộc sống.",# [9]  letter_content
            "",          # [10] letter_image_url
            "https://res.cloudinary.com/dogyjotxv/image/upload/v1772989988/Xoa_Toc_-_Up_lmg6qu.gif",          # [11] gif_up
            "https://res.cloudinary.com/dogyjotxv/image/upload/v1772989988/Xoa_Toc_-_Down_vsmfgx.gif",          # [12] gif_down
            "https://res.cloudinary.com/dogyjotxv/image/upload/v1772725128/Xoa_Toc_-_Left_wezif7.gif",          # [13] gif_left
            "https://res.cloudinary.com/dogyjotxv/image/upload/v1772725128/Xoa_Toc_-_Right_pljrjz.gif",          # [14] gif_right
            "@2807missphuongmaidinhmaidnh8386@",          # [15] gift_password
            "https://res.cloudinary.com/dogyjotxv/image/upload/v1772539394/qua1_ko17hc.png",          # [16] gift_image
            "",          # [17] profile_password
        ),
    ]

    cursor.executemany(
        """INSERT INTO profiles
               (short_name, full_name, nickname, things_we_love,
                layer_url, audio_url, avatar_url, song, letter_content, letter_image_url,
                gif_up, gif_down, gif_left, gif_right,
                gift_password, gift_image, profile_password)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
           ON CONFLICT(short_name) DO UPDATE SET
               full_name        = excluded.full_name,
               nickname         = excluded.nickname,
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
               gift_image       = excluded.gift_image,
               profile_password = excluded.profile_password""",
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
        """SELECT full_name, nickname, things_we_love,
                  layer_url, audio_url, avatar_url, song,
                  gif_up, gif_down, gif_left, gif_right,
                  profile_password
           FROM profiles WHERE short_name = ?""",
        (norm,)
    )
    row = cursor.fetchone()
    conn.close()

    if row:
        profile_data = {
            'name':             row[0],
            'nickname':         row[1],
            'things_we_love':   row[2],
            'layer':            row[3],
            'audio':            row[4],
            'avatar':           row[5],
            'song':             row[6],
            'gif_up':           row[7],
            'gif_down':         row[8],
            'gif_left':         row[9],
            'gif_right':        row[10],
            'profile_password': row[11],
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
            'gift_password':    row[3],
            'gift_image':       row[4],
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
