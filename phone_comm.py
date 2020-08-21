import socket
server_sock = None
connected = False
def open_server_socket(ipaddr, port):
    global server_sock, g_ipaddr, g_port, connected
    # Next 3 lines are a dirty way to make the stop function work
    g_ipaddr = ipaddr
    g_port = port
    connected = False

    server_sock= socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.bind((ipaddr,port))
    server_sock.listen(5)


    print(f'Listening for connection on {ipaddr}:{port}')
    client_sock, client_info = server_sock.accept()
    connected = True
    print("Accepted connection from ", client_info)
    return client_sock, server_sock, client_info

#Creates and closes a connection to the server socket in order to stop it from blocking
def stop():
    global server_sock
    if (server_sock):
        if not connected:
            socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect( (g_ipaddr, g_port))
        server_sock.close()
        server_sock = None
