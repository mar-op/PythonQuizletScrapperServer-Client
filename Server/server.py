import threading
import json
import os
import datetime
import socket

#json and rpc Host/Port Configuration
JSON_HOST='0.0.0.0'
JSON_PORT=9001
RPC_HOST='0.0.0.0'
RPC_PORT=9002

#logging
LOG_DIR='logs'
os.makedirs(LOG_DIR,exist_ok=True)
LOG_FILE=os.path.join(LOG_DIR,'activity_log.jsonl')
log_lock=threading.Lock()
    #append an event dict as a JSON line with timestamp to the log file.
def log_event(event):
    record={'timestamp':datetime.datetime.now().isoformat(),**event}
    with log_lock:
        with open(LOG_FILE,'a',encoding='utf-8') as f:
            f.write(json.dumps(record)+'\n')

#user accounts 
USERS_DIR='users'
os.makedirs(USERS_DIR,exist_ok=True)
#module directory set up
MODULE_DIR='modules'
os.makedirs(MODULE_DIR,exist_ok=True)
#json reciever set up 
RECV_DIR=os.path.join(MODULE_DIR,'received')
os.makedirs(RECV_DIR,exist_ok=True)
counter_lock=threading.Lock()
counter=0
#auth helper

def authenticate(conn,client_ip):
    try:
        conn.sendall(b"select:(C)reate account or (L)ogin:")
        choice=conn.recv(1024).decode().strip().upper()#receive and process client choice
        if choice == 'C':#creation
            conn.sendall(b"Username:")
            username=conn.recv(1024).decode().strip()
            conn.sendall(b"Password:")#password
            password=conn.recv(1024).decode().strip()
            user_file=os.path.join(USERS_DIR,f"{username}.json")#path for user file
            with open(user_file,'w',encoding='utf-8') as uf:#save credentials to file
                json.dump({'username':username,'password':password},uf)
            log_event({'type':'user_created','client_ip':client_ip,'username':username})#log account creation
            conn.sendall(b"Account created successfully.\n")#notify client
            return username
        elif choice == 'L':#login
            conn.sendall(b"Username:")
            username=conn.recv(1024).decode().strip()
            user_file=os.path.join(USERS_DIR,f"{username}.json")#path for user file
            if not os.path.isfile(user_file):#check if user exists
                conn.sendall(b"User not found.\n")
                print("user not found")#log
                log_event({'type':'login_failed','client_ip':client_ip,'username':username,'reason':'not_found'})#log fail
                return None#return None on failure
            with open(user_file,'r',encoding='utf-8') as uf:#load user credentials
                creds=json.load(uf)
            conn.sendall(b"Password:")#prompt for password
            password=conn.recv(1024).decode().strip()#receive password
            if password == creds.get('password'):#validate password
                conn.sendall(b"Login successful.\n")
                print("login success")#log
                log_event({'type':'login_success','client_ip':client_ip,'username':username})#log success
                return username
            else:#handle bad password
                conn.sendall(b"Invalid password.\n")#notify client
                print("invalid pass")#log to server console
                log_event({'type':'login_failed','client_ip':client_ip,'username':username,'reason':'bad_password'})
                return None#return None on failure
        else:#handle invalid selection
            conn.sendall(b"Invalid selection.\n")#notify client
            return None#return None on invalid input
    except BrokenPipeError:
        #handle client disconnect
        return None

#json client 
def handle_json_client(conn,addr):
    client_ip=addr[0]#extract client ip address
    #read raw bytes 
    data=b''#init
    try:
        while True:
            chunk=conn.recv(4096)
            if not chunk:
                break
            data += chunk
    except Exception as e:
        log_event({'type':'json_receive_error','client_ip':client_ip,'error':str(e)})#log error
        conn.close()
        return    
    try:
        payload=json.loads(data.decode('utf-8'))#decode bytes and parse json
        #^decode json 
    except Exception as e:#handle invalid json
        log_event({'type':'json_invalid','client_ip':client_ip,'error':str(e)})
        conn.close()
        return    
    username=payload.get('username')#extract username from json    
    if not username:#check if username exists
        log_event({'type':'json_no_username','client_ip':client_ip})
        conn.close()
        return
    #make path user directory 
    user_recv_dir=os.path.join(RECV_DIR,username)#user specific directory path
    os.makedirs(user_recv_dir,exist_ok=True)#directory exists    
    log_event({'type':'json_connection','client_ip':client_ip,'username':username})
    log_event({'type':'json_payload','client_ip':client_ip,'username':username,'keys':list(payload.keys())})
    global counter
    with counter_lock:#synch counter access,assign current counter value,increment
        idx=counter
        counter += 1
    timestamp=datetime.datetime.now().strftime('%Y-%m-%d_%H%M%S')#generate timestamp
    filename=f"{idx:07d}_{timestamp}.json"#unique filename
    path=os.path.join(user_recv_dir,filename)#full path for json
    try:
        with open(path,'w',encoding='utf-8') as f:
            json.dump(payload,f,indent=2)#write json with indentation
        log_event({'type':'json_received','client_ip':client_ip,'username':username,'filename':filename})
    except Exception as e:#error handle
        log_event({'type':'json_save_error','client_ip':client_ip,'username':username,'error':str(e)})
    finally:
        conn.close()#close connection

#json server 
def start_json_server():
    server=socket.socket(socket.AF_INET,socket.SOCK_STREAM)#create a tcp socket
    server.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)#allow reuse of the address
    server.bind((JSON_HOST,JSON_PORT))#bind the server to specified host and port
    server.listen()
    log_event({'type':'json_server_start','host':JSON_HOST,'port':JSON_PORT})
    print(f"[JSON] Listening on {JSON_HOST}:{JSON_PORT}")
    while True:
        conn,addr=server.accept()#accept client connection
        threading.Thread(target=handle_json_client,args=(conn,addr),daemon=True).start()#handle client in a new thread

#module rpc request 
def handle_module_rpc(conn,addr):
    client_ip=addr[0]
    username=authenticate(conn,client_ip)#auth client
    if not username:
        conn.close()
        return
    log_event({'type':'rpc_connection','client_ip':client_ip,'username':username})#log rpc connection
    try:
        raw=conn.recv(1024).decode().strip()#receive and decode client request
        log_event({'type':'rpc_raw_receive','client_ip':client_ip,'username':username,'data':raw})
        cmd,mod=raw.split(maxsplit=1)
        #^split request into command/module name
        log_event({'type':'module_request','client_ip':client_ip,'username':username,'module':mod})#log
        if cmd != 'GET':#eror handle
            conn.sendall(b'ERROR:Unknown command')#send client error
            log_event({'type':'module_response_error','client_ip':client_ip,'username':username,'module':mod,'error':'Unknown command'})
        else:#for good 'GET' command
            path=os.path.join(MODULE_DIR,f"{mod}.py")#construct module file path,thencheck if module exists
            if not os.path.isfile(path):
                conn.sendall(f"ERROR:Module {mod} not found".encode())#send client the error
                log_event({'type':'module_not_found','client_ip':client_ip,'username':username,'module':mod})
            else:#send module source code
                with open(path,'r',encoding='utf-8') as f:#read module file
                    source=f.read()
                conn.sendall(source.encode())#send source code to client
                log_event({'type':'module_sent','client_ip':client_ip,'username':username,'module':mod,'bytes':len(source),'snippet':source[:50]})#log successful send
    except Exception as e:#handle unexpected errors
        err=str(e)#convert error to string
        try:
            conn.sendall(f"ERROR:{err}".encode())#send error to client
        except:
            pass
        log_event({'type':'module_rpc_error','client_ip':client_ip,'username':username,'error':err})#log error
    finally:
        conn.close()#close connection

#module rpc server thread 
def start_module_server():
    server=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
    server.bind((RPC_HOST,RPC_PORT))
    server.listen()
    log_event({'type':'rpc_server_start','host':RPC_HOST,'port':RPC_PORT})
    print(f"[RPC] Listening on {RPC_HOST}:{RPC_PORT}")
    while True:
        conn,addr=server.accept()
        threading.Thread(target=handle_module_rpc,args=(conn,addr),daemon=True).start()

#main
if __name__ == '__main__':
    #start
    threading.Thread(target=start_json_server,daemon=True).start()
    threading.Thread(target=start_module_server,daemon=True).start()
    log_event({'type':'server_running'})
    print("Servers running. Press Ctrl+C to exit.")
    try:
        while True:
            threading.Event().wait(1)
    except KeyboardInterrupt:
        log_event({'type':'server_shutdown'})
        print("Shutting down.")