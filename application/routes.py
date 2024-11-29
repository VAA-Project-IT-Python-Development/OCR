from application import app
from flask import Response, flash, jsonify, render_template, url_for, request, redirect, session, redirect, send_file
import secrets
import os
from application.forms import QRCodeData
from application import utils
#voice
import speech_recognition as sr
#pymongo
from application.mongo_config import mongo  # Import MongoDB đã được config
# OCR
import cv2
import pytesseract
from PIL import Image
import numpy as np
# pip install gTTS
from gtts import gTTS
import mediapipe as mp
import tempfile
from application.hand_detection import detect_sign_language_sequence
#omr
from imutils.perspective import four_point_transform
from imutils import contours
import argparse
import imutils
from werkzeug.utils import secure_filename




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
    # print("Session data:", session)  # In session để kiểm tra

    sentence = session.get("sentence")

    if sentence is None or sentence == "":
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
        # print(translated_text)

        # Tạo file âm thanh từ kết quả dịch
        tts = gTTS(translated_text, lang=translate_to)
        file_location = os.path.join(app.config['AUDIO_FILE_UPLOAD'], generated_audio_filename)
        tts.save(file_location)

      # Chuẩn bị dữ liệu để lưu vào MongoDB
        translation_data = {
            "original_text": sentence,  
            "translated_text": translated_text, 
            "source_language": lang,  
            "translate_to": translate_to,  
            "audio_file_path": file_location  
        }

        mongo.db.translate.insert_one(translation_data)

        # Xóa dữ liệu trong session sau khi submit form
        session["sentence"] = ""

        return render_template("decoded.html", 
                               form=form,
                               translated_text=translated_text,  # Truyền kết quả dịch
                               audio=True,
                               lang=utils.languages.get(lang),
                               file=generated_audio_filename)

    else:
        form.data_field.data = sentence  # Đưa dữ liệu nhận diện vào trường input
        # Không xóa session ở đây, chỉ làm khi người dùng submit form

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

                # Lưu file âm thanh
                voice_folder = os.path.join(app.config['UPLOAD_FOLDER'])
                os.makedirs(voice_folder, exist_ok=True)

                # Tạo tên file âm thanh
                audio_filename = secrets.token_hex(10) + ".wav"
                audio_path = os.path.join(voice_folder, audio_filename)

                # Lưu âm thanh
                with open(audio_path, "wb") as audio_file:
                    audio_file.write(audio_data.get_wav_data())

                print(f"Audio saved at {audio_path}")

                # Nhận diện âm thanh
                text = recognizer.recognize_google(audio_data, language="vi-VN")
                print("Recognition successful:", text)

                # Lưu kết quả vào session
                session["sentence"] = text

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
    translations = mongo.db.translate.find()
    return render_template("translate.html", title="Translate History", translations=translations)

@app.route("/sign_language", methods=["GET", "POST"])
def sign_language():
    return render_template("sign_language.html", title="Sign Language")


@app.route('/video_feed')
def video_feed():
    return Response(detect_sign_language_sequence(), mimetype='multipart/x-mixed-replace; boundary=frame')













#omr
# OMR Upload
# Hàm xử lý hình ảnh OMR
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

def process_omr(answer_key, test_image_path):
    # Tải ảnh bài kiểm tra và xử lý
    test_image = cv2.imread(test_image_path)
    gray = cv2.cvtColor(test_image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edged = cv2.Canny(blurred, 75, 200)

    cnts = cv2.findContours(edged.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cnts = imutils.grab_contours(cnts)
    docCnt = None

    # Tìm đường viền lớn nhất, xác định hình vuông hoặc hình tứ giác để làm OMR
    if len(cnts) > 0:
        cnts = sorted(cnts, key=cv2.contourArea, reverse=True)
        for c in cnts:
            peri = cv2.arcLength(c, True)
            approx = cv2.approxPolyDP(c, 0.02 * peri, True)
            if len(approx) == 4:
                docCnt = approx
                break

    if docCnt is None:
        return None, None, "Không tìm thấy đường viền tài liệu."

    paper = four_point_transform(test_image, docCnt.reshape(4, 2))
    warped = four_point_transform(gray, docCnt.reshape(4, 2))
    thresh = cv2.threshold(warped, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1]

    cnts = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cnts = imutils.grab_contours(cnts)
    questionCnts = []

    for c in cnts:
        (x, y, w, h) = cv2.boundingRect(c)
        ar = w / float(h)
        if w >= 20 and h >= 20 and ar >= 0.9 and ar <= 1.1:
            questionCnts.append(c)

    questionCnts = contours.sort_contours(questionCnts, method="top-to-bottom")[0]

    # Đảm bảo số câu trả lời khớp với số câu hỏi
    num_questions = len(questionCnts) // 5  # Mỗi câu hỏi có 5 tùy chọn trả lời
    if len(answer_key) != num_questions:
        return None, None, f"Số câu trả lời ({len(answer_key)}) không khớp với số câu hỏi phát hiện được ({num_questions})."

    correct = 0
    results = []

    for (q, i) in enumerate(np.arange(0, len(questionCnts), 5)):
        cnts = contours.sort_contours(questionCnts[i:i + 5])[0]
        bubbled = None

        for (j, c) in enumerate(cnts):
            mask = np.zeros(thresh.shape, dtype="uint8")
            cv2.drawContours(mask, [c], -1, 255, -1)
            mask = cv2.bitwise_and(thresh, thresh, mask=mask)
            total = cv2.countNonZero(mask)

            if bubbled is None or total > bubbled[0]:
                bubbled = (total, j)

        k = answer_key[q]
        results.append(k == bubbled[1])
        if k == bubbled[1]:
            color = (0, 255, 0)  # Màu xanh cho câu trả lời đúng
            correct += 1  # Chỉ tăng một lần ở đây
        else:
            color = (0, 0, 255)  # Màu đỏ cho câu trả lời sai

        cv2.drawContours(paper, [cnts[k]], -1, color, 3)

        # In ra để kiểm tra
        print(f"Question {q}: Bubbling {bubbled[1]}, Key {k}")

    score = (correct / len(answer_key)) * 100

     # Lưu ảnh đã chấm điểm
    scored_image_path = os.path.join(app.config['UPLOAD_FOLDER'], 'scored_test.png')

    cv2.imwrite(scored_image_path, paper)

    # In ra kết quả cuối cùng
    print("Final Results:", results)
    print("Final Score:", score)

    return results, score, scored_image_path

@app.route('/omr_upload', methods=['GET', 'POST'])
def omr_upload():
    score = None
    results = []

    if request.method == 'POST':
        if 'file' not in request.files:
            flash('Không có tệp nào được chọn.')
            return redirect(request.url)
        
        file = request.files['file']
        if file.filename == '':
            flash('Không có tệp nào được chọn.')
            return redirect(request.url)

        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        # Lấy đáp án từ form đầu vào
        answers = request.form.getlist('answers')
        answer_key = [ord(a.upper()) - ord('A') for a in answers if a.upper() in ['A', 'B', 'C', 'D', 'E']]

        results, score, scored_image_path = process_omr(answer_key, file_path)

        if results is None:
            flash("Lỗi: Không tìm thấy đường viền tài liệu hoặc số câu trả lời không khớp.")
            return redirect(request.url)

        # Thiết lập đường dẫn cho hình ảnh gốc và ảnh đã chấm điểm
        goc_image = url_for('static', filename='uploads/' + filename)
        cham_diem_image = url_for('static', filename='uploads/scored_test.png')

        # In ra để kiểm tra
        print("Goc Image:", goc_image)
        print("Cham Diem Image:", cham_diem_image)

        # Trả kết quả ra trang HTML
        return render_template('omr_result.html', score=score, results=results, goc_image=goc_image, cham_diem_image=cham_diem_image)

    return render_template('omr_upload.html', score=score, results=results)