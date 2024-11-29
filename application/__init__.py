import os
import cv2
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
    UPLOADED_PATH=os.path.join(dir_path, 'static/uploaded_files/'),  # Path for uploaded images
    UPLOAD_FOLDER=os.path.join(dir_path, 'static/uploads_voice/'),  # Path for uploaded voice files
    DROPZONE_ALLOWED_FILE_TYPE='image',  # Cho phép định dạng hình ảnh (jpg, png, v.v.)
    DROPZONE_MAX_FILE_SIZE=20,  # Kích thước tối đa của file ảnh
    DROPZONE_MAX_FILES=1,
    AUDIO_FILE_UPLOAD=os.path.join(dir_path, 'static/audio_files/')  # Path for uploaded audio files
)


# Paths for demo video
app.config['DEMO_VIDEO_PATH'] = os.path.join(dir_path, 'static/demo_video.mp4')
app.config['DROPZONE_REDIRECT_VIEW'] = 'decoded'

# OMR Uploads Path
app.config['UPLOAD_FOLDER'] = os.path.join(dir_path, 'static/uploads')
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize Dropzone
dropzone = Dropzone(app)

# Import routes at the end to avoid circular imports
from application import routes
from application import app
