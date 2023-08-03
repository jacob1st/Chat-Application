# Chat-Application
A sockets based python Tkinter chat application

An updated version of my previous chat application.
----
![chat_picture](https://github.com/jacob1st/Chat-Application/blob/main/Demo/ChatAppImage.png)
![chat_picture1](https://github.com/jacob1st/Chat-Application/blob/main/Demo/ChatAppImage01.png)
Demo Video:
https://github.com/jacob1st/Chat-Application/assets/87782445/47e01bc8-d9da-42e9-af37-da9b62cf8992
----
# Running the application:
First download the three files in the repository, make sure that the client and preferances folder are in the same directory.

To host the server on a LAN:

  - Check the IP address of the machine that will be hosting the server: If on windows, open CMD and run "ipconfig". On Linux, open Terminal and run "ifconfig".
  - You can leave the ADDR variable in server.py blank, and simply run the file. This will start up the server.
  - To connect from another machine from the same LAN, change the ADDR variable in client.py to the IP address from before, then run the file.
  
To host the server publicly:
  - You should set up port forwarding on your router so incoming requests to your router to a specific port can be forwarded to the right machine (the one hosting the server)
  - I recommend looking up a tutorial to do this properly.
  - Connecting to the server will be done the same way, however you must connect using the router's (public) IP, not the hosting machine's private one.

----
# Documentation (sort of)
Some notes about how the server and client should communiate. Feel free to make your own Client to communicate with the server. (The server requires further error-handling for incorrect clients, so until them expect some server crashes)

Messages will be sent using the following protocal:
----
- Any message sent by the client will be followed by a response from the server.
- The server doesn't expect any reponse from the client to its messages, therefore any will be treated as a new message to respond to
- All requests should be encoded/decoded using utf-8
 
Messages from the client/server will be formatted as follows:
----
- reason,parameters,content
- The term "reason" is used to mean the first section of the requests. A list of possible "reasons" can be found below.
- Parameters will be defined with an "=" and separated with a ";". EX: foo=bar;key=value
- For example: to establish a connection, the client will send ```CON,nickname=nick;password=pass;color=#FFFFFF,``` to which the server will respond:
- ```CONVER,time=YYYY-MM-DD HH-MM-SS,OK```. If there are errors, it will be sent as: ```CONVER,time=YYYY-MM-DD HH-MM-SS,error...```
- Messages sent to everyone in the chat will be formatted as (client then server respectively)
- ```CHAT,rec=-ALL,your message here```, server will respond to everyone in turn: ```CHATR,time=YYYY-MM-DD HH-MM-SS;sender=user;rec=-ALL;color=senders color,your message here```
- Note: -ALL is to differentiate from a possible user nickname (nicknames cannot start with a non-letter or number)
- Client and server must format their responses with escape characters before sending.
- Any commas ```,```, semi-colons ```;```, equals ```=``` or forward slashes ```/``` should be escaped using a preliminary forward slash ```/```.
- A nickname of ```foo,bar``` should be sent as ```nickname=foo/,bar```.
- A nickname of ```foo/bar``` must be sent as ```nickname=foo//bar```.
- Escaping characters should only be done in the parameters section of the request. 
- The "reason" section should never have special characters, and anything after the second non-escaped comma will be read as is, as the content.
- An escape character followed by a regular character will have no affect.

 Acceptable reasons from the client:
 ----
 |Reason|Parameters|Explanation|
 |------|----------|-----------|
 |CON|nickname, password, color| Initial message after connecting to the server|
 ||Example Usage: | "CON,nickname=my nick;password=my pass;color=#FFFFFF,"|
 |CHAT|rec|Message to send|
 ||Example Usage: |"CHAT,rec=-ALL,your message goes here"|
 |UPDATE|nickname, password, color|Changing something about your account|
 ||Example Usage: |"UPDATE,nickname=new nickname;color=#FF00FF,"|
 |DISCON||Disconnecting from the chat|
 ||Example Usage: |"DISCON,,"|
 |REF||Refreshing the client; requests previous messages to be reset|
 ||Example Usage: |"REF,,"|
 |USER||Requests a list of all logged in users, and admins|
 ||Example Usage: |"USER,,"|
 |KICK|user|Kicks a user out of the chat (admin required)|
 ||Example Usage: |"KICK,user=foo,You have been kicked for spamming"|
        
Reponses from the server:
----
|Reason|Parameters|Explanation|
|------|----------|-----------|
|CONVER|time|verifying a connection. The content will either be "OK" or an error|
|CHATR|time, sender, rec, color|A chat message sent by a user|
|CONFIRM|time, reason|A confirmation for an UDPATE, REF, or DISCON request|
|INFO|time, sender|A public change to a user always sent to everyone (joining, leaving, changing name, etc...)|
|ERR|time|Client request resulted in an error|
|WARN|time|Something from the server changed or resulted in an error|
|USER|time, num, admin, *| Usually after an INFO, the parameters will list the current users|
- Further explanation on the user tag:
 
     Example: "USER,admin=3;num=4;1=user1;2=admin;3=user3;4=user4;admin0=admin;admin1=admin1;admin2=admin2,Current Users."
     num tells how many users are logged in. Each one will be listed with increment keys.
     admin tells the number of admins, regardless of if they are logged in or not. Admins that are logged in will be listed twice in the list.

  
