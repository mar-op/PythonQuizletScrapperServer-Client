import sys
import socket
import importlib.abc
import importlib.machinery
from requests_html import HTMLSession
from random import randint
import html
import re
from colorama import Fore, init
init()
####################################################################################
#configure rpc conncection and log in 
print("Configure RPC connection:")
RPC_HOST=input("RPC host (default 127.0.0.1): ").strip() #or '127.0.0.1'#localhost if no input

port_input=input("RPC port (default 9002): ").strip()
try:
    RPC_PORT=int(port_input) if port_input else 9002
    #if u
except ValueError:
    print("Invalid port, using default 9002")
    RPC_PORT=9002
#while loop for c or l prompt
while True:
    RPC_AUTH=input("(C)reate or (L)ogin: ").strip().lower()
    if RPC_AUTH in ('c','l'):
        break
    print("please enter 'C' to create an account or 'L' to log in")
RPC_USER=input("username: ").strip()
RPC_PASS=input("password: ").strip()

#####################################################################################

#init remote_modules4&5 so can call from server later
REMOTE_MODULES={'module4','module5'}
class RemoteLoader(importlib.abc.Loader):
    def __init__(self, name, addr):
        self.name=name
        self.addr=addr
    def exec_module(self, module):
        #connect to RPC,do auth handshake        
        with socket.create_connection(self.addr) as s:            
            _=s.recv(1024)#receive "select: (C)reate account or (L)ogin:"
            s.sendall(f"{RPC_AUTH}\n".encode('utf-8'))#answer w rpc_auth            
            _=s.recv(1024)#receive "Username: " prompt
            s.sendall(f"{RPC_USER}\n".encode('utf-8'))#answer w rpc_user
            _=s.recv(1024)#receive "Password: " prompt
            s.sendall(f"{RPC_PASS}\n".encode('utf-8'))#answer w rpc_pass
            result=s.recv(1024).decode('utf-8')#receive auth result
            if not (result.lower().startswith('login successful') or result.lower().startswith('account created')):
                #^checkif authresult either logged in or account creation
                raise ImportError(f"Authentication failed: {result.strip()}")#error handling
            #now request module source
            s.sendall(f"GET {self.name}\n".encode('utf-8'))
            source_bytes = b''#init empty bytes object to store module source
            while True:
                chunk = s.recv(4096)
                if not chunk: #break loop if no more data received
                    break
                source_bytes += chunk#append received chunk to source bytes        
        source = source_bytes.decode('utf-8')#decode into utf8
        if source.startswith('ERROR:'):
            raise ImportError(source)#if server return eror
        code = compile(source, f"<remote {self.name}>", 'exec')#compile source code into object
        module.__dict__['RPC_USER'] = RPC_USER#inject rpc_user into modules namespace so you can save json as a name you remember
        exec(code, module.__dict__)

####################################################################################


#remote finder
class RemoteFinder(importlib.abc.MetaPathFinder):
    def __init__(self, addr, modules):#init w server address&modules to fetch remotely
        self.addr = addr
        self.modules = modules        
    def find_spec(self, fullname, path, target=None):
    #locate module spec if its in remote modules set
        if fullname in self.modules:
            return importlib.machinery.ModuleSpec(
                fullname,#modulename
                RemoteLoader(fullname, self.addr),#fetch module 
                origin='remote'#specify remotee source
            )
        return None

#install finder
sys.meta_path.insert(0, RemoteFinder((RPC_HOST, RPC_PORT), REMOTE_MODULES))
#needed to import my modules here and not at the top since they are being served from my server
import module4
import module5


def gato():  #random ascii cat def that i made last month (where i got the idea from to apply this to quizlet)
    session=HTMLSession()
    resp=session.get("https://www.asciiart.eu/animals/cats")
    cats=resp.html.find('pre[class=""]')
    idx=randint(0,len(cats)-1)
    art=re.sub(r'</?pre[^>]*>','',html.unescape(cats[idx].html))
    print(art.replace('\r\n','\n').replace('\r','\n'))

def gatolist():  #accii cat  list. wanted to do something where user 
                    #could choose specific ascii to always have open 
                    #on start up but didnt have time.
    session = HTMLSession()
    resp=session.get("https://www.asciiart.eu/animals/cats")
    cats=resp.html.find('pre[class=""]')
    gatoQ=input(f"print {len(cats)} cats? y/n\n")
    if gatoQ=='y':
        for idx,cat in enumerate(cats):
            art=re.sub(r'</?pre[^>]*>', '', html.unescape(cats[idx].html))
            print(art.replace('\r\n', '\n').replace('\r','\n'))


def readMe():print("""
socket web scraper program

Overview
---------
client/server socket system written in python
The server provides two services:
- a JSON server that receives and saves web scraping results.
- a RPC server that authenticates users and serves Python modules remotely.

The client connects, authenticates, remotely imports modules, and provides users with scraping tools:
- module 5: scrapes quizlet flashcard sets (more complete)
- module 4: scrapes a webpage or a domain for emails, phone numbers, usernames, media files, and links.

How to Run
---------
1. Start the Server:
   - Run server.py.
   - This starts:
     - JSON server on port 9001
     - RPC server on port 9002
2. Run the Client:
   - Run perfclient.py.
   - You will be prompted to:
     - Enter RPC host (default: 127.0.0.1)
     - Enter RPC port (default: 9002)
     - Choose to Create or Login to an account.
     - Enter a username and password.
3. Use the Client Menu:
   After login, the menu options are:
     0) Exit
     1) Quizlet scraper (module5)
     2) URL scraper (module4)
     3) View multiple ASCII cats

Example Usage
---------
Starting Server:
> python server.py
Starting Client:
> python perfclient.py

Example Interaction:
Configure RPC connection: 
RPC host (default 127.0.0.1):192.168.X.X
RPC port (default 9002):9002
(C)reate or (L)ogin: c
username: user1
password: pass123

[ASCII cat prints]

Logged in as user1

options:
 0) exit
 1) quizlet scraper
 2) url scraper
 3) catslol
Select: 1
enter quizlet set url: https://quizlet.com/123456789/example-set

(Then scrape the Quizlet set, save results, or explore more options.)

group statement
---------
NOTE: the username functionality is only made to keep track of saved json content.
      in server when a user saves a scrape, it will go to modules/recieved/username/file.json
      there is no other functionality to the users other than keeping track of what saved content is where
      i was going to add more functionality to the users but was tired and no time left on 4 more minutes to turn in
""")

####################################################################################


#main menu     
def menu():
    while True:
        print(Fore.CYAN)
        gato()#random cat generator
        print(f"logged in as {RPC_USER}\n")
        print("\noptions:\n 0) exit\n 1) quizlet scraper\n 2) url scraper/crawler\n 3) catslol\n 4) READ ME")
        choice=input("Select: ").strip()
        if choice=='1':
            print(Fore.GREEN)
            module5.main()
        elif choice=='2':
            print(Fore.MAGENTA)
            module4.main()
        elif choice=='0':
            print("exiting")
            sys.exit(0)
        elif choice=='3':
            gatolist()   
        elif choice=='4':
            readMe()         
        else:
            print("invalid input, choose 0, 1, 2, 3, or 4.")

if __name__=='__main__':
    menu()
