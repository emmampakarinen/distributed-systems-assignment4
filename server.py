import socket
import threading

# additional references: 
# - https://realpython.com/intro-to-python-threading/ 
# - https://realpython.com/python-sockets/ 
# - https://www.geeksforgeeks.org/socket-programming-multi-threading-python/ 

thread_lock = threading.Lock() # using locks to edit data/letting only one thread execute blocks of code to avoid race conditions and/or crashes. When one thread has locked a code element, other threads will wait for their turn

# dictionarys for active users and channels users have joined
active_users = {}
channels = {}

def handle_client(c, a):
    print(f"New connection from {a}")
    nickname = c.recv(1024).decode('utf-8')

    # modifying data --> acquiring the lock to avoid race conditions / crashes
    with thread_lock:
        active_users[nickname] = c

    try:
        while True:
            try:
                # data received from client
                data = c.recv(1024).decode('utf-8')
                actionList = data.split(" ", 2)

                if not data or data == "/quit":
                    with thread_lock:
                        active_users.pop(nickname, None) # removing client from active users
                    resp = f"Goodbye {nickname}!"
                    c.send(resp.encode("utf-8"))
                    break

                elif actionList[0] == "/join":
                    channel_name = actionList[1]

                    with thread_lock:
                        # checking if channel name already exists
                        if channel_name not in channels:
                            channels[channel_name] = []

                        # checking if user has already joined the channel
                        if nickname not in channels[channel_name]:
                            channels[channel_name].append(nickname)
                            resp = f"User {nickname} joined channel {channel_name}"
                        else:
                            resp = f"User {nickname} is already in channel {channel_name}"
                    
                    c.send(resp.encode("utf-8"))
                    

                elif actionList[0] == "/leave":
                    if len(actionList) != 2:
                        resp = "Invalid command. Usage: /leave [channel]"
                        c.send(resp.encode("utf-8"))
                    else: 
                        channel_name = actionList[1]
                        with thread_lock:
                            if channel_name in channels and nickname in channels[channel_name]:
                                channels[channel_name].remove(nickname)
                                if not channels[channel_name]:  # if the channel is empty, deleting it
                                    del channels[channel_name]
                            
                            resp = f"User {nickname} removed from channel {channel_name}"
                        
                        c.send(resp.encode("utf-8"))
                        
                elif actionList[0] == "/msgCh":
                    if len(actionList) != 3:
                        resp = "Invalid command. Usage: /msgCh [channel] [message]"
                        c.send(resp.encode("utf-8"))
                    else: 
                        channel_name = actionList[1]
                        message = actionList[2]

                        with thread_lock:
                            if channel_name in channels:
                                msgToSend = f"[{channel_name}] {nickname}: {message}"
                                
                                # Finding all users in the channel given in the actionList
                                for user in channels[channel_name]:
                                    user_c = active_users.get(user)
                                    if user_c:
                                        # sending the message to the user in channel
                                        user_c.send(msgToSend.encode("utf-8"))
                            else:
                                resp = f"Channel {channel_name} does not exist."
                                c.send(resp.encode("utf-8"))
                        

                elif data == "/channels":
                    joined_channels = []

                    for channel, nicknames in channels.items():
                        if nickname in nicknames:
                            joined_channels.append(channel)

                    resp = "Joined channels: " + ", ".join(joined_channels) if joined_channels else "You haven't joined any channels." # conditional response based on if user has joined any channels
                    c.send(resp.encode("utf-8"))

                elif actionList[0] == "/msg":
                    if len(actionList) != 3:
                        resp = "Invalid command. Usage: /msg [nickname] [message]"
                        c.send(resp.encode("utf-8"))
                    else: 
                        user = actionList[1]
                        message = actionList[2]

                        with thread_lock:
                            if user in active_users:
                                msgToSend = f"{nickname}: {message}"
                                user_c = active_users.get(user)
                                if user_c:
                                    user_c.send(msgToSend.encode("utf-8"))
                                    resp = "Message sent."
                                    c.send(resp.encode("utf-8"))
                            else:
                                resp = f"User {user} is not active at the moment."


                elif data == "/active":
                    resp = "Active users: " + ", ".join(active_users)
                    c.send(resp.encode("utf-8"))

                else:
                    resp = "Uknown action, try again."
                    c.send(resp.encode("utf-8"))
                
            
            except ConnectionResetError: # client disconnects with for example ctrl+c
                print("Client disconnected.")
                break
            except Exception as err:
                print(f"An error occurred with the client {nickname}: {err}")
                break
        
    # Client is leaving, acquiring the lock before removing the user from active users list
    finally:
        with thread_lock:
            active_users.pop(nickname, None)  # remove user from the active users list with lock
        c.close()  # making sure socket is closed in case of exception
        print(f"Connection with {nickname} closed.")

 



def main_server():
    HOST, PORT = "localhost", 8000
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # Creating new socket. Syntax: AF_INET = address family using IPv4 addressing, SOCK_STREAM = socket type in this case TCP (UDP would be DGRAM)
    s.bind((HOST, PORT)) # binding socket to the localhost and to port number
    s.listen() # telling the server socket to listen for incoming connections. Starts the TCP listener
    print("Server is running")

    try:
        while True:
            try: 
                client_connection, client_address = s.accept() # when new client tries to connect, accept() returns new socket object client_connection (=the connection) and client_address which is the address including IP and port

                client_thread = threading.Thread(target=handle_client, args=(client_connection, client_address))
                client_thread.start()
            except Exception as e:
                print(f"Server shutting down. Error: {e}")
                break
    except KeyboardInterrupt:
        print("Server shutting down.")
    finally:
        s.close()
        print("Server closed.")


main_server()