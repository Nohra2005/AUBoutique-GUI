from socket import *
import threading
#from protocol import client_handler

# Server setup
server = socket(AF_INET, SOCK_STREAM)
server.bind(('localhost', 8888))
server.listen(5)

print("Server listening on port 8888...")

while True:
    client_socket, addr = server.accept()
    print(f"Connection from {addr}")

    # Start a new thread for the client
    #client_thread = threading.Thread(target=client_handler, args=(client_socket,))
    #client_thread.start()