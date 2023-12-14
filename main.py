import json
import logging
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse
import threading
import mimetypes
import pathlib
import socket
from datetime import datetime


BASE_DIR = pathlib.Path()
SOCKET_HOST ='127.0.0.1'
SOCKET_PORT = 5000
BUFFER_SIZE = 1024
HTTP_PORT = 3000
HTTP_HOST ='0.0.0.0'
class HttpHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        route = urllib.parse.urlparse(self.path)
        match route.path:
            case '/':
                self.send_html('front-init/index.html')
            case '/message.html':
                self.send_html('front-init/message.html')
            case _:
                file = BASE_DIR.joinpath(route.path[1:])
                if pathlib.Path().joinpath(route.path[1:]).exists():
                    self.send_static()
                else:
                    self.send_html('front-init/error.html', 404)

    def do_POST(self):
        data = self.rfile.read(int(self.headers['Content-Length']))
        print(data)
        data_parse = urllib.parse.unquote_plus(data.decode())
        print(data_parse)
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        client_socket.sendto(data, (SOCKET_HOST, SOCKET_PORT))
        client_socket.close()
        #data_dict = {key: value for key, value in [el.split('=') for el in data_parse.split('&')]}
        #print(data_dict)
        self.send_response(302)
        self.send_header('Location', '/')
        self.end_headers()
    def send_html(self, filename, status=200):
        self.send_response(status)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        with open(filename, 'rb') as fd:
            self.wfile.write(fd.read())

    def send_static(self):
        self.send_response(200)
        mt = mimetypes.guess_type(self.path)
        if mt:
            self.send_header("Content-type", mt[0])
        else:
            self.send_header("Content-type", 'text/plain')
        self.end_headers()
        with open(f'.{self.path}', 'rb') as file:
            self.wfile.write(file.read())

def save_data_from_form(data):
    data_parse = urllib.parse.unquote_plus(data.decode())
    print(data_parse)
    try:
        data_dict = {key: value for key, value in [el.split('=') for el in data_parse.split('&')]}
        print(data_dict)
        with open('front-init/storage/data.json', 'a', encoding='utf-8') as file: #data_dict
            print(datetime.now())
            new_dict = {}
            new_dict[str(datetime.now())] = data_dict
            json.dump(new_dict, file, ensure_ascii=False, indent=4)
    except ValueError as err:
        logging.error(err)
    except OSError as err:
        logging.error(err)
def run_socket_server(host, port):
    socket_server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    socket_server.bind((host, port))
    logging.info('Starting socket server')
    try:
        while True:
            msg, addres = socket_server.recvfrom(BUFFER_SIZE)
            save_data_from_form(msg)
    except KeyboardInterrupt:
        pass
    finally:
        socket_server.close()

def run_http_server(host, port):
    server_address = (host, port)
    http = HTTPServer(server_address, HttpHandler)
    try:
        logging.info('Starting http server')
        http.serve_forever()

    except KeyboardInterrupt:
        pass
    finally:
        http.server_close()


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG, format='%(threadName)s %(message)s')
    server = threading.Thread(target=run_http_server, args=(HTTP_HOST, HTTP_PORT))
    server.start()

    socket_server = threading.Thread(target=run_socket_server, args=(SOCKET_HOST, SOCKET_PORT))
    socket_server.start()

    print('Done!')