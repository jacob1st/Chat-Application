import socket
import threading
import tkinter as tk
import json
import re

# Client and server must format their responses with escape characters before sending.

# Messages will be sent using the following protocal:
# Any message sent by the client will be followed by a response from the server.
# The server doesn't expect any reponse from the client to its messages, therefore any will be treated as a new message to respond to
# All requests should be encoded/decoded using utf-8
# Messages from the client/server will be formatted as follows: reason,parameters,content 
# Parameters will be defined with an "=" and separated with a ";". EX: foo=bar;key=value
# For example: to establish a connection, the client will send "CON,nickname=nick;password=pass;color=#FFFFFF," to which the server will respond:
# CONVER,time=YYYY-MM-DD HH-MM-SS,OK. If there are errors, it will be sent as: "CONVER,time=YYYY-MM-DD HH-MM-SS,error..."
# Messages sent to everyone in the chat will be formatted as (client then server respectively)
# "CHAT,rec=-ALL,your message here", server will respond to everyone in turn: "CHATR,time=YYYY-MM-DD HH-MM-SS;sender=user;rec=-ALL;color=senders color,your message here"
# Note: -ALL is to differentiate from a possible user nickname (nicknames cannot start with a non-letter or number)
# Any commas ",", semi-colons ";", equals "=" or forward slashes "/" should be escaped using a preliminary forward slash "/".
# A nickname of foo,bar should be sent as nickname=foo/,bar.
# The escape character must itself be escaped to use it as a forward slash.
# A nickname of foo/bar must be sent as nickname=foo//bar.
# Escaping characters should only be done in the parameters section of the request. 
# The "reason" should never have special characters, and anything after the second non-escaped comma will be read as is, as the content.
# An escape character followed by a regular character will have no affect.

# Acceptable reasons from the client: ("REASON": parameters: explanation)
#   "CON"       : nickname, password, color                 : Initial message immidiately after connecting to server
#            Example Usage: "CON,nickname=my nick;password=my pass;color=#FFFFFF,"
#   "CHAT"      : rec (-ALL or a specific username)  : A message you're sending
#            Example Usage: "CHAT,rec=-ALL,your message goes here"
#   "UPDATE"    : nickname, password, color                 : Changing something about your account
#            Example Usage: "UPDATE,nickname=new nickname,"
#   "DISCON"    :                                           : Disconnecting from the chat
#            Example Usage: "DISCON,,"
#   "REF"       :                                           : Refreshing the client and requests previous messages to be resent
#            Example Usage: "REF,,"
#   "USER"      :                                           : Requests a list of logged in users
#            Example Usage: "USER,,"
#   "KICK"      : user                                      : Kicks a user out of the chat (admin required)
#            Example Usage: "KICK,user=foo,You have been kicked for spamming"

# Reponses from the server: 
#   "CONVER"    : time                      : verifing a connection.
#   "CHATR"     : time, sender, rec, color  : A message sent by another user.
#   "CONFIRM"   : time, reason,             : A confirmation for an UPDATE, REF, DISCON request.
#   "INFO"      : time, sender              : A public change to a user always sent to everyone (joining, leaving, changing name, etc...).
#   "ERR"       : time                      : Client requests resulted in an error.
#   "WARN"      : time                      : Something changed from the server.
#   "USER"      : time, num admin *         : Usually after an INFO, the parameters will be the current connected users.
    # USER,admin=3;num=4;1=user1;2=admin;3=user3;4=user4;admin0=admin;admin1=admin1;admin2=admin2,Current Users.
    # num tells how many users are logged in. Each one will be listed with increment keys.
    # admin tells the number of admins, regardless of if they are logged in or not. Admins that are logged in will be listed twice in the list.

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
    parameters = msg[:parameters_match.end() - 1]

    # replaced = re.sub("/(?=[^/]|(//))", "", parameters)
    # The rest is the content
    content = msg[parameters_match.end():]

    all_parameters = {}
    individual_p = re.split("(?<=[^/])(//){0,9999999};", parameters)
    for par in individual_p:
        if par:
            parameter = re.split("(?<=[^/])(//){0,9999999}=", par)
            all_parameters[parameter[0]] = re.sub("/(?=[^/]|(//))", "", parameter[2])
    
    return reason, all_parameters, content

def set_nickname(nickname):
    global global_nickname
    global_nickname = nickname
    label['text'] = nickname
    label['fg'] = pref['message-color']

def load_json(file):
    with open(file, "r") as jsonfile:
        data = json.load(jsonfile) # Reading the file
        jsonfile.close()
    
    return data

# Client Socket connected to server
def connect_to_server(nickname, password, color):
    global connected
    if not connected:
        client.connect((ADDR, PORT))
    connected = True
    connection_message = f"CON,nickname={format(nickname)};password={format(password)};color={format(color)},"
    client.send(connection_message.encode(FORMAT))
    verify_connection(nickname)

def start():
    recv_thread = threading.Thread(target=listen_for_msg)
    recv_thread.start()

def verify_connection(nickname):
    verification = client.recv(1024).decode(FORMAT)
    reason, parameters, content = splice_response(verification)
    if reason == "CONVER":
        if content == "OK":
            set_nickname(nickname)
            draw_main_screen()
            start()
        else:
            error_label['text'] = content
    else:
        error_label['text'] = "Unexpected response from server: " + verification

    
# Seperate Thread to listen for incoming messages from the server
def listen_for_msg():
    while connected:
        final_message = client.recv(2048).decode(FORMAT)
        reason, paramters, message = splice_response(final_message)
        if reason == "CHATR":
            color = paramters["color"]
            time = paramters["time"]
            sender = paramters["sender"]

            # start_message = texts.index("end-1c")
            start_color = texts.index("end-1c")
            texts.insert('end', f"{sender} ")
            end_color = texts.index("end-1c")
            start_timestamp = texts.index("end-1c")
            texts.insert('end', f"{time}")
            if paramters["rec"] == "-ALL":
                texts.insert('end', " (To everyone).")
            else:
                texts.insert('end', f" (To {paramters['rec']}).")
            end_timestamp = texts.index("end-1c")
            texts.insert('end', "\n - " + message + "\n")
            # end_message = texts.index("end-1c")

            # if sender != global_nickname:
            #     texts.tag_add(global_nickname, start_message, end_message)
            #     texts.tag_configure(global_nickname, background="#50505E", relief="sunken", borderwidth=3, lmargin1=10)
            # else:
            #     texts.tag_add(sender, start_message, end_message)
            #     texts.tag_configure(sender, background="#60606E", relief="raised", borderwidth=3, lmargin1=10)

            texts.tag_add(sender + "COLOR", start_color, end_color)
            texts.tag_configure(sender + "COLOR", foreground=color, spacing3=.05, spacing1=20)

            texts.tag_add(sender + "TIMESTAMP" + str(color), start_timestamp, end_timestamp)
            texts.tag_configure(sender + "TIMESTAMP" + str(color), font="Arial 8", spacing3=.05, spacing1=20)

        elif reason == "ERR" or reason == "WARN":
            warnings['text'] = f"{reason}: {message}."
        elif reason == "INFO":
            texts.insert('end', f"{paramters['time']} {message} \n")
        elif reason == "CONFIRM":
            if paramters["reason"] == "DISCON":
                print("Logged out successfully...")
            if paramters["reason"] == "REF":
                print("Refreshing...")
            if paramters["reason"] == "UPDATE":
                if message == "OK":
                    global awaited_changes
                    if awaited_changes[0]:
                        set_nickname(awaited_changes[0])
                    if awaited_changes[1]:
                        pref["message-color"] = awaited_changes[1]
                        label["fg"] = awaited_changes[1]
                    with open("preferances.json", "w") as outfile:
                        json.dump(pref, outfile)
                    awaited_changes = ['', '', '']
                else:
                    awaited_changes = ['', '', '']
                    submit_warnings['text'] = message
        elif reason == "USER":
            reset_users(paramters)
        else:
            warnings['text'] = f"Unkown message from server: {final_message}"

    root.quit()

def send(msg):
    message = msg.encode(FORMAT)
    client.send(message)

def sending_messages(entry_message):
    if (len(entry_message) > 300):  # check if message is too long
        warnings['text'] = 'Message too long'
    else:
        warnings['text'] = ''
        texts.yview_moveto(1)  # scroll to bottom of page
        send(f"CHAT,rec={msg_type_clicked.get()},{entry_message}")
        entry.delete(0, 'end')
        if entry_message == "!DISCONNECT":
            root.destroy()

def refresh_chat():
    texts.delete("1.0","end")
    send("REF,,")

def enter_key_pressed(event):
    sending_messages(entry.get())

def draw_main_screen():
    starting_frame.place_forget()
    customize_frame.place_forget()
    frame.place(relx=0, rely=0, relwidth=1, relheight=1)

def draw_customize_screen():
    frame.place_forget()
    customize_frame.place(relx=0,rely=0,relwidth=1,relheight=1)

def drop_clicked(*args):
    if msg_type_clicked.get() == "-REFRESH":
        send("USER,,")

def close_window():
    global connected
    if connected:
        send("DISCON,,")
        connected = False
    else:
        root.quit()

def submit_updates(new_name, new_color, new_password):
    if not new_name and not new_color and not new_password:
        submit_warnings['text'] = "You must change at least one thing." 
        return 0
    response = "UPDATE,"
    if new_name:
        awaited_changes[0] = new_name
        response += f"nickname={format(new_name)};"
    if new_color:
        awaited_changes[1] = new_color
        response += f"color={new_color};"
    if new_password:
        awaited_changes[2] = new_password
        response += f"password={format(new_password)};"
    
    response = response[:-1]
    response += ","

    send(response)
    change_color_entry.delete(0, 'end')
    change_nickname_entry.delete(0, 'end')
    change_password_entry.delete(0, 'end')

def reset_users(parameters):
    msg_type_drop['menu'].delete(0, 'end')
    msg_type_clicked.set("-ALL")

    msg_type_drop['menu'].add_command(label="-ALL", command=tk._setit(msg_type_clicked, "-ALL"))
    msg_type_drop['menu'].add_command(label="-REFRESH", command=tk._setit(msg_type_clicked, "-REFRESH"))
    for i in range(int(parameters["num"])):
        msg_type_drop['menu'].add_command(label=parameters[str(i)], command=tk._setit(msg_type_clicked, parameters[str(i)]))

def kick_user():
    user_to_kick = msg_type_clicked.get()
    send(f"KICK,user={format(user_to_kick)},{entry.get()}")

PORT = 6666
ADDR = "192.168.1.199"
FORMAT = 'utf-8'
HEADER = 64

HEIGHT = 700
WIDTH = 850

connected = False
awaited_changes = ['', '', ''] # Holds a pending change for nickname, color, password

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
global_nickname = ""
pref = load_json("preferances.json")

##**Actually creating the GUI**

root = tk.Tk()
root.protocol("WM_DELETE_WINDOW", close_window)

canvas = tk.Canvas(root, height=HEIGHT, width=WIDTH)
canvas.pack()

### Starting Screen
starting_frame = tk.Frame(root, bg=pref["login-page-bg"])
starting_frame.place(relx=0, rely=0, relheight=1, relwidth=1)

# nickname entry
enter_nick_entry = tk.Entry(starting_frame, bg="#777777", relief="ridge", font="Calibri 13")
enter_nick_entry.place(relx=0.39, rely=.3, relwidth=.28, relheight=.07) 

# Login button
login_button = tk.Button(starting_frame, text="LOGIN", font="Arial 12", bg="#FFFFFF", fg="#000000", relief="sunken", command=lambda: connect_to_server(enter_nick_entry.get(), enter_pass_entry.get(), pref["message-color"]))
login_button.place(relx=.68, rely=0.4, relwidth=.12, relheight=.07)

# Login label
label = tk.Label(starting_frame, text="Enter nickname: ", fg="#FFFFFF", bg="#000000", relief="raised", font="Arial 12")
label.place(relx=.2, rely=0.3, relwidth=.18, relheight=.07)

# Login label
password_label = tk.Label(starting_frame, text="Enter password: ", fg="#FFFFFF", bg="#000000", relief="raised", font="Arial 12")
password_label.place(relx=0.2, rely=0.4, relwidth=.18, relheight=.07)

# password entry
enter_pass_entry = tk.Entry(starting_frame, bg="#777777", relief="ridge", font="Calibri 13", show="*")
enter_pass_entry.place(relx=0.39, rely=.4, relwidth=.28, relheight=.07) 

# Welcome label
welcome_label = tk.Label(starting_frame, text="Welcome to the chat!", fg=pref["login-page-text"], bg=pref["login-page-bg"], relief="raised", font="Arial 30")
welcome_label.place(relx=.2, rely=0.1, relwidth=.6, relheight=.14)

# Error Message
error_label = tk.Label(starting_frame, text="", fg="#FF3333", bg=pref["login-page-bg"], font="Arial 12")
error_label.place(relx=.1, rely=0.6, relwidth=1, relheight=.07)

# Error Message
info_label = tk.Label(starting_frame, text="*Passwords are only required for registered users", fg="#3CE312", bg=pref["login-page-bg"], font="Arial 12")
info_label.place(relx=.1, rely=0.5, relwidth=1, relheight=.07)

# Blue frame (for entry)
frame = tk.Frame(root, bg=pref["bg-color"])
# full_frame.place(relx=0, rely=0, relwidth=1, relheight=1)

# Where the text will show
texts = tk.Text(frame, bg=pref["text-background"], fg=pref["default-text-color"], wrap=tk.WORD, relief="ridge", font=pref["text-font"], border=4, spacing3=15)
texts.place(relx=0.1, rely=0.1, relwidth=0.8, relheight=0.7)

# placing a scrollbar
scrollbar = tk.Scrollbar(frame)
scrollbar.place(relx=.98, rely=0, relwidth=.02, relheight=.8)
# scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

# getting the scrollbar to work
scrollbar.config(command=texts.yview)
texts.config(yscrollcommand=scrollbar.set)

# Send button
button = tk.Button(frame, text="Send!", font="Arial 12", relief="raised", border=3, bg=pref["send-button-bg"], fg=pref["send-button-fg"], command=lambda: sending_messages(entry.get()))
button.place(relx=.7, rely=0.87, relwidth=.1, relheight=.08)

# Top button
top_button = tk.Button(frame, text="\u25b2", font="Arial 8", bg=pref["other-button-bg"], fg=pref["other-button-fg"], command=lambda: texts.yview_moveto(0))
top_button.place(relx=.93, rely=0.03, relwidth=.05, relheight=.05)

# Bottom button
bottom_button = tk.Button(frame, text="\u25bc", font="Arial 8", bg=pref["other-button-bg"], fg=pref["other-button-fg"], command=lambda: texts.yview_moveto(1))
bottom_button.place(relx=.93, rely=0.75, relwidth=.05, relheight=.05)

# Bottom button
disconnect_button = tk.Button(frame, text="DISCONNECT", font="Arial 12", bg=pref["other-button-bg"], fg=pref["other-button-fg"], command=lambda: close_window())
disconnect_button.place(relx=.6, rely=.03, relwidth=.15, relheight=.05)

# Bottom button
customize_button = tk.Button(frame, text="CUSTOMIZE", font="Arial 12", bg=pref["other-button-bg"], fg=pref["other-button-fg"], command=lambda: draw_customize_screen())
customize_button.place(relx=.2, rely=.03, relwidth=.15, relheight=.05)

# Refresh button
refresh_button = tk.Button(frame, text="\u27f3", font="Arial 14", bg=pref["other-button-bg"], fg=pref["other-button-fg"], command=lambda: refresh_chat())
refresh_button.place(relx=.93, rely=0.1, relwidth=.05, relheight=.05)

# Message label
label = tk.Label(frame, text="User:", bg=pref["bg-color"], fg="#FFFFFF", font="Arial 12")
label.place(relx=.03, rely=0.86, relwidth=.1, relheight=.1)

# To send message
entry = tk.Entry(frame, bg=pref["text-entry-bg"], fg=pref["text-entry-fg"], relief="sunken", border=7, font="Calibri 13", insertbackground='white')
entry.bind("<Return>", enter_key_pressed)
entry.place(relx=0.15, rely=.87, relwidth=.55, relheight=.08) 

# Message warnings
warnings = tk.Label(frame, fg='red',bg=pref["bg-color"], font="Calibri 14")
warnings.place(relx=0.1, rely=0.8, relwidth=.6, relheight=.05)

# datatype of menu text
msg_type_clicked = tk.StringVar()
  
# initial menu text
msg_type_clicked.set("-ALL")
msg_type_clicked.trace("w", drop_clicked)

# Create Dropdown menu
msg_type_drop = tk.OptionMenu(frame, msg_type_clicked, *["-ALL", "-REFRESH"])
msg_type_drop.config(bg=pref["dropdown-bg"], fg=pref["dropdown-fg"], activebackground=pref["active-dropdown-bg"], direction="above")
msg_type_drop.place(relx=.82, rely=.87, relwidth=.16, relheight=.05)

msg_type_label = tk.Label(frame, text="Select recipients: ", bg=pref["bg-color"], fg="#FFFFFF", font="Calibri 14")
msg_type_label.place(relx=.82, rely=.82, relwidth=.16, relheight=.05)

kick_button = tk.Button(frame, text="Kick", bg="red", command=lambda: kick_user())
kick_button.place(relx=.82, rely=.95, relwidth=.1, relheight=.05)

# Customization
customize_frame = tk.Frame(root, bg=pref["custom-bg"])

# Go back button
main_screen_button = tk.Button(customize_frame, text="GO BACK", font="Arial 12", bg=pref["other-button-bg"], fg=pref["other-button-fg"], command=lambda: draw_main_screen())
main_screen_button.place(relx=.1, rely=.1, relwidth=.15, relheight=.05)

# Changes entries
change_nickname_entry = tk.Entry(customize_frame, bg=pref["custom-entry"], relief="sunken", border=7, font="Calibri 13")
change_nickname_entry.place(relx=0.35, rely=.2, relwidth=.2, relheight=.1) 

change_nickname_label = tk.Label(customize_frame, text="Change nickname: ", bg=pref["custom-label-bg"], fg=pref["custom-label-fg"], font="Calibri 14")
change_nickname_label.place(relx=.1, rely=.2, relwidth=.2, relheight=.1)

# Changes entries
change_color_entry = tk.Entry(customize_frame, bg=pref["custom-entry"], relief="sunken", border=7, font="Calibri 13")
change_color_entry.place(relx=0.35, rely=.4, relwidth=.2, relheight=.1) 

change_color_label = tk.Label(customize_frame, text="Change color: ", bg=pref["custom-label-bg"], fg=pref["custom-label-fg"], font="Calibri 14")
change_color_label.place(relx=.1, rely=.4, relwidth=.2, relheight=.1)

# Changes entries
change_password_entry = tk.Entry(customize_frame, bg=pref["custom-entry"], relief="sunken", border=7, font="Calibri 13")
change_password_entry.place(relx=0.35, rely=.6, relwidth=.2, relheight=.1) 

change_password_label = tk.Label(customize_frame, text="Change password: ", bg=pref["custom-label-bg"], fg=pref["custom-label-fg"], font="Calibri 14")
change_password_label.place(relx=.1, rely=.6, relwidth=.2, relheight=.1)

# Submit
submit_changes_button = tk.Button(customize_frame, text="SUBMIT", font="Arial 12", bg=pref["other-button-bg"], fg=pref["other-button-fg"], command=lambda: submit_updates(change_nickname_entry.get(), change_color_entry.get(), change_password_entry.get()))
submit_changes_button.place(relx=.6, rely=.8, relwidth=.15, relheight=.05)

# Message warnings
submit_warnings = tk.Label(customize_frame, fg='red',bg=pref["custom-bg"], font="Calibri 14")
submit_warnings.place(relx=0.1, rely=0.9, relwidth=.8, relheight=.05)

root.mainloop()