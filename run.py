from asyncio.subprocess import PIPE
from logging import exception
import subprocess
from os import mkdir, remove
from time import sleep
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.edge.options import Options as EdgeOptions
from datetime import datetime
from datetime import timedelta
from pathlib import Path
from json import dump, load
import sys
import getopt
from win10toast import ToastNotifier
import logging

run_options = ChromeOptions()
userdirectory = Path.home()
url = "http://www.google.com"
urlalt = "http://www.cloudflareportal.com/test"
browser = 0
notifier = ToastNotifier()
icon_path = f"{userdirectory}\\Code\\auto-login\\padlock.ico"

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
c_handler = logging.StreamHandler()
f_handler = logging.FileHandler(f"{userdirectory}\\Code\\auto-login\\logfile.txt")

c_format = logging.Formatter('%(asctime)s :: %(levelname)s :: %(message)s')
f_format = logging.Formatter('%(asctime)s :: %(name)s :: %(levelname)s %(process)d :: %(message)s')
c_handler.setFormatter(c_format)
f_handler.setFormatter(f_format)



def driverSetup():
    global browser
    global logtext
    global run_options
    try:
        with open(f"{str(userdirectory)}\\AppData\\Roaming\\SOPHOS_auto_login\\log.dat",'r') as f:
            userData = load(f)
        if userData['browser'] == "chrome":
            browser = 0
            run_options = ChromeOptions()
            run_options.add_argument("--headless")
            logger.debug("Added runtime argument 'headless' for Chrome webdriver")
            run_options.add_argument("--window-size=1920,1080")
            logger.debug("Added runtime argument 'window-size' for Chrome webdriver")
        elif userData['browser'] == 'edge':
            browser = 1
            run_options = EdgeOptions()
            run_options.add_argument("--headless")
            logger.debug("Added runtime argument 'headless' for Edge webdriver")
            run_options.add_argument("--window-size=1920,1080")
            logger.debug("Added runtime argument 'window-size' for Edge webdriver")
        elif userData['browser'] == 'firefox':
            browser = 2
            run_options = FirefoxOptions()
            run_options.add_argument("--headless")
            logger.debug("Added runtime argument 'headless' for Firefox webdriver")
            run_options.add_argument("--window-size=1920,1080")
            logger.debug("Added runtime argument 'window-size' for Firefox webdriver")
            
    except Exception:
        setup()

            
def setup():
    uid = input("Enter Username : ")
    passwd = input("Enter Password : ")
    time = datetime.time(datetime.now())
    browser = input("Choose a browser [Chrome/Edge/Firefox]").lower()
    userData = {"uid":uid,"passwd":passwd,"time":timedelta(hours=time.hour, minutes=time.minute),"browser":browser}
    try:
        with open(f"{str(userdirectory)}\\AppData\\Roaming\\SOPHOS_auto_login\\log.dat",'w') as f:
            dump(userData,f,default=str)
    except FileNotFoundError:
        logger.info("Config file parent folder does not exist.")
        mkdir(f"{str(userdirectory)}\\AppData\\Roaming\\SOPHOS_auto_login\\")
        with open(f"{str(userdirectory)}\\AppData\\Roaming\\SOPHOS_auto_login\\log.dat",'w') as f:
            dump(userData,f,default=str)
    return userData
    
def ping(repeat):
    global log_level
    global logtext
    if repeat == 3:
        return 1
    logger.debug("Attempting to ping 'www.google.com'")
    pingProcess = subprocess.run(['ping','www.google.com',],stdout=PIPE)
    re = pingProcess.stdout.decode('utf-8')
    if("Sent" not in re):
        logger.warning("Server address could not be resolved.")
        return 1
    sent = re[re.find("Sent")+7]
    received = re[re.find("Received")+11]
    if(received<sent):
        return ping(repeat+1)
    elif(received == 0):
        return 1
    else:
        logger.debug("Ping successful. Login not required.")
        return 0
    

def WarpDisconnect():
    global log_level
    global logtext
    checkerprocess = subprocess.run(['warp-cli','status'], stdout=PIPE)
    if("Connected" in checkerprocess.stdout.decode("utf-8")):
        logger.debug("Disconnecting from CloudFlare Warp")
        process = subprocess.run(['warp-cli','disconnect'],stdout=PIPE)
        if("Success" in process.stdout.decode('utf-8')):
            logger.debug("Disconnected from CloudFlare Warp")
            try:
                notifier.show_toast("Auto Login","Disconnected from Warp",icon_path=icon_path,duration=5)
            except Exception as e:
                logger.exception("Exception occured")
            return 0
        else:
            logger.warning("Could not disconnect from Warp.")
            return 1
    else:
        return 0

def WarpReconnect():
    global log_level
    global logtext
    n = 5
    retry = 1
    checkerprocess = subprocess.run(['warp-cli','status'],stdout=PIPE)
    if("Connected" in checkerprocess.stdout.decode('utf-8')):
        logger.debug("Warp is already connected.")
        status = 1
    else:
        logger.debug("Attempting to establish connection to CouldFlare servers.")
        status = 0
    
    while status == 0:
        if(retry == 5):
            logger.warning("Retry 5/5 failed. Unable to establish connection to CloudFlare servers.")
            return 1
        process = subprocess.run(['warp-cli','connect'],stdout=PIPE)
        sleep(n)
        if("Success" not in process.stdout.decode('utf-8')):
            if log_level == 1:print(process.stdout.decode('utf-8'))
            else: pass
        checkerprocess = subprocess.run(['warp-cli','status'],stdout=PIPE)
        if("Connected" in checkerprocess.stdout.decode('utf-8')):
            status = 1
            logger.debug("Connection established")
            try:
                notifier.show_toast("Auto Login","Disconnected from Warp",icon_path=icon_path,duration=5, threaded=True)
            except TypeError as e:
                logger.exception("Exception occured")
        else:
            status = 0
            logger.info(f"Connection timed out. Retrying {retry}/5")
            retry += 1
            n += 2
    return 0

def main(argv):
    global logtext
    global logfile
    global log_level
    log_level = 0
    
    opts,args = getopt.getopt(argv,"hsrdl:",["show-credentials","reconfigure-credentials","delete_credentials","log-level="])
    c_handler.setLevel(logging.WARNING)
    f_handler.setLevel(logging.WARNING)
    
    opts = [("-l",'d')]
    
    for opt,arg in opts:
        if(opt == "-h"):
            print(help)
        elif(opt in ("-l","--log-level")):
            if arg.lower() in ("info","i"):
                c_handler.setLevel(logging.INFO)
                f_handler.setLevel(logging.INFO)
            elif arg.lower() in ("debug","d"):
                c_handler.setLevel(logging.DEBUG)
                f_handler.setLevel(logging.DEBUG)
        elif(opt in ("-s","--show-credentails")):
            try:
                with open(f"{str(userdirectory)}\\AppData\\Roaming\\SOPHOS_auto_login\\log.dat",'r') as f:
                    userData = load(f)
                print(f"Username : {userData['uid']}\nPassword : {userData['passwd']}\nBrowser : {userData['browser']}")
                return 0
            except Exception:
                logger.warning("Config file not found!")
                print("Credentials not configured.")
                try:
                    choice = input("Configure now?[Y/N]").lower()
                    if choice == 'y':
                        setup()
                        return 0
                    else:
                        return 0
                except Exception as e:
                    print(e.message)
                    return 1
        elif(opt in ("-r","--reconfigure-credentials")):
            setup()
            return 0
        elif(opt in ('-d','--delete-credentials')):
            remove(f"{str(userdirectory)}\\AppData\\Roaming\\SOPHOS_auto_login\\log.dat")
            return 
    
    logger.addHandler(c_handler)
    logger.addHandler(f_handler)
    driverSetup()
    while True:
        logfile = open(f"{userdirectory}\\Code\\auto-login\\logfile.txt","a")
        try:
            logger.debug("Loading user data")
            with open(f"{str(userdirectory)}\\AppData\\Roaming\\SOPHOS_auto_login\\log.dat",'r') as f:
                userData = load(f)
            logger.debug("Loaded user data")
        except Exception as e:
            userData = setup()
        try:            
            WarpDisconnect()
            doLogin = True if ping(1) == 1 else False
            if doLogin is True:
                logger.debug("Initiating Login\nSetting runtime options for webdriver")
                if browser == 0:
                    driver = webdriver.Chrome(options=run_options)
                elif browser == 1:
                    driver = webdriver.Edge(options=run_options)
                elif browser == 2:
                    driver = webdriver.Firefox(service=FirefoxService(executable_path="C:\\Program Files (x86)\\Browser_Drivers\\geckodriver.exe"),firefox_binary="C:\\Program Files\\Mozilla Firefox\\firefox.exe",options=run_options)
                else:
                    return 1
                logger.debug("Finished setting runtime options for webdriver.\nConnecting to http://172.16.0.30:8090/httpclient.html")
                driver.get('http://172.16.0.30:8090/httpclient.html')
                uname = driver.find_element(By.ID, 'username')
                passwd = driver.find_element(By.ID, 'password')
                loginbutton = driver.find_element(By.ID, 'loginbutton')
                uname.send_keys('f20212382')
                logger.debug("Populated username field")
                passwd.send_keys('fd$21130617')
                logger.debug("Populated password field")
                loginbutton.click()
                logger.debug("Clicked 'Sign In' button")
                if(loginbutton.text == "Sign out"):
                    logger.debug("Login successful")
                    try:
                        notifier.show_toast("Auto Login","Disconnected from Warp",icon_path=icon_path,duration=5)
                    except Exception as e:
                        logger.exception("Exception occured")
                else:
                    logger.fatal("Login failed!")
                    try:
                        notifier.show_toast("Auto Login","Disconnected from Warp",icon_path=icon_path,duration=5)
                    except Exception as e:
                        logger.exception("Exception occured")
                    driver.close()
                    return 1
                logger.debug("Retrieving current date and time")
                time = datetime.time(datetime.now())
                logger.debug("Updating current time into last login time in user data")
                userData["time"] = timedelta(hours=time.hour, minutes=time.minute)
                logger.debug("Writing user data into file")
                with open(f"{str(userdirectory)}\\AppData\\Roaming\\SOPHOS_auto_login\\log.dat",'w') as f:
                    dump(userData,f,default=str)
                    
                try:
                    logger.debug("Terminating browser instance")
                    driver.close()
                    driver.close()
                    logger.debug("Browser instance terminated")
                except Exception:
                    logger.warning("Could not terminate browser instance")
                    pass
                WarpReconnect()
                logger.info("\nPausing execution for 43200 seconds\n")
                sleep(43200)
                
            else:
                WarpReconnect()
                time = datetime.strptime(userData["time"],"%H:%M:%S")
                currentTime = datetime.time(datetime.now())
                lastLoginDelta = timedelta(hours=time.hour, minutes=time.minute)
                currentTimeDelta = timedelta(hours=currentTime.hour, minutes=currentTime.minute)
                realTimeDifference = lastLoginDelta - currentTimeDelta
                timeDifference = realTimeDifference - timedelta(hours=0,minutes=1)
                
                if timeDifference.total_seconds()<0:
                    logger.info("\nPausing execution for 43200 seconds\n")
                    sleep(43200)
                else:
                    logger.info(f"\nPausing execution for {timeDifference.total_seconds()} seconds\n")
                    sleep(timeDifference.total_seconds())
                continue
            
        except FileNotFoundError as e:
            mkdir(f"{str(userdirectory)}\\AppData\\Roaming\\SOPHOS_auto_login")
            continue

if __name__ == "__main__":
    command_line_args = sys.argv[1: ]
    if main(command_line_args) == 1:
        logger.fatal("\nProcess failed. Possible reasons could be, invalid credentials, <browser_driver>.exe is not in PATH, warp-cli.exe is not in PATH, selenium module is not installed, webdriver_manager module is not installed\n")
    