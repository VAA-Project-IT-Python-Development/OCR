from application import app
from flask import render_template, url_for, request, redirect, session
import secrets
import os
from application.forms import QRCodeData
from application import utils

# OCR
import cv2
import pytesseract
from PIL import Image
import numpy as np
# pip install gTTS
from gtts import gTTS


#trang chủ
@app.route("/")
def index():
    return render_template("index.html", title="Home Page")

@app.route("/upload", methods=["GET", "POST"])
def upload():
    if request.method == 'POST':
        # Set a session value
        sentence = ""

        # Lấy file từ form
        f = request.files.get('file')

        # Kiểm tra phần mở rộng của file
        if not f or '.' not in f.filename:
            return "File không hợp lệ", 400

        filename, extension = f.filename.rsplit('.', 1)
        if extension.lower() not in ['jpg', 'jpeg', 'png']:
            return "Chỉ hỗ trợ các file hình ảnh (.jpg, .jpeg, .png)", 400

        generated_filename = secrets.token_hex(10) + f".{extension}"
        file_location = os.path.join(app.config['UPLOADED_PATH'], generated_filename)

        # Save file vào thư mục
        f.save(file_location)

        # OCR xử lý hình ảnh
        pytesseract.pytesseract.tesseract_cmd = r'/opt/homebrew/bin/tesseract'  # Đảm bảo đúng đường dẫn tới Tesseract

        # Đọc hình ảnh bằng OpenCV
        img = cv2.imread(file_location)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)  # Chuyển đổi màu sắc ảnh từ BGR -> RGB

        # Sử dụng Tesseract với ngôn ngữ tiếng Việt
        config = '--oem 3 --psm 6'  # cấu hình cho OCR, thêm PSM tùy chỉnh
        boxes = pytesseract.image_to_data(img, lang='vie', config=config, output_type=pytesseract.Output.DICT)

        # Xử lý dữ liệu nhận diện và ghép các từ thành câu
        for i in range(len(boxes['text'])):
            if int(boxes['conf'][i]) > 0:  # Lọc ra những từ có độ chính xác cao (conf > 0)
                sentence += boxes['text'][i] + " "

        # Lưu câu nhận diện vào session
        session["sentence"] = sentence.strip()

        # Xóa file sau khi hoàn thành
        os.remove(file_location)

        return redirect("/decoded/")

    # Nếu là GET request, render trang upload
    return render_template("upload.html", title="Upload File")

    
@app.route("/decoded", methods=["POST", "GET"])
def decoded():
    sentence = session.get("sentence")
    lang, _ = utils.detect_language(sentence)
    form = QRCodeData() 
    translated_text = None  # Biến chứa kết quả dịch
    
    if request.method == "POST" and form.validate_on_submit():
        generated_audio_filename = secrets.token_hex(10) + ".mp4"
        text_data = form.data_field.data
        translate_to = form.language.data

        # Thực hiện dịch văn bản
        translated_text = utils.translate_text(text_data, translate_to)
        print(translated_text)

        # Tạo file âm thanh từ kết quả dịch
        tts = gTTS(translated_text, lang=translate_to)
        file_location = os.path.join(app.config['AUDIO_FILE_UPLOAD'], generated_audio_filename)
        tts.save(file_location)

        return render_template("decoded.html", 
                               form=form,
                               translated_text=translated_text,  # Truyền kết quả dịch
                               audio=True,
                               lang=utils.languages.get(lang),
                               file=generated_audio_filename)

    else:
        form.data_field.data = sentence
        session["sentence"] = ""

        return render_template("decoded.html", 
                               form=form, 
                               audio=False,
                               lang=utils.languages.get(lang))

@app.route("/voice_upload", methods=["GET", "POST"])
def voice_upload():
    return render_template("voice_upload.html", title="Voice Upload")

@app.route("/translate", methods=["GET", "POST"])
def translate():
    return render_template("translate.html", title="Translate")