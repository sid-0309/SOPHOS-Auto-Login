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
from keyboard import is_pressed
import sys
import getopt
from win10toast import ToastNotifier
log_level = 0
run_options = ChromeOptions()
userdirectory = Path.home()
url = "http://www.google.com"
urlalt = "http://www.cloudflareportal.com/test"
browser = 0
notifier = ToastNotifier()
icon_path = f"{userdirectory}\\Code\\auto-login\\padlock.ico"
logfile = open(f"{userdirectory}\\Code\\auto-login\\logfile.txt","a")
logtext = ""

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
            if log_level == 1:
                print("Added runtime argument 'headless' for Chrome webdriver")
                logtext += "Added runtime argument 'headless' for Chrome webdriver"
            run_options.add_argument("--window-size=1920,1080")
            if log_level == 1:
                print("Added runtime argument 'window-size' for Chrome webdriver")
                logtext += "Added runtime argument 'window-size' for Chrome webdriver"
        elif userData['browser'] == 'edge':
            browser = 1
            run_options = EdgeOptions()
            run_options.add_argument("--headless")
            if log_level == 1:
                print("Added runtime argument 'headless' for Edge webdriver")
                logtext += "Added runtime argument 'headless' for Edge webdriver"
            run_options.add_argument("--window-size=1920,1080")
            if log_level == 1:
                print("Added runtime argument 'window-size' for Edge webdriver")
                logtext += "Added runtime argument 'window-size' for Edge webdriver"
        elif userData['browser'] == 'firefox':
            browser = 2
            run_options = FirefoxOptions()
            run_options.add_argument("--headless")
            if log_level == 1:print("Added runtime argument 'headless' for Firefox webdriver")
            logtext += "Added runtime argument 'headless' for Firefox webdriver"
            run_options.add_argument("--window-size=1920,1080")
            if log_level == 1:print("Added runtime argument 'window-size' for Firefox webdriver")
            logtext += "Added runtime argument 'window-size' for Firefox webdriver"
            
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
        mkdir(f"{str(userdirectory)}\\AppData\\Roaming\\SOPHOS_auto_login\\")
        with open(f"{str(userdirectory)}\\AppData\\Roaming\\SOPHOS_auto_login\\log.dat",'w') as f:
            dump(userData,f,default=str)
    return userData
    
def ping(repeat):
    global log_level
    global logtext
    if repeat == 3:
        return 1
    if log_level == 1:
        print("Attempting to ping 'www.google.com'")
        logtext += "Attempting to ping 'www.google.com'"
    pingProcess = subprocess.run(['ping','www.google.com',],stdout=PIPE)
    re = pingProcess.stdout.decode('utf-8')
    if("Sent" not in re):
        if log_level == 1:
            print("Server address could not be resolved.")
            logtext += "Server address could not be resolved."
        return 1
    sent = re[re.find("Sent")+7]
    received = re[re.find("Received")+11]
    if(received<sent):
        return ping(repeat+1)
    elif(received == 0):
        return 1
    else:
        
        if log_level == 1:
            print("Ping successful. Login not required.")
            logtext+="Ping successful. Login not required."
        else: pass
        return 0
    

def WarpDisconnect():
    global log_level
    global logtext
    checkerprocess = subprocess.run(['warp-cli','status'], stdout=PIPE)
    if("Connected" in checkerprocess.stdout.decode("utf-8")):
        if log_level == 1:
            print("Disconnecting from CloudFlare Warp")
            logtext += "Disconnecting from CloudFlare Warp"
        else:pass
        process = subprocess.run(['warp-cli','disconnect'],stdout=PIPE)
        if("Success" in process.stdout.decode('utf-8')):
            if log_level == 1:
                print("Disconnected")
                logtext += "Disconnected"
            else: pass
            notifier.show_toast("Auto Login","Disconnected from Warp",icon_path=icon_path,duration=5)
            return 0
        else:
            if log_level == 1:
                print("Could not disconnect from Warp.")
                logtext += "Could not disconnect from Warp."
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
        if log_level == 1:print("Warp is already connected.")
        logtext += "Warp is already connected."
        status = 1
    else:
        if log_level == 1:
            print("Attempting to establish connection to CouldFlare servers.")
            logtext += "Attempting to establish connection to CouldFlare servers."
        status = 0
    
    while status == 0:
        if(retry == 5):
            if log_level == 1:
                print("Retry 5/5 failed. Unable to establish connection to CloudFlare servers.")
                logtext += "Retry 5/5 failed. Unable to establish connection to CloudFlare servers."
            else :pass
            return 1
        process = subprocess.run(['warp-cli','connect'],stdout=PIPE)
        sleep(n)
        if("Success" not in process.stdout.decode('utf-8')):
            if log_level == 1:print(process.stdout.decode('utf-8'))
            else: pass
        checkerprocess = subprocess.run(['warp-cli','status'],stdout=PIPE)
        if("Connected" in checkerprocess.stdout.decode('utf-8')):
            status = 1
            if log_level == 1:
                print("Connection established")
            notifier.show_toast("Auto Login","Connected to Warp",icon_path=icon_path,duration=5)
        else:
            status = 0
            if log_level == 1:
                print(f"Connection timed out. Retrying {retry}/5")
                logtext += f"Connection timed out. Retrying {retry}/5"
            else : pass
            retry += 1
            n += 2
    return 0

def main(argv):
    global logtext
    global logfile
    global log_level
    log_level = 0
    
    opts,args = getopt.getopt(argv,"hsrdl:",["show-credentials","reconfigure-credentials","delete_credentials","log-level="])
    
    
    for opt,arg in opts:
        if(opt == "-h"):
            print(help)
        elif(opt in ("-l","--log-level")):
            if arg.lower() in ("verbose","v"):
                log_level = 1
            else: log_level = 0
        elif(opt in ("-s","--show-credentails")):
            try:
                with open(f"{str(userdirectory)}\\AppData\\Roaming\\SOPHOS_auto_login\\log.dat",'r') as f:
                    userData = load(f)
                print(f"Username : {userData['uid']}\nPassword : {userData['passwd']}\nBrowser : {userData['browser']}")
                return 0
            except Exception:
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
            return 0
    driverSetup()
    while True:
        try:
            if log_level == 1:
                print("Loading user data.")
                logtext += "Loading user data."
            else: pass
            with open(f"{str(userdirectory)}\\AppData\\Roaming\\SOPHOS_auto_login\\log.dat",'r') as f:
                userData = load(f)
            if log_level == 1:
                print("Success")
                logtext += "Success"
        except Exception as e:
            userData = setup()
        try:            
            WarpDisconnect()
            doLogin = True if ping(1) == 1 else False
            if doLogin is True:
                if log_level == 1:
                    print("Initiating Login\nSetting runtime options for webdriver.")
                    logtext += "Initiating Login\nSetting runtime options for webdriver."
                else: pass
                if browser == 0:
                    driver = webdriver.Chrome(options=run_options)
                elif browser == 1:
                    driver = webdriver.Edge(options=run_options)
                elif browser == 2:
                    driver = webdriver.Firefox(service=FirefoxService(executable_path="C:\\Program Files (x86)\\Browser_Drivers\\geckodriver.exe"),firefox_binary="C:\\Program Files\\Mozilla Firefox\\firefox.exe",options=run_options)
                else:
                    return 1
                if log_level == 1:
                    print("Finished setting runtime options for webdriver.\nConnecting to http://172.16.0.30:8090/httpclient.html")
                    logtext += "Finished setting runtime options for webdriver.\nConnecting to http://172.16.0.30:8090/httpclient.html"
                driver.get('http://172.16.0.30:8090/httpclient.html')
                uname = driver.find_element(By.ID, 'username')
                passwd = driver.find_element(By.ID, 'password')
                loginbutton = driver.find_element(By.ID, 'loginbutton')
                uname.send_keys('f20212382')
                if log_level == 1:
                    print("Populated username field.")
                    logtext += "Populated username field."
                passwd.send_keys('fd$21130617')
                if log_level == 1:print("Populated password field.")
                logtext += "Populated password field."
                loginbutton.click()
                if log_level == 1:
                    print("Clicked 'Sign In' button.")
                    logtext += "Clicked 'Sign In' button."
                if(loginbutton.text == "Sign out"):
                    if log_level == 1:
                        print("Login successful")
                        logtext += "Login successful"
                    else: pass
                    notifier.show_toast("Auto Login","Login Successful",icon_path=icon_path,duration=5)
                else:
                    if log_level == 1:
                        print("Login failed")
                        logtext += "Login failed"
                    else:pass
                    notifier.show_toast("Auto Login","Login Failed",icon_path=icon_path,duration=5)
                    driver.close()
                    return 1
                if log_level == 1:
                    print("Retrieving current date and time.")
                    logtext += "Retrieving current date and time."
                time = datetime.time(datetime.now())
                if log_level == 1:
                    print("Updating current time into last login time in user data.")
                    logtext += "Updating current time into last login time in user data."
                userData["time"] = timedelta(hours=time.hour, minutes=time.minute)
                if log_level == 1:
                    print("Writing user data into file.")
                    logtext += "Writing user data into file."
                with open(f"{str(userdirectory)}\\AppData\\Roaming\\SOPHOS_auto_login\\log.dat",'w') as f:
                    dump(userData,f,default=str)
                    
                try:
                    if log_level == 1:
                        print("Terminating browser instance.")
                        logtext += "Terminating browser instance."
                    driver.close()
                    driver.close()
                except Exception:
                    pass
                WarpReconnect()
                if log_level == 1:
                    print("\nPausing execution for 43200 seconds\n")
                    logtext += "\nPausing execution for 43200 seconds\n"
                    logfile.write(logtext)
                else: pass
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
                    if log_level == 1:
                        print("\nPausing execution for 43200 seconds\n")
                        logtext += "\nPausing execution for 43200 seconds\n"
                        logfile.write(logtext)
                    else : pass
                    sleep(43200)
                else:
                    if log_level == 1:
                        print(f"\nPausing execution for {timeDifference.total_seconds()} seconds\n")
                        logtext +=f"\nPausing execution for {timeDifference.total_seconds()} seconds\n"
                        logfile.write(logtext)
                    else:pass
                    sleep(timeDifference.total_seconds())
                continue
            
        except FileNotFoundError as e:
            mkdir(f"{str(userdirectory)}\\AppData\\Roaming\\SOPHOS_auto_login")
            continue

if __name__ == "__main__":
    command_line_args = sys.argv[1: ]
    if main(command_line_args) == 1:
        print("Process failed. Possible reasons could be, invalid credentials, <browser_driver>.exe is not in PATH, warp-cli.exe is not in PATH, selenium module is not installed, webdriver_manager module is not installed.")
    