import socket


class Request:
    def __init__(self, request: bytes) -> None:
        lines: list[str] = request.decode().splitlines()

        request_line: list[str] = lines[0].split(' ')
        self.method: str = request_line[0]
        self.path: list[str] = request_line[1].split('/')
        self.version: str = request_line[0]

        self.headers: list[str] = lines[1:]


def main() -> None:
    server_socket: socket.socket = socket.create_server(('localhost', 4221), reuse_port=True)
    connection: socket.socket
    address: tuple[str, int]
    connection, address = server_socket.accept()

    with connection:
        request: Request = Request(connection.recv(1024))

        if request.path[1] == '':
            response: str = "HTTP/1.1 200 OK\r\n\r\n"
        elif request.path[1] == 'echo':
            message: str = request.path[2]
            response: str = f"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\nContent-Length: 3\r\n\r\n{message}\r\n"
        else:
            response: str = "HTTP/1.1 404 Not Found\r\n\r\n"

        connection.sendall(response.encode())


if __name__ == "__main__":
    main()
