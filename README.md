# SOPHOS-Auto-Login
Script for automatically logging into SOPHOS.

Can automatically disconnect and reconnect to warp.(disconnect before accessing SOPHOS to bypass 'Captive Portal' error and reconnect after loggin in to SOPHOS)

### Requirements
1. Chrome/Firefox/Edge browser
2. Webdriver for the browser of choice ( download from https://www.selenium.dev/documentation/webdriver/getting_started/install_drivers)
3. Python packages : selenium, webdriver_manager,win10toast. Install using the following command
```
python -m pip install selenium webdriver_manager win10toast
```
4. The webdrivers should be added to PATH.

### Limitations
Currently works only if Warp is present ( I use Warp so didn't bother making it optional )

### Planned Features
System tray icon to enable manual termination of process.
