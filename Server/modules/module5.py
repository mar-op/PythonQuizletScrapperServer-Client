import json
import datetime
import socket
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import time

def fetchQuizCards(url, wait=1):#go to flashcard set page
                                #wait 1sec after load for content to render
    opts = Options()
    opts.add_argument("--headless")
    driver = webdriver.Firefox(options=opts)#inits ffox webdriver with options above
    try:
        driver.get(url)#nav ffox webdriver to url
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.SetPageTermsList-term"))
        )#wait up to 15sec for css selector to find a <div> tag containing class="SetPageTermsList-term"
        time.sleep(wait)#pause 1sec to let page load
        soup = BeautifulSoup(driver.page_source, "html.parser")#parse page source with html.parser
        
        cards = []
        #loop through each <div> containing class=SetPageTermsList-term
        for term in soup.select("div.SetPageTermsList-term"):
            sides = term.select('div[data-testid="set-page-term-card-side"] .TermText')
            #^select txt content for each side to put in 'sides' list
            if len(sides) >= 2:#check theres two sides,then [0]=q,[1]=a
                q = sides[0].get_text(strip=True)#extract txt from each side
                a = sides[1].get_text(strip=True)
                cards.append({"question": q, "answer": a})
                #^appen to cards list
        return cards
    finally:
        driver.quit()

def sendJson(data, host, port, RPC_USER):#send JSON to server
    data["username"] = RPC_USER#include sender's username
    payload = json.dumps(data)#format payload
    with socket.create_connection((host, port)) as s:#connect to server
        s.sendall(payload.encode('utf-8'))#send payload
    print(f"{RPC_USER} sent JSON to {host}:{port}")

def main():    
    print(f"Logged in as {RPC_USER}\n")
    dateStr=datetime.datetime.now().strftime("%m-%d-%Y")#define dateStr
    while True:#program cli
        url = input("enter quizlet set url: ").strip()
        print("scraping set...\n")
        try:#call fetchQuizCards def setting user's url as variable 'url'
            cards = fetchQuizCards(url)
            print(f"found {len(cards)} cards\n")#tell user amount of cards found in set
        except Exception as e:#error handling
            print(f"error scraping {url}: {e}\n")
            cards = []
        #prepare payload
        out = {"url": url, "date": dateStr, "cards": cards}#create dict for sendJson        
        #post scrape menu
        while True:
            print("options:")
            print(" 1) save set to server")
            print(" 2) look at scraped set")
            print(" 3) scrape another set")
            print(" 4) exit")
            choice = input("choose (1-4): ").strip()
            if choice == '1':
                #prompt for server info
                host = input("enter JSON server host (default 127.0.0.1): ").strip() or '127.0.0.1'
                portStr = input("enter JSON server port (default 9001): ").strip() or '9001'
                try:
                    port = int(portStr) if portStr else 9001
                except:
                    print("invalid port; using 9001")
                sendJson(out, host, port, RPC_USER)#send JSON to server                
            elif choice=='2':
                if not cards:
                    print("no cards to display.")#handling for no cards
                else:#print cardlist
                    for i, card in enumerate(cards, 1):
                        print(f"card {i}")#for card in cards 0-cards 
                        print("q:", card['question'])
                        print("a:", card['answer'])
                        print()
            elif choice=='3':
                break # restart main loop
            elif choice== '4':
                print("exiting.")
                break
            else:
                print("invalid. enter 1, 2, 3, or 4.")#input handling
            print()
        if choice=="4":
            break

if __name__=='__main__':
    main()