import socket


class Request:
    def __init__(self, request: bytes) -> None:
        lines: list[str] = request.decode().splitlines()

        self.http_method: str
        self.path: str
        self.http_version: str
        self.http_method, self.path, self.http_version = lines[0].split(' ')

        self.headers: list[str] = lines[1:]


def main() -> None:
    server_socket: socket.socket = socket.create_server(('localhost', 4221), reuse_port=True)
    connection: socket.socket
    address: tuple[str, int]
    connection, address = server_socket.accept()

    with connection:
        request: Request = Request(connection.recv(1024))

        if request.path == '/':
            response: str = "HTTP/1.1 200 OK\r\n\r\n"
        else:
            response: str = "HTTP/1.1 404 Not Found\r\n\r\n"

        connection.sendall(response.encode())


if __name__ == "__main__":
    main()
