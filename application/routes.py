from application import app
from flask import render_template, url_for, request, redirect, session
import secrets
import os
from application.forms import QRCodeData
from application import utils
#voice
import speech_recognition as sr

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
#chạy hàm upload image
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

  # Hàm xử lý sự kiện sau khi nhận diện giọng nói thành công
@app.route("/decoded", methods=["POST", "GET"])
def decoded():
    print("Session data:", session)  # In ra session để kiểm tra nội dung
    sentence = session.get("sentence")

    if sentence is None:
        return "No sentence found in session.", 400  # Trả về lỗi nếu không có dữ liệu

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
        session["sentence"] = ""  # Xóa dữ liệu trong session sau khi sử dụng

        return render_template("decoded.html", 
                               form=form, 
                               audio=False,
                               lang=utils.languages.get(lang))


# Hàm xử lý upload voice
@app.route("/voice_upload", methods=["GET", "POST"])
def voice_upload():
    if request.method == 'POST':
        recognizer = sr.Recognizer()
        with sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source, duration=1)
            print("Listening...")

            try:
                # Ghi nhận âm thanh từ microphone
                audio_data = recognizer.listen(source, timeout=10)
                print("Processing audio data...")

                # Lưu audio file vào thư mục uploads/voices/
                voice_folder = os.path.join(app.config['UPLOAD_FOLDER'])
                os.makedirs(voice_folder, exist_ok=True)  # Tạo thư mục nếu chưa có

                # Tạo tên file duy nhất cho âm thanh
                audio_filename = secrets.token_hex(10) + ".wav"
                audio_path = os.path.join(voice_folder, audio_filename)

                # Lưu âm thanh vào file
                with open(audio_path, "wb") as audio_file:
                    audio_file.write(audio_data.get_wav_data())  # Lưu dữ liệu âm thanh dưới dạng .wav

                print(f"Audio saved at {audio_path}")

                # Sử dụng Google Speech Recognition để nhận dạng âm thanh
                text = recognizer.recognize_google(audio_data, language="vi-VN")
                print("Recognition successful:", text)

                # Lưu kết quả nhận dạng vào session
                session["sentence"] = text
                # Redirect đến trang decoded
                print(f"Text saved in session: {session['sentence']}")  # In ra để kiểm tra

                return redirect("/decoded")

            except sr.UnknownValueError:
                print("Voice recognition could not understand the audio.")
                return "Voice recognition could not understand the audio.", 400
            except sr.RequestError as e:
                print(f"Could not request results from Google Speech Recognition service: {e}")
                return f"Could not request results from Google Speech Recognition service: {e}", 500
            except Exception as e:
                print(f"An unexpected error occurred: {e}")
                return f"An unexpected error occurred: {e}", 500

    return render_template("voice_upload.html", title="Voice Upload")




@app.route("/translate", methods=["GET", "POST"])
def translate():
    return render_template("translate.html", title="Translate")