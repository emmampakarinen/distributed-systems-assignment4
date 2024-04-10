import socket
import threading
from threading import Event

# creating an event object to handle printing correctly
message_received = Event()
# creating an event object to handle exiting the prograrm gracefully
closing = Event()

# Function for listening for incoming messages from other clients (from server)
def listen_messages():
    global message_received
    global closing
    while not closing.is_set():
        try:
            message = server.recv(1024).decode('utf-8')
            if message:
                print("\n" + message)
                message_received.set()
            else:
                print("\nDisconnected from the server.")
                closing.set()
                break
        except Exception as e:
            print(f"Disconnected from the server with an error: {e}")
            closing.set()
            break


HOST, PORT = "localhost", 8000
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
server.connect((HOST, PORT)) # connecting to server
print("Connection to server established!\n")

while True:
    nickname = input("Give nickname to use on the chat: ")
    if (nickname == ""):
        print("Nickname can't be empty.")
    else:
        break    
# sending the nickname to the server
server.sendall(nickname.encode('utf-8'))

# Starting the thread to listen incoming messages from server
listen_thread = threading.Thread(target=listen_messages) 
listen_thread.start()

# Loop for printing menu and sending user action to server
while True:
    try: 

        action = input("\nGive a command or list (/list) commands: ")

        if (action == ""): # not accepting empty commands
            continue
        
        if action == "/list":
            print("\n/join [channel] -- join a new chat channel.")
            print("/leave [channel] -- leave a chat channel.")
            print("/msgCh [channel] [message] -- send a message to a specific channel.")
            print("/channels -- list channels which you have joined.")
            print("/msg [nickname] [message] -- send a private message to a specific user.")
            print("/active -- shows currently active users connected to server.")
            print("/quit -- disconnect from the server.")
            continue

        server.sendall(action.encode('utf-8'))

        if action == "/quit":
            closing.set() # setting closing event to stop the loop in the listen_messages function
            print("Disconnecting from the server...")
            listen_thread.join() # letting the thread finish running
            break
        
        # wait for message/response string from server to be received before printing the menu again
        message_received.wait()
        message_received.clear() # https://stackoverflow.com/questions/60934257/python-using-thread-event-as-an-object-member 
    except KeyboardInterrupt: # if client quits the client with CTRL+C
        print("\nClosing client.")
        closing.set()
        break
    except Exception as e: # Other exception means problems in server side, closing client
        print("Server closed. Closing client.")
        closing.set()
        break
        

server.close()



