import sys
import socket
import re
import time
import datetime
import json
from urllib.parse import urlparse, urljoin
from collections import deque
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import WebDriverWait
#from selenium.webdriver.support import expected_conditions as EC
#from selenium.webdriver.common.by import By

#patterns to search for
EMAIL_PATTERN=re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PHONE_PATTERN=re.compile(r"(?:\+?1[-.\s]?)?(?:\(\d{3}\)|\d{3})[-.\s]?\d{3}[-.\s]?\d{4}")
USERNAME_PATTERN=re.compile(r"@[A-Za-z0-9_]{3,30}")
MEDIA_PATTERN=re.compile(r"\.(js|png|jpg|aspx|gif|bmp|jpeg|html|asp|php|bak|txt|mp3|wav|mp4)(?:[\?#].*)?$", re.IGNORECASE)

#fetch and render page
def fetchPage(url, timeout=30, wait=2, headless=True):
    opts = Options()#run ffox in headless cli
    if headless:
        opts.add_argument("--headless")
    driver = webdriver.Firefox(options=opts)#apply opts
    try:
        driver.get(url)
        WebDriverWait(driver, timeout).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
        time.sleep(wait)
        return driver.page_source
    finally:
        driver.quit()

#extreact strings based on patterns configured earlier
def scanUrls(html):
    emails=set(EMAIL_PATTERN.findall(html))
    phones=set(PHONE_PATTERN.findall(html))
    users=set(USERNAME_PATTERN.findall(html))
    soup=BeautifulSoup(html, 'html.parser')
    raw_links={a['href'] for a in soup.find_all('a', href=True)}
    media={l for l in raw_links if MEDIA_PATTERN.search(l)}
    links=raw_links -media
    return {'emails':emails,'phones':phones,'usernames':users,'links':links,'media':media}

def sendJson(data, host, port, RPC_USER):#send JSON to server
    data["username"] = RPC_USER  # include sender's username
    payload = json.dumps(data)#format payload
    with socket.create_connection((host, port)) as s:#connect to server
        s.sendall(payload.encode('utf-8'))#send payload
    print(f"{RPC_USER} sent JSON to {host}:{port}")

#start crawl
def crawl(start_url, max_pages=20, link_timeout=5):
    root=urlparse(start_url).netloc
    queue= deque([start_url])
    visited=set()
    aggregated={'emails': set(), 'phones': set(), 'usernames': set(), 'links': set(), 'media': set()}
    host=input("enter JSON server host (default 127.0.0.1): ").strip() or '127.0.0.1'
    portStr=input("enter JSON server port (default 9001): ").strip() or '9001'
    count=0
    while queue and count < max_pages:
        url = queue.popleft().strip()
        if url in visited:
            continue
        visited.add(url)
        count += 1
        print(f"[{count}/{max_pages}] Crawling: {url}")
        try:
            html = fetchPage(url, timeout=link_timeout)
            data = scanUrls(html)
            for k in aggregated:
                aggregated[k].update(data.get(k, []))
        except Exception as e:
            data = {'emails': set(), 'phones': set(), 'usernames': set(), 'links': set(), 'media': set(), 'error': str(e)}

        #prepare JSON payload
        date_str = datetime.datetime.now().strftime("%m-%d-%Y")
        out = {
            'url': url,
            'date': date_str,
            'emails': sorted(aggregated['emails']),
            'phones': sorted(aggregated['phones']),
            'usernames': sorted(aggregated['usernames']),
            'links': sorted(aggregated['links']),
            'media': sorted(aggregated['media'])
        }
        #send to server
        
        try:
            port = int(portStr)
        except:
            print("invalid port; using 9001")
            port = 9001
        sendJson(out, host, port, RPC_USER)

        # enqueue same-domain links
        for link in data.get('links', []):
            full = urljoin(url, link)
            if urlparse(full).netloc == root and full not in visited:
                queue.append(full)

    print(f"Crawl complete: {count} pages processed.")
    return aggregated

#main loop
def main():
    print(f"Logged in as {RPC_USER}\n")
    while True:
        url = input("Enter URL to fetch: ").strip()
        date_str = datetime.datetime.now().strftime("%m-%d-%Y")
        print("\n-- Initial Scan --")
        try:
            html    = fetchPage(url)
            initial = scanUrls(html)
        except Exception as e:
            print(f"Initial fetch error: {e}\n")
            initial = {k: set() for k in ['emails','phones','usernames','links','media']}

        # display counts
        print(f"Found emails: {len(initial['emails'])}, phones: {len(initial['phones'])},")
        print(f"usernames: {len(initial['usernames'])}, links: {len(initial['links'])}, media: {len(initial['media'])}\n")
        saveQ = input("save to server? (y/n): ").strip().lower()
        if saveQ in ('y', 'yes'):
            out = {
                'url': url,
                'date': date_str,
                'emails': sorted(initial['emails']),
                'phones': sorted(initial['phones']),
                'usernames': sorted(initial['usernames']),
                'links': sorted(initial['links']),
                'media': sorted(initial['media'])
            }
            host = input("enter JSON server host (default 127.0.0.1): ").strip() or '127.0.0.1'
            portStr = input("enter JSON server port (default 9001): ").strip() or '9001'
            try:
                port = int(portStr)
            except:
                print("invalid port; using 9001")
                port = 9001
            sendJson(out, host, port, RPC_USER)#send JSON to server                

        # inspection menu
        while True:
            print("inspect initial scan:")
            print(" 1) emails")
            print(" 2) phones")
            print(" 3) usernames")
            print(" 4) links")
            print(" 5) media files")
            print(" 6) continue to crawl")
            print(" 7) exit")
            choice = input("choose (1-7): ").strip()
            if choice == '1':#1-7 list what the user says list or continuyes to crawl or exit
                print(*sorted(initial['emails']), sep='\n')
            elif choice == '2':
                print(*sorted(initial['phones']), sep='\n')
            elif choice == '3':
                print(*sorted(initial['usernames']), sep='\n')
            elif choice == '4':
                print(*sorted(initial['links']), sep='\n')
            elif choice == '5':
                print(*sorted(initial['media']), sep='\n')
            elif choice == '6':
                break
            elif choice == '7':
                break
            else:
                print("invalid choice.")
            print()
        # ask to crawl
        if input("Crawl linked pages? (y/n): ").lower() == 'y':
            try:
                pages = int(input("Pages to crawl (5-100, default 20): ").strip() or 20)
            except:
                pages = 20
            pages = max(5, min(100, pages))
            aggregated = crawl(url, max_pages=pages, link_timeout=5)
            # show totals
            totals = {k: len(initial[k] | aggregated[k]) for k in aggregated}
            print(f"\nTotals after crawl: emails {totals['emails']}, phones {totals['phones']},")
            print(f"usernames {totals['usernames']}, links {totals['links']}, media {totals['media']}\n")
        else:
            print("Crawl skipped.\n")
        # rerun or exit
        if input("Run again? (y/n): ").lower() != 'y':
            break
    print("Exiting.")
#main
if __name__ == '__main__':
    main()