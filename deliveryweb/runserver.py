"""
This script runs the deliveryweb application using a development server.
"""

from os import environ
from deliveryweb import app

if __name__ == '__main__':
    # Lấy HOST từ biến môi trường hoặc sử dụng localhost làm mặc định
    HOST = environ.get('SERVER_HOST', '127.0.0.1')  
    
    # Lấy PORT từ biến môi trường hoặc sử dụng cổng 5000 làm mặc định
    try:
        PORT = int(environ.get('SERVER_PORT', '5000'))  
    except ValueError:
        PORT = 5000

    # Chạy ứng dụng Flask trên cổng và host đã chỉ định
    app.run(host=HOST, port=PORT, debug=True)
