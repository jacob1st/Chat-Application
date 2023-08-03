import socket
import threading
from datetime import datetime
import re
import time


# Set up updating as working (possibly changeing customization options and writing to json)
# admin perms
# dming
# refreshing (client keeps log, server-side)
# user list upon info, and updating dropdown. also refreshing user list
# error catching, especially upon closing

class Client:
    def __init__(self, client_conn, client_address, nickname,  color):
        self.conn = client_conn
        self.address = client_address
        self.nickname = nickname
        self.color = color
        self.message_log = []
        self.admin = False
        self.connected = True

    def send(self, message, save=False):
        if save:
            if len(self.message_log) > 20:
                self.message_log.pop(0)
            self.message_log.append(message)

        self.conn.send(message.encode(FORMAT))

    def refresh(self):
        for i in self.message_log:
            self.conn.send(i.encode(FORMAT))
            time.sleep(TIME_DELAY)

def get_registered_users(registered_users):
    # Using readlines()
    users = open('registeredUsers.txt', 'r')
    lines = users.readlines()
 
    # Strips the newline character
    for line in lines:
        line = line.split(",")
        registered_users[line[0]] = line[1]
    
    return registered_users

def format(parameter):
    i = 0
    escape = ",;=/"
    while i < len(parameter):
        if parameter[i] in escape:
            parameter = parameter[:i] + "/" + parameter[i:]
            i += 1
        i += 1

    return parameter

def splice_response(msg):
    # separate the reason by finding the first comma (there are set reasons, so no escaped commas should be found before this)
    reason_match = re.search("^[a-zA-z]*,", msg)
    reason = reason_match.group()[:-1]
    msg = msg[reason_match.end():]

    # Seperate the parameters by finding the next unescaped comma
    parameters_match = re.search("[^/](//){0,9999999},", msg)
    if parameters_match:
        parameters = msg[:parameters_match.end() - 1]
    else:
        parameters = ""

    # replaced = re.sub("/(?=[^/]|(//))", "", parameters)
    # The rest is the content
    if parameters_match:
        content = msg[parameters_match.end():]
    else: 
        content = msg[1:]

    all_parameters = {}
    individual_p = re.split("(?<=[^/])(//){0,9999999};", parameters)
    for par in individual_p:
        if par:
            parameter = re.split("(?<=[^/])(//){0,9999999}=", par)
            all_parameters[parameter[0]] = re.sub("/(?=[^/]|(//))", "", parameter[2])
    
    return reason, all_parameters, content

def update_message_log(new_message):
    if len(public_message_log) > 20:
        public_message_log.pop(0)

    public_message_log.append(new_message)

def log(message):
    message = datetime.now().strftime('%Y-%m-%d %H:%M:%S') + " : " + message
    print(message)
    private_server_log.append(message)

def verify_login_params(parameters):
    if "nickname" in parameters and "password" in parameters and "color" in parameters:
        valid_nick = validate_nick(parameters["nickname"], parameters["password"])
        return valid_nick
    else:
        return ["ERROR", "Incorrect paramters. nickname, password, and color are required"]

def validate_nick(nickname, password):
    for user in all_clients:
        if nickname == user:
            return ["ERROR", "User is already logged in"]
        
    for ru in registered_users:
        if nickname == ru:
            if password == registered_users[ru]:
                return ["OK", "Logging in..."]
            else:
                return ["ERROR", "User is a registered user"]
            
    if not nickname[0].isalpha():
        return ["ERROR", "Username must start with a letter"]
    
    if len(nickname) < 2 or len(nickname) > 16:
        return ["ERROR", "Username must be between lengths 2 and 16"]
    
    return ["OK", "Connecting to chat..."]

def validate_color(color):
    match = re.search(r'^#(?:[0-9a-fA-F]{3}){1,2}$', color)
    if match:
        return color
    else:
        return "#FFFFFF"

def broadcast(message):
    public_message_log.append(message)
    for client in all_clients:
        all_clients[client].send(message, save=True)

def send_user_list(send_to = False):
    message = f"USER,time={datetime.now().strftime('%Y-%m-%d %H:%M:%S')};num={len(all_clients)};admin={len(registered_users)}"
    i = 0
    for client in all_clients:
        message += f";{i}={client}"
        i += 1

    i = 0
    for user in registered_users:
        message += f";admin{i}={user}"
        i += 1

    message += ","

    if send_to:
        send_to.send(message)
    else:
        broadcast(message)

def disconnect_user(dis_client):
    dis_client.connected = False
    log(f"{dis_client.address} has disconnected")
    dis_client.conn.close()
    all_clients.pop(dis_client.nickname)
    broadcast(f"INFO,time={datetime.now().strftime('%Y-%m-%d %H:%M:%S')};sender={format(dis_client.nickname)},{dis_client.nickname} has disconnected")
    time.sleep(TIME_DELAY)
    send_user_list()

def connected_client(client_conn, client_addr, valid_client):
    log(f"{client_addr} connected to the chat")
    all_clients[valid_client.nickname] = valid_client
    broadcast(f"INFO,time={datetime.now().strftime('%Y-%m-%d %H:%M:%S')};sender={format(valid_client.nickname)},{valid_client.nickname} has joined the chat!")
    time.sleep(TIME_DELAY)
    send_user_list()
    while valid_client.connected:
        try:
            message = client_conn.recv(2048).decode(FORMAT)
        except ConnectionResetError:
            log(f"{client_addr} has disconnected unexpectedly...")
            disconnect_user(valid_client)
            break

        reason, paramters, actual_message = splice_response(message)
        if valid_client.connected == False:
            break
        if reason == "DISCON":
            valid_client.send(f"CONFIRM,time={datetime.now().strftime('%Y-%m-%d %H:%M:%S')};reason=DISCON,Disconnected Successfully.")
            disconnect_user(valid_client)
            break
        elif reason == "CHAT":
            if "rec" in paramters:
                if paramters["rec"] == "-ALL":
                    broadcast(f"CHATR,time={datetime.now().strftime('%Y-%m-%d %H:%M:%S')};sender={format(valid_client.nickname)};rec=-ALL;color={valid_client.color},{actual_message}")
                elif paramters["rec"] in all_clients:
                    all_clients[paramters["rec"]].send(f"CHATR,time={datetime.now().strftime('%Y-%m-%d %H:%M:%S')};sender={format(valid_client.nickname)};rec={format(paramters['rec'])};color={valid_client.color},{actual_message}", save=True)
                    valid_client.send(f"CHATR,time={datetime.now().strftime('%Y-%m-%d %H:%M:%S')};sender={format(valid_client.nickname)};rec={format(paramters['rec'])};color={valid_client.color},{actual_message}", save=True)
                else:
                    valid_client.send(f"ERR,time={datetime.now().strftime('%Y-%m-%d %H:%M:%S')},Error: {paramters['rec']} Unrecognized recipient.")
            else:
                valid_client.send(f"ERR,time={datetime.now().strftime('%Y-%m-%d %H:%M:%S')},Error: rec parameter required.")
        elif reason == "UPDATE":
            valid_update_request = True
            nickname_changed = False
            color_changed = False
            password_changed = False
            previous_nickname = valid_client.nickname
            response_message = ""
            public_changes = ""
            if "nickname" in paramters:
                valid_nickname = validate_nick(paramters["nickname"], "")
                if valid_nickname[0] == "ERROR":
                    response_message += f"Error: {format(valid_nickname[1])}. "
                    valid_update_request = False
                else:
                    public_changes += f"name changed to {paramters['nickname']} "
                    nickname_changed = True
            if "color" in paramters:
                proper_color = validate_color(paramters["color"])
                if proper_color == paramters["color"]:
                    color_changed = True
                    public_changes += f"color changed to {proper_color} "
                else:
                    response_message += f"Error: Color not recgnized as Hex color. "
                    valid_update_request = False
            if "password" in paramters:
                password_changed = True
            
            if valid_update_request:
                if nickname_changed:
                    valid_client.nickname = paramters["nickname"]
                    all_clients[paramters["nickname"]] = all_clients.pop(previous_nickname)
                    if valid_client.admin:
                        registered_users[paramters["nickname"]] = registered_users.pop(previous_nickname)
                    log(f"{client_addr} changed their nickname to {paramters['nickname']}")
                if color_changed:
                    valid_client.color = paramters["color"]
                    log(f"{client_addr} changed their color to {paramters['color']}")
                if password_changed:
                    log(f"{client_addr} changed their password")
                    # valid_client.password = paramters["password"]
                    pass
                valid_client.send(f"CONFIRM,time={datetime.now().strftime('%Y-%m-%d %H:%M:%S')};reason=UPDATE,OK")
                broadcast(f"INFO,time={datetime.now().strftime('%Y-%m-%d %H:%M:%S')};sender={format(valid_client.nickname)},{format(previous_nickname)}'s {public_changes}")
                time.sleep(TIME_DELAY)
                send_user_list()
            else:
                valid_client.send(f"CONFIRM,time={datetime.now().strftime('%Y-%m-%d %H:%M:%S')};reason=UPDATE,{response_message}")
        elif reason == "REF":
            valid_client.send(f"CONFIRM,time={datetime.now().strftime('%Y-%m-%d %H:%M:%S')};reason=REF,Resending messages...")
            valid_client.refresh()
        elif reason == "USER":
            send_user_list(valid_client)
        elif reason == "KICK":
            if valid_client.admin:
                if "user" in paramters:
                    all_clients[paramters["user"]].send(f"WARN,time={datetime.now().strftime('%Y-%m-%d %H:%M:%S')},You have been kicked for reason: {actual_message}")
                    all_clients[paramters["user"]].connected = False
                    all_clients.pop(paramters["user"])
                    time.sleep(TIME_DELAY)
                    broadcast(f"INFO,time={datetime.now().strftime('%Y-%m-%d %H:%M:%S')};sender={format(valid_client.nickname)},{format(paramters['user'])} has been kicked by {valid_client.nickname}")
                    time.sleep(TIME_DELAY)
                    send_user_list()
            else:
                valid_client.send(f"ERR,time={datetime.now().strftime('%Y-%m-%d %H:%M:%S')},Error: Must be an admin to preform that action.")
        else:
            valid_client.send(f"ERR,time={datetime.now().strftime('%Y-%m-%d %H:%M:%S')},Error: Unknown reason: {format(reason)}.")

    client_conn.close()

def initial_connection(client_conn, client_addr):
    temp_client = Client(client_conn, client_addr, "TEMP", "#FFFFFF")
    while True:
        initial_response = client_conn.recv(1024).decode(FORMAT)
        reason, parameters, message = splice_response(initial_response)
        log(f"New connection from: {client_addr} with request: {reason} {parameters}")

        if reason != "CON":
            log(f"Unexpected request from {client_addr}.")
            temp_client.send(f"CONVER,time={datetime.now().strftime('%Y-%m-%d %H:%M:%S')},Error: Unknown connection attempt. Expected: 'CON/,nickname/,password/,color'")
        else:
            valid_nick = verify_login_params(parameters)
            if valid_nick[0] == "ERROR":
                log(f"Invalid nickname from {client_addr}.")
                temp_client.send(f"CONVER,time={datetime.now().strftime('%Y-%m-%d %H:%M:%S')},Error: {format(valid_nick[1])}")
            else:
                if valid_nick[1] == "Logging in...":
                    temp_client.admin = True

                color = validate_color(parameters["color"])
                nickname = parameters["nickname"]
                temp_client.nickname = nickname
                temp_client.color = color
                temp_client.send(f"CONVER,time={datetime.now().strftime('%Y-%m-%d %H:%M:%S')},OK")
                connected_client(client_conn, client_addr, temp_client)
                break

ADDR = ""
PORT = 6666
HEADER = 64
FORMAT = 'utf-8'
TIME_DELAY = .05
registered_users = {}
registered_users = get_registered_users(registered_users)

all_clients = {}
private_server_log = []
public_message_log = []

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((ADDR, PORT))

def end_server():
    while True:
        stop_server = input()
        if stop_server == "!QUIT":
            log("Closing all connections and exiting...")
            for client in all_clients:
                all_clients[client].send(f"WARN,time={datetime.now().strftime('%Y-%m-%d %H:%M:%S')},Server [shutting down] unexpectedly. Please close down the chat and try again later.".encode(FORMAT))
                all_clients[client].conn.close()
                log("Successfully closed one connection.")
            server.close()
            break

def start_server():
    server.listen()
    log(f"Server [listening] on {ADDR}:{PORT}...")
    closingThread = threading.Thread(target=end_server)
    closingThread.start()
    while True:
        try:
            client_conn, client_addr = server.accept()
        except OSError:
            break
        
        thread = threading.Thread(target=initial_connection, args=(client_conn,client_addr,))
        thread.start()
        log(f"{int((threading.active_count()-2))} active connections")

log(f"Chat is [Starting] on {ADDR}:{PORT}")
start_server()