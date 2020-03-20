import sys
import os
import dbus, dbus.mainloop.glib
import json
from gi.repository import GObject
from my_advertisement import Advertisement
from my_advertisement import register_ad_cb, register_ad_error_cb
from gatt_server import Service, Characteristic
from gatt_server import register_app_cb, register_app_error_cb
 
BLUEZ_SERVICE_NAME =           'org.bluez'
DBUS_OM_IFACE =                'org.freedesktop.DBus.ObjectManager'
LE_ADVERTISING_MANAGER_IFACE = 'org.bluez.LEAdvertisingManager1'
GATT_MANAGER_IFACE =           'org.bluez.GattManager1'
GATT_CHRC_IFACE =              'org.bluez.GattCharacteristic1'
WIFICONF_SERVICE_UUID =            '00001201-0000-1152-2019-0009af100700'
WIFICONF_RX_CHARACTERISTIC_UUID =  '00001202-0000-1152-2019-0009af100700'
WIFICONF_TX_CHARACTERISTIC_UUID =  '00001203-0000-1152-2019-0009af100700'
LOCAL_NAME =                   'BLE_Wificonfig'
mainloop = None

class Finder:
    def __init__(self, *args, **kwargs):
        self.server_name = kwargs['server_name']
        self.password = kwargs['password']
        self.main_dict = {}

    def run(self):
        command = """sudo iwlist wlan0 scan | grep -ioE 'ssid:"(.*{}.*)"'"""
        result = os.popen(command.format(self.server_name))
        result = list(result)

        if "Device or resource busy" in result:
                return None
        else:
            ssid_list = [item.lstrip('SSID:').strip('"\n') for item in result]
            print("Successfully get ssids {}".format(str(ssid_list)))

        for name in ssid_list:
            try:
                result = self.connection(name)
            except Exception as exp:
                print("Couldn't connect to name : {}. {}".format(name, exp))
            else:
                if result:
                    print("Successfully connected to {}".format(name))

    def connection(self, name):
        try:
            os.system("nmcli d wifi connect {} password {}".format(name,
       self.password))
        except:
            raise
        else:
            return True

class TxCharacteristic(Characteristic):
    def __init__(self, bus, index, service):
        Characteristic.__init__(self, bus, index, WIFICONF_TX_CHARACTERISTIC_UUID,
                                ['notify'], service)
        self.notifying = False
        GObject.io_add_watch(sys.stdin, GObject.IO_IN, self.on_console_input)
 
    def on_console_input(self, fd, condition):
        s = fd.readline()
        if s.isspace():
            pass
        else:
            self.send_tx(s)
        return True
 
    def send_tx(self, s):
        if not self.notifying:
            return
        value = []
        for c in s:
            value.append(dbus.Byte(c.encode()))
        self.PropertiesChanged(GATT_CHRC_IFACE, {'Value': value}, [])
 
    def StartNotify(self):
        if self.notifying:
            return
        self.notifying = True
 
    def StopNotify(self):
        if not self.notifying:
            return
        self.notifying = False
 
class RxCharacteristic(Characteristic):
    def __init__(self, bus, index, service):
        Characteristic.__init__(self, bus, index, WIFICONF_RX_CHARACTERISTIC_UUID,
                                ['write'], service)
 
    def WriteValue(self, value, options):
        print('remote: {}'.format(bytearray(value).decode()))
        #value_dict = json.loads(bytearray(value).decode())
        #print('ssid: {}'.format(value_dict['SSID']))
        #print('pw: {}'.format(value_dict['PW']))
	#F = Finder(server_name=value_dict['SSID'],
	#	   password=value_dict['PW'])
        str_value = bytearray(value).decode()
        str_array = str_value.split(",")
        F = Finder(server_name=str_array[0], password=str_array[1])
        F.run()
 
class WifiConfService(Service):
    def __init__(self, bus, index):
        Service.__init__(self, bus, index, WIFICONF_SERVICE_UUID, True)
        self.add_characteristic(TxCharacteristic(bus, 0, self))
        self.add_characteristic(RxCharacteristic(bus, 1, self))
 
class Application(dbus.service.Object):
    def __init__(self, bus):
        self.path = '/'
        self.services = []
        dbus.service.Object.__init__(self, bus, self.path)
 
    def get_path(self):
        return dbus.ObjectPath(self.path)
 
    def add_service(self, service):
        self.services.append(service)
 
    @dbus.service.method(DBUS_OM_IFACE, out_signature='a{oa{sa{sv}}}')
    def GetManagedObjects(self):
        response = {}
        for service in self.services:
            response[service.get_path()] = service.get_properties()
            chrcs = service.get_characteristics()
            for chrc in chrcs:
                response[chrc.get_path()] = chrc.get_properties()
        return response
 
class WifiConfApplication(Application):
    def __init__(self, bus):
        Application.__init__(self, bus)
        self.add_service(WifiConfService(bus, 0))
 
class WifiConfAdvertisement(Advertisement):
    def __init__(self, bus, index):
        Advertisement.__init__(self, bus, index, 'peripheral')
        self.add_service_uuid(WIFICONF_SERVICE_UUID)
        self.add_local_name(LOCAL_NAME)
        self.include_tx_power = True
 
def find_adapter(bus):
    remote_om = dbus.Interface(bus.get_object(BLUEZ_SERVICE_NAME, '/'),
                               DBUS_OM_IFACE)
    objects = remote_om.GetManagedObjects()
    for o, props in objects.items():
        for iface in (LE_ADVERTISING_MANAGER_IFACE, GATT_MANAGER_IFACE):
            if iface not in props:
                continue
        return o
    return None
 
def main():
    global mainloop
    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
    bus = dbus.SystemBus()
    adapter = find_adapter(bus)
    if not adapter:
        print('BLE adapter not found')
        return
 
    service_manager = dbus.Interface(
                                bus.get_object(BLUEZ_SERVICE_NAME, adapter),
                                GATT_MANAGER_IFACE)
    ad_manager = dbus.Interface(bus.get_object(BLUEZ_SERVICE_NAME, adapter),
                                LE_ADVERTISING_MANAGER_IFACE)
 
    app = WifiConfApplication(bus)
    adv = WifiConfAdvertisement(bus, 0)
 
    mainloop = GObject.MainLoop()
 
    service_manager.RegisterApplication(app.get_path(), {},
                                        reply_handler=register_app_cb,
                                        error_handler=register_app_error_cb)
    ad_manager.RegisterAdvertisement(adv.get_path(), {},
                                     reply_handler=register_ad_cb,
                                     error_handler=register_ad_error_cb)
    try:
        mainloop.run()
    except KeyboardInterrupt:
        adv.Release()
 
if __name__ == '__main__':
    main()
