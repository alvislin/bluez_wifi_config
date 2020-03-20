# bluez_wifi_config
wificonfig with BLE base on bluez-5.50 (on RaspberryPi)

install python and download bluez-5.50

type command to start wifi config through BLE GATT Server

sudo python wificonfig_perpheral.py
[this version parser string with "ssid,password"]
or
sudo python wificonfig_perpheral_json.py
[this version parser JSON with {"SSID":"ssid", "PW":"pw"}]


you can download this app

![image](https://raw.githubusercontent.com/eddentsai/bluez_wifi_config/master/pic/1.png)

open app to scan BLE devices

![image](https://raw.githubusercontent.com/eddentsai/bluez_wifi_config/master/pic/2.png)

connect to get device info

![image](https://raw.githubusercontent.com/eddentsai/bluez_wifi_config/master/pic/3.png)

filled with ssid,password (because of length limit, need to add value)

![image](https://raw.githubusercontent.com/eddentsai/bluez_wifi_config/master/pic/4.png)
![image](https://raw.githubusercontent.com/eddentsai/bluez_wifi_config/master/pic/5.png)
![image](https://raw.githubusercontent.com/eddentsai/bluez_wifi_config/master/pic/6.png)
![image](https://raw.githubusercontent.com/eddentsai/bluez_wifi_config/master/pic/7.png)
