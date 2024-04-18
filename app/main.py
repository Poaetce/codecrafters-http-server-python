import socket


def main() -> None:
    server_socket: socket.socket = socket.create_server(('localhost', 4221), reuse_port=True)
    connection: socket.socket
    address: tuple[str, int]
    connection, address = server_socket.accept()

    with connection:
        data: bytes = connection.recv(1024)
        connection.sendall(b"HTTP/1.1 200 OK\r\n\r\n")


if __name__ == "__main__":
    main()
