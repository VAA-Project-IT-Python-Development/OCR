from application import app
from application.mongo_config import init_mongo  # Import hàm khởi tạo MongoDB

# Khởi tạo MongoDB
init_mongo(app)

if __name__ == "__main__":
    app.run(debug=True)


