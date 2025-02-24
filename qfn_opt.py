import os
import time
import subprocess
from plyer import notification
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

qlservers = [
    "https://qlstats.net/server/4545",
    "https://qlstats.net/server/6527"
]

knownplayers = {url: set() for url in qlservers}

# store last clearfreq time
lastclear = time.time()

# time to clear knownplayers (default 20min)
clearfreq = 1200

def init_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    driver = webdriver.Chrome(options=chrome_options)
    return driver

# auto accept cookies per session
def accept_cookies(driver, url):    
    driver.get(url)
    try:
        cookie_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Agree')]")
        cookie_button.click()
        print(f"[{time.strftime('%H:%M:%S')}] Accepted cookies for {url}")
    except:
        print(f"[{time.strftime('%H:%M:%S')}] No cookie popup for {url}")

# extract player name and rating from html element
def playercheck(driver, url):
    driver.get(url)
    try:
        player_data = []
        rows = driver.find_elements(By.XPATH, "//table[@id='livePlayers']//tbody//tr")
        for row in rows:
            columns = row.find_elements(By.TAG_NAME, "td")
            if len(columns) >= 3:
                nickname = columns[1].text.strip()
                glicko = columns[2].text.strip()
                if nickname and glicko:
                    player_data.append((nickname, glicko))
        return set(player_data)
    except:
        return set()


def notify(server_name, all_players):
    timestamp = time.strftime("%H:%M:%S")
    players_list = "\n".join([f"{nick} (Glicko: {glicko})" for nick, glicko in all_players])
    message = f"{timestamp}\n\nCurrent players:\n{players_list}"

    # probe os
    if os.name == 'nt':  # = windows
        notification.notify(
            title=f"Players on {server_name}",
            message=message,
            timeout=5
        )
        print(f"\n[{timestamp}] Notification sent - {server_name} \n{message}\n")

    elif os.name == 'posix':  # = linux        
        subprocess.run(["notify-send", f"Players on {server_name}", message])                
        # play notification sound (define path to sound file):
        
        # sound_path = "/path/to/your/sound"
        # subprocess.run(["paplay", sound_path])
        
        print(f"\n[{timestamp}] Notification sent - {server_name} \n{message}\n")


# function that clears known players
def clearplayers():
    global lastclear, knownplayers


    if time.time() - lastclear > clearfreq:
        print(f"[{time.strftime('%H:%M:%S')}] Clearing known players list...")    
        knownplayers = {url: set() for url in qlservers}
        lastclear = time.time()  # update lastclear as referenced in line 16


# webdriver persistence
driver = init_driver()

try:
    # handle cookies
    for url in qlservers:
        accept_cookies(driver, url)

    while True:
        clearplayers()

        for index, url in enumerate(qlservers):
            server_name = "Quake For Newbies | EU 1100 Max" if index == 0 else "Quake For Newbies | EU 1100 Max #2"
            current_players = playercheck(driver, url)

            if current_players > knownplayers[url]:
                notify(server_name, current_players)
                knownplayers[url] = current_players
            else:
                print(f"[{time.strftime('%H:%M:%S')}] No new players on {server_name}")

        print(f"[{time.strftime('%H:%M:%S')}] Waiting for the next cycle...")
        time.sleep(30)

finally:
    driver.quit()  # quit headless chrome session on exit
