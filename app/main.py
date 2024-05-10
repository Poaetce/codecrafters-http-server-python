import socket
import threading
import os
import argparse


def encoding_valid(encoding: str) -> bool:
    return encoding in [
        'gzip',
    ]


def encode_content(encoding_type: str, content: bytes) -> bytes:
    match encoding_type:
        case 'gzip':
            import gzip
            return gzip.compress(content)
            
        case _:
            return b''


class Request:
    def __init__(self, request: bytes) -> None:
        lines: list[str] = request.decode().splitlines()

        request_line: list[str] = lines[0].split(' ')
        self.method: str = request_line[0]
        self.path: list[str] = request_line[1].split('/')
        self.version: str = request_line[0]

        self.headers: dict[str, list[str]] = {}
        for line in lines[1:]:
            if not line:
                break
            split_line: list[str] = line.split(': ')
            self.headers[split_line[0].lower()] = split_line[1].split(', ')

        self.body = lines[-1]


def respond(
        status_code: int,
        content: bytes | None = None,
        content_type: str | None = None,
        content_encoding: str | None = None,
) -> bytes:
    CRLF: bytes = b'\r\n'
    
    status_line: bytes = b'HTTP/1.1 '
    headers: list[bytes] = []
    body: bytes = b''

    match status_code:
        case 200:
            status_line += b'200 OK'
        case 201:
            status_line += b'201 Created'
        case 404:
            status_line += b'404 Not Found'

    if content:
        headers.append(f'Content-Length: {len(content)}'.encode())
        headers.append(f'Content-Type: {content_type}'.encode())

        body =  CRLF + content +  CRLF
        
        if content_encoding:
            headers.append(f'Content-Encoding: {content_encoding}'.encode())

    return CRLF.join([status_line, CRLF.join(headers), body])


def main() -> None:
    argument_parser: argparse.ArgumentParser = argparse.ArgumentParser()
    argument_parser.add_argument('--directory')
    arguments: argparse.Namespace = argument_parser.parse_args()

    server_socket: socket.socket = socket.create_server(('localhost', 4221), reuse_port = True)

    while True:
        connection: socket.socket
        address: tuple[str, int]
        connection, address = server_socket.accept()

        thread: threading.Thread = threading.Thread(target = connect, args = [connection, arguments])
        thread.start()


def connect(connection: socket.socket, arguments: argparse.Namespace) -> None:
    directory: str = arguments.directory or '' 

    with connection:
        request: Request = Request(connection.recv(1024))
        response: bytes

        match request.path[1]:
            case '':
                response = respond(200)

            case 'echo':
                content: bytes = '/'.join(request.path[2:]).encode()

                accept_encoding: list[str] | None = None
                content_encoding: str | None = None

                if 'accept-encoding' in request.headers:
                    accept_encoding = request.headers['accept-encoding']
                    for encoding_type in accept_encoding:
                        if encoding_valid(encoding_type):
                            content_encoding = encoding_type
                            break

                if content_encoding:
                    content = encode_content(content_encoding, content)

                response = respond(
                    200,
                    content,
                    'text/plain',
                    content_encoding,
                    )
                
            case 'user-agent':
                response = respond(
                    200,
                    request.headers['user-agent'][0].encode(),
                    'text/plain',
                    )
                
            case 'files':
                file_path: str = os.path.join(directory, request.path[-1])

                match request.method:
                    case 'GET':
                        if os.path.exists(file_path):
                            with open(file_path, 'r') as file:
                                response = respond(
                                    200,
                                    file.read().encode(),
                                    'application/octet-stream',
                                )
                        else:
                            response = respond(404)
                    
                    case 'POST':
                        with open(file_path, 'w') as file:
                            file.write(request.body)
                        response = respond(201)

            case _:
                response = respond(404)

        connection.sendall(response)


if __name__ == '__main__':
    main()
