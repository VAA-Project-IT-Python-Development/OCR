import os
from flask import Flask
from flask_session import Session
from flask_dropzone import Dropzone

app = Flask(__name__)
app.config['SECRET_KEY'] = 'aea22e6ff5c4be822cc2ed127089ebc76b619320c0121596b0b714d10464'

# Sessions
SESSION_TYPE = 'filesystem'
app.config.from_object(__name__)
Session(app)

dir_path = os.path.dirname(os.path.realpath(__file__))

# Cập nhật đường dẫn lưu file upload
app.config.update(
    UPLOADED_PATH=os.path.join(dir_path, 'static/uploaded_files/'),  # Đường dẫn lưu ảnh upload
    UPLOAD_FOLDER=os.path.join(dir_path, 'static/uploads_voice/'),  # Đường dẫn lưu file voice upload
    # Flask-Dropzone config:
    DROPZONE_ALLOWED_FILE_TYPE='image',
    DROPZONE_MAX_FILE_SIZE=3,
    DROPZONE_MAX_FILES=1,
    AUDIO_FILE_UPLOAD=os.path.join(dir_path, 'static/audio_files/')  # Đường dẫn lưu file âm thanh
)

app.config['DROPZONE_REDIRECT_VIEW'] = 'decoded'

dropzone = Dropzone(app)

from application import routes
from application import app
