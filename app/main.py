import socket
import threading
import os
import argparse


class Request:
    def __init__(self, request: bytes) -> None:
        lines: list[str] = request.decode().splitlines()

        request_line: list[str] = lines[0].split(' ')
        self.method: str = request_line[0]
        self.path: list[str] = request_line[1].split('/')
        self.version: str = request_line[0]

        self.headers: dict[str, str] = {}
        for line in lines[1:]:
            if not line:
                break
            split_line: list[str] = line.split(': ')
            self.headers.update({split_line[0]: split_line[1]})

        self.body = lines[-1]


def respond(status_code: int, content: str | None = None, content_type: str | None = None) -> str:
    CRLF: str = '\r\n'
    
    status_line: str = "HTTP/1.1 "
    headers: list[str] = []
    body: str = ''

    match status_code:
        case 200:
            status_line += "200 OK"
        case 201:
            status_line += "201 Created"
        case 404:
            status_line += "404 Not Found"

    if content:
        headers.append(f"Content-Length: {len(content)}")
        headers.append(f"Content-Type: {content_type}")

        body =  CRLF + content +  CRLF

    return CRLF.join([status_line, CRLF.join(headers), body])


def main() -> None:
    argument_parser: argparse.ArgumentParser = argparse.ArgumentParser()
    argument_parser.add_argument("--directory")
    arguments: argparse.Namespace = argument_parser.parse_args()

    server_socket: socket.socket = socket.create_server(("localhost", 4221), reuse_port = True)

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
        response: str

        match request.path[1]:
            case '':
                response = respond(200)

            case "echo":
                response = respond(
                    200,
                    '/'.join(request.path[2:]),
                    "text/plain",
                    )
                
            case "user-agent":
                response = respond(
                    200,
                    request.headers["User-Agent"],
                    "text/plain",
                    )
                
            case "files":
                file_path: str = os.path.join(directory, request.path[-1])

                match request.method:
                    case "GET":
                        if os.path.exists(file_path):
                            with open(file_path, 'r') as file:
                                response = respond(
                                    200,
                                    file.read(),
                                    "application/octet-stream",
                                )
                        else:
                            response = respond(404)
                    
                    case "POST":
                        with open(file_path, 'w') as file:
                            file.write(request.body)
                        response = respond(201)

            case _:
                response = respond(404)

        connection.sendall(response.encode())


if __name__ == "__main__":
    main()
