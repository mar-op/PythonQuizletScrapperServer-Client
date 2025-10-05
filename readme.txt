socket web scraper program, 05-04-25, 

Requirements
---------
Python 3.8 or higher

Python Libraries:
requests_html
colorama
selenium
beautifulsoup4
                   
Standard Libraries Used:
socket, threading, json, os, datetime, importlib, re, time, sys, html, random, collections.deque, urllib.parse   
                
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
