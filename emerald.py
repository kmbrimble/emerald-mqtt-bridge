import datetime
import os
import pydbus
import pytz
import time
import random
import paho.mqtt.client as mqtt
from gi.repository import GLib
from itertools import repeat

# References:
# 0) https://github.com/WeekendWarrior1/emerald_electricity_advisor
# 1) https://stackoverflow.com/questions/63928675/pydbus-more-notifications-same-time-handling
# 2) https://github.com/karulis/pybluez
# 3) https://ukbaz.github.io/howto/bluetooth_overview.html
# 4) https://pypi.org/project/pygatt/
# 5) https://raspberrypi.stackexchange.com/questions/114044/scripting-bluetoothctl-causes-it-to-fail-after-connection
# 6) https://stackoverflow.com/questions/28868393/accessing-bluetooth-dongle-from-inside-docker
# 7) https://ukbaz.github.io/howto/bluetooth_overview.html <- Must watch video

#
# Setup the debug level from the environment
#
if 'DEBUG_LEVEL' in os.environ:
    debug_level = int(os.environ['DEBUG_LEVEL'])
    print("Debug level set to", debug_level, flush=True)
else:
    debug_level = 0

def dbg(level):
    #
    # Boolean if ok to if dbg(0): print.
    #
    return level <= debug_level

# Setup local timestamp TZ stuff
localTZ       = pytz.timezone("Australia/Melbourne")

def datetimestamp():
    t = datetime.datetime.now(localTZ)
    return t.strftime("%d %b %Y %H:%M:%S")

if dbg(0): print(datetimestamp(), "Emerald EMS to MQTT", flush=True)

if 'DEVICE' in os.environ:
    DEV_EMERALD = os.environ['DEVICE']
else:
    DEV_EMERALD = '30:1B:97:64:B0:7B'
# bus = pydbus.SystemBus()

# Debug stuff to if dbg(0): print object methods
def get_methods(object, spacing=20):
    #
    # Reference: https://stackoverflow.com/questions/34439/finding-what-methods-a-python-object-has
    #
    methodList = []
    for method_name in dir(object):
        try:
            if callable(getattr(object, method_name)):
                methodList.append(str(method_name))
        except Exception:
            methodList.append(str(method_name))
    processFunc = (lambda s: ' '.join(s.split())) or (lambda s: s)
    for method in methodList:
        try:
            if dbg(9): print(str(method.ljust(spacing)) + ' ' +
            processFunc(str(getattr(object, method).__doc__)[0:90]))
        except Exception:
            if dbg(9): print(method.ljust(spacing) + ' ' + ' getattr() failed')
    if dbg(9): print(flush=True)

class mqtt_client_object:
    def get_mqtt_settings(self):
        if dbg(5): print(datetimestamp(), "OS Environment passed in:", os.environ, flush=True)
        settings = {'ok':False}
        if 'MQTT_BASE_TOPIC' in os.environ:
            settings['base_topic'] = os.environ['MQTT_BASE_TOPIC']
        else:
            if dbg(2): print(datetimestamp(), "MQTT_BASE_TOPIC initialization error", flush=True)
            return False
        if 'MQTT_HOSTNAME' in os.environ:
            settings['hostname'] = os.environ['MQTT_HOSTNAME']
        else:
            if dbg(2): print(datetimestamp(), "MQTT_HOSTNAME initialization error", flush=True)
            return False
        if 'MQTT_PORT' in os.environ:
            settings['port'] = os.environ['MQTT_PORT']
        else:
            if dbg(2): print(datetimestamp(), "MQTT_PORT initialization error", flush=True)
            return False
        if 'MQTT_USERNAME' in os.environ:
            settings['username'] = os.environ['MQTT_USERNAME']
        else:
            if dbg(2): print(datetimestamp(), "MQTT_USERNAME initialization error", flush=True)
            return False
        if 'MQTT_PASSWORD' in os.environ:
            settings['password'] = os.environ['MQTT_PASSWORD']
        else:
            if dbg(2): print(datetimestamp(), "MQTT_PASSWORD initialization error", flush=True)
            return False
        settings['client_id'] = f'python-mqtt-{random.randint(0, 1000)}'
        if dbg(5): print(datetimestamp(), "MQTT settings initialized", flush=True)
        settings['ok'] = True
        return settings

    def __init__(self):
        self.private_connected = False
        self.last_mid          = -1
        self.settings          = self.get_mqtt_settings()

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self.private_connected = True
            if dbg(5): print(datetimestamp(), "Connected to MQTT Broker!", flush=True)
        else:
            self.private_connected = False
            if dbg(0): print(datetimestamp(), "Failed to connect, return code %d\n", rc, flush=True)

    def on_disconnect(self, client, userdata, rc):
        self.private_connected = False
        if dbg(0): print(datetimestamp(), "MQTT disconnected", flush=True)

    def on_publish(self, client, userdata, mid):
        self.last_mid = mid
        if dbg(9): print(datetimestamp(), "MQTT on_publish, mid {}".format(mid), flush=True)

    def connected(self):
        return self.private_connected

    def connect(self):
        if self.settings['ok'] != True:
            if dbg(9): print(datetimestamp(), "Connection error: invalid MQTT settings", flush = True)
            return self.private_connected
        # Set Connecting Client ID
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1, self.settings['client_id'])
        self.client.username_pw_set(self.settings['username'], self.settings['password'])
        self.client.on_connect    = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        self.client.on_publish    = self.on_publish
        self.client.loop_start()
        self.client.connect(self.settings['hostname'], int(self.settings['port']))
        timeout = 0
        while self.private_connected == False:
            timeout += 1
            if timeout > 10:
                break
            time.sleep(1)
        if dbg(9): print(datetimestamp(), "connect_mqtt:", self.settings, flush=True)
        return self.private_connected

    def disconnect(self):
        self.private_connected = False
        self.client.disconnect()

    def publish(self, topic, data, qos, retain):
        if self.private_connected:
            self.waiting_mid = self.client.publish(self.settings['base_topic'] + topic, data, qos, retain)[1]
            if dbg(9): print(datetimestamp(), "Publish Result:", self.waiting_mid, flush = True)
            timeout = 0
            while self.waiting_mid != self.last_mid:
                if timeout > 100:
                    if dbg(1): print(datetimestamp(), "Publish timeout (mid:", self.waiting_mid, ")", flush = True)
                    break
                else:
                    timeout += 1
                    time.sleep(0.1)
        else:
            if dbg(9): print(datetimestamp(), "Publish error: not connected", flush = True)

class RemoteDevice:
    SERVICE_UUID_DEVICE_INFO = '0000180A-0000-1000-8000-00805f9b34fb'
    CHAR_UUID_MANUFACTURER   = '00002a29-0000-1000-8000-00805f9b34fb'
    CHAR_UUID_SERIAL         = '00002a25-0000-1000-8000-00805f9b34fb'
    CHAR_UUID_VERSION        = '00002a26-0000-1000-8000-00805f9b34fb'
    CHAR_UUID_2A05           = '00002a05-0000-1000-8000-00805f9b34fb'
    SERVICE_UUID_TIME        = '00001910-0000-1000-8000-00805f9b34fb'
    CHAR_UUID_TIME_READ      = '00002b10-0000-1000-8000-00805f9b34fb'
    CHAR_UUID_TIME_WRITE     = '00002b11-0000-1000-8000-00805f9b34fb'
    CHAR_UUID_10203          = '00010203-0405-0607-0809-0a0b0c0d2b12'
    SERVICE_UUID_BATTERY     = '0000180f-0000-1000-8000-00805f9b34fb'
    CHAR_UUID_BATTERY_READ   = '00002a19-0000-1000-8000-00805f9b34fb'

    cmdGetImpulse            = [ 0x00, 0x01, 0x01, 0x05, 0x00 ]
    cmdGetPairingCode        = int('0001030100',16)
    cmdGetEvery30sPowerConsumption \
                             = int('0001020306',16)
    cmdGetDeviceTime         = [ 0x00, 0x01, 0x01, 0x02, 0x00 ]
    cmdGetUpdatedPower       = [ 0x00, 0x01, 0x02, 0x01, 0x00 ]
    cmdGetEvery30sPowerConsumptionWithinHours \
                             = int('0001021308',16)

    # Set pulses_per_kwh, with 2 bytes after the command
    # eg. 000101040203E8 <- (1000 in hex = 03E8)
    cmdSetImpulse            = int('0001010402',16)
    cmdStartGettingHistory   = int('0001020400',16)
    cmdEndGettingHistory     = int('0001020600',16)
    cmdSetDeviceTime         = [ 0x00, 0x01, 0x01, 0x01, 0x04 ]
    cmdReset                 = int('0001010a00',16)
    # Enable automatic upload of pulses (every 30s)
    # eg. 0001020b0101 <- (true in hex = 01)
    cmdSetAutoUploadStatus   = [ 0x00, 0x01, 0x02, 0x0b, 0x01 ]

    cmdReturn30sPowerConsumption \
                             = [ 0x00, 0x01, 0x02, 0x0a, 0x06 ]
    cmdReturnUpdatedPower    = [ 0x00, 0x01, 0x02, 0x02, 0x04 ]
    cmdReturnEvery30sPowerConsumption \
                             = [ 0x00, 0x01, 0x02, 0x05, 0x0e ]
    cmdReturnImpulse         = [ 0x00, 0x01, 0x01, 0x06, 0x02 ]
    cmdReturnPairingCode     = [ 0x00, 0x01, 0x03, 0x02, 0x06 ]
    cmdReturnDeviceTime      = [ 0x00, 0x01, 0x01, 0x03, 0x04 ]

    gatt_uuid           = ""
    gatt_uuid           = ""
    notify_session_list = []
    uuids               = []

    def get_characteristic_path(self, dev_path, uuid):
        for path in self.mng_objs:
            chr_uuid = self.mng_objs[path].get('org.bluez.GattCharacteristic1', {}).get('UUID')
            if path.startswith(dev_path) and chr_uuid == uuid:
               return path

    def get_remote_UUIDs(self):
        self.uuids = []
        for path in self.mng_objs:
            chr_uuid = self.mng_objs[path].get('org.bluez.GattCharacteristic1', {}).get('UUID')
            if type(chr_uuid) != type(None):
                self.uuids.append(chr_uuid)

    def print_remote_UUIDs(self):
        for path in self.mng_objs:
            chr_uuid = self.mng_objs[path].get('org.bluez.GattCharacteristic1', {}).get('UUID')
            if type(chr_uuid) != type(None):
                if dbg(2): print(datetimestamp(), chr_uuid + ": " + path)

    def __init__(self, mac_addr):
        self.bus      = pydbus.SystemBus()
        device_path   = f"/org/bluez/hci0/dev_{mac_addr.replace(':', '_')}"
        self.device   = self.bus.get('org.bluez', device_path)
        self.mngr     = self.bus.get('org.bluez', '/')
        self.adapter  = self.bus.get('org.bluez', '/org/bluez/hci0')
        self.mng_objs = self.mngr.GetManagedObjects()

        # Placeholder for characteristic details
        self.characteristic        = None
        self.notify_characteristic = None

    def _get_gatt_details(self, gattUUID):
        char_path           = self.get_characteristic_path(self.device._path, gattUUID)
        self.characteristic = self.bus.get('org.bluez', char_path)
        self.gatt_uuid = gattUUID

    def connect(self):
        if dbg(1): print(datetimestamp(), 'Attempt connection', flush=True)
        self.device.Connect()
        for i in range (1,30):
            if self.device.ServicesResolved: break
            if dbg(5): print(datetimestamp(), 'Wait for service resolution', i, flush=True)
            time.sleep(1)
        if not self.device.ServicesResolved:
            raise TimeoutError('Failed to resolve services within time limit')
        self._get_gatt_details(RemoteDevice.CHAR_UUID_TIME_READ)

    def disconnect(self):
        if dbg(5): print(datetimestamp(), "Disconnect enter ==================" , flush=True)
        for i in self.notify_session_list:
            self._get_gatt_details(i)
            if dbg(9): print(datetimestamp(), "StopNotify self.characteristic.UUID",self.gatt_uuid , flush=True)
            try:
                self.characteristic.StopNotify()
            except Exception as e:
                if dbg(0): print(datetimestamp(), "Exception during disconnect", flush=True)
                if dbg(0): print(datetimestamp(), e, flush=True)
        self.device.Disconnect()
        if dbg(5): print(datetimestamp(), "Disconnect leave ==================" , flush=True)

    def is_connected(self):
        return self.device.Connected

    def get_gatt_details(self, gattUUID):
        self._get_gatt_details(gattUUID)

    def read(self):
        return self.characteristic.ReadValue({})

    def write(self, new_value):
        self.characteristic.WriteValue(new_value, {})

    def _notify_handler(self, iface, prop_changed, prop_removed):
        value = prop_changed.get('Value', [])
        if len(value) > 0:
            self.print_notify_data(self.device.Address, value)

    def _notify_handler_00002b10_0000_1000_8000_00805f9b34fb(self, iface, prop_changed, prop_removed):
        value = prop_changed.get('Value', [])
        if len(value) > 0:
            self.print_notify_data('00002b10-0000-1000-8000-00805f9b34fb', value)

    def _notify_handler_00002a05_0000_1000_8000_00805f9b34fb(self, iface, prop_changed, prop_removed):
        value = prop_changed.get('Value', [])
        if len(value) > 0:
            self.print_notify_data('00002a05-0000-1000-8000-00805f9b34fb', value)

    def _notify_handler_00010203_0405_0607_0809_0a0b0c0d2b12(self, iface, prop_changed, prop_removed):
        value = prop_changed.get('Value', [])
        if len(value) > 0:
            self.print_notify_data('00010203-0405-0607-0809-0a0b0c0d2b12', value)

    def _notify_handler_00002b11_0000_1000_8000_00805f9b34fb(self, iface, prop_changed, prop_removed):
        value = prop_changed.get('Value', [])
        if len(value) > 0:
            self.print_notify_data('00002b11-0000-1000-8000-00805f9b34fb', value)

    def _notify_handler_00002a26_0000_1000_8000_00805f9b34fb(self, iface, prop_changed, prop_removed):
        value = prop_changed.get('Value', [])
        if len(value) > 0:
            self.print_notify_data('00002a26-0000-1000-8000-00805f9b34fb', value)

    def _notify_handler_00002a25_0000_1000_8000_00805f9b34fb(self, iface, prop_changed, prop_removed):
        value = prop_changed.get('Value', [])
        if len(value) > 0:
            self.print_notify_data('00002a25-0000-1000-8000-00805f9b34fb', value)

    def _notify_handler_00002a29_0000_1000_8000_00805f9b34fb(self, iface, prop_changed, prop_removed):
        value = prop_changed.get('Value', [])
        if len(value) > 0:
            self.print_notify_data('00002a29-0000-1000-8000-00805f9b34fb', value)

    def set_notify(self):
        unknown_string = ""
        if self.gatt_uuid == "00002b10-0000-1000-8000-00805f9b34fb":
            self.characteristic.onPropertiesChanged = self._notify_handler_00002b10_0000_1000_8000_00805f9b34fb
        elif self.gatt_uuid == "00002a05-0000-1000-8000-00805f9b34fb":
            self.characteristic.onPropertiesChanged = self._notify_handler_00002a05_0000_1000_8000_00805f9b34fb
        elif self.gatt_uuid == "00010203-0405-0607-0809-0a0b0c0d2b12":
            self.characteristic.onPropertiesChanged = self._notify_handler_00010203_0405_0607_0809_0a0b0c0d2b12
        elif self.gatt_uuid == "00002b11-0000-1000-8000-00805f9b34fb":
            self.characteristic.onPropertiesChanged = self._notify_handler_00002b11_0000_1000_8000_00805f9b34fb
        elif self.gatt_uuid == "00002a26-0000-1000-8000-00805f9b34fb":
            self.characteristic.onPropertiesChanged = self._notify_handler_00002a26_0000_1000_8000_00805f9b34fb
        elif self.gatt_uuid == "00002a25-0000-1000-8000-00805f9b34fb":
            self.characteristic.onPropertiesChanged = self._notify_handler_00002a25_0000_1000_8000_00805f9b34fb
        elif self.gatt_uuid == "00002a29-0000-1000-8000-00805f9b34fb":
            self.characteristic.onPropertiesChanged = self._notify_handler_00002a29_0000_1000_8000_00805f9b34fb
        else:
            unknown_string = "***Unknown***"
            self.characteristic.onPropertiesChanged = self._notify_handler
        if dbg(5): print(datetimestamp(), "Set handler:", self.gatt_uuid, unknown_string, flush=True)
        self.characteristic.StartNotify()
        self.notify_session_list.append(self.gatt_uuid)

    def start_notify(self):
        if dbg(5): print(datetimestamp(), "Emerald UUID callbacks ==============================", flush=True)
        self.get_remote_UUIDs()
        for uuid in self.uuids:
            self.get_gatt_details(uuid)
            try:
                self.set_notify()
            except:
                # Not all uuids support a call back
                pass

    def set_current_datetime(self):
        t = datetime.datetime.now(localTZ)
        year   = t.year - 2000
        month  = t.month
        day    = t.day
        hour   = t.hour
        minute = t.minute
        second = t.second
        dataToSnd  = (year   & int('0b111111', 2)) << 26
        dataToSnd += (month  & int(  '0b1111', 2)) << 22
        dataToSnd += (day    & int( '0b11111', 2)) << 17
        dataToSnd += (hour   & int( '0b11111', 2)) << 12
        dataToSnd += (minute & int('0b111111', 2)) <<  6
        dataToSnd += (second & int('0b111111', 2))
        if dbg(9): print(datetimestamp(), "{0:b}".format(dataToSnd))
        if dbg(3): print(datetimestamp(), 'Set DateTime:', year, month, day, hour, minute, second, flush=True)
        cmd = self.cmdSetDeviceTime
        cmd.append((dataToSnd >> 24) & int('0b11111111', 2))
        cmd.append((dataToSnd >> 16) & int('0b11111111', 2))
        cmd.append((dataToSnd >>  8) & int('0b11111111', 2))
        cmd.append((dataToSnd)       & int('0b11111111', 2))
        self.get_gatt_details(self.CHAR_UUID_TIME_WRITE)
        self.write(cmd)

    def set_auto_upload(self, on_off):
        cmd = self.cmdSetAutoUploadStatus
        cmd.append(on_off)
        self.get_gatt_details(self.CHAR_UUID_TIME_WRITE)
        self.write(cmd)

    def print_notify_data(self, handler_uuid, ndata):
        def decode_datetime(data):
            dict = {}
            dict['year' ] = (data >> 26) & int('0b111111', 2)
            dict['month'] = (data >> 22) & int(  '0b1111', 2)
            dict['days' ] = (data >> 17) & int( '0b11111', 2)
            dict['hours'] = (data >> 12) & int( '0b11111', 2)
            dict['mins' ] = (data >>  6) & int('0b111111', 2)
            dict['secs' ] =  data        & int('0b111111', 2)
            return dict
        #
        # Print returned data.
        #
        if dbg(9):
            print(datetimestamp(), "==>", flush=True)
            print(datetimestamp(), f'{handler_uuid} length: ', len(ndata), flush=True)
            for i in ndata:
                print(datetimestamp(), "Typeof(i)=", type(i), i, flush=True)
                print(datetimestamp(), f'{handler_uuid} is {int.from_bytes(ndata, byteorder="little")}', flush=True)
                print(datetimestamp(), f'{handler_uuid} is "{"".join( chr(x) for x in ndata)}"', flush=True)
        if len(ndata) == 9:
            cmd = ndata[:5]
            # FIXED: Uses index 5, 6, 7, 8
            dataReturned = (ndata[5] << 24) + (ndata[6] << 16) + (ndata[7] << 8) + ndata[8]
            if cmd == self.cmdReturnUpdatedPower:
                print(datetimestamp(), "cmdReturnUpdatedPower:", dataReturned, flush="True")
                mqtt_client.publish('/power/lastUpdate', datetimestamp(), qos = 1, retain = True)
                mqtt_client.publish('/power/watts',      dataReturned,    qos = 1, retain = True)
            elif cmd == self.cmdReturnDeviceTime:
                if dbg(0): print(datetimestamp(), "cmdReturnDeviceTime:", "{0:b}".format(dataReturned), decode_datetime(dateReturned), flush="True")
            else:
                if dbg(0): print(datetimestamp(), f'{handler_uuid} is "{"".join( """0x{:02X},""".format(x) for x in ndata)}"', flush=True)
        elif len(ndata) == 11:
            cmd          = ndata[:5]
            dateReturned = (ndata[6] << 24) + (ndata[6] << 16) + (ndata[7] << 8) + ndata[8]
            data         = (ndata[9] << 16) + ndata[10]
            if cmd == self.cmdReturn30sPowerConsumption:
                print(datetimestamp(), "cmdReturn30sPowerConsumption:", decode_datetime(dateReturned), "pulses count:", data, flush=True)
                mqtt_client.publish('/energy/lastUpdate', datetimestamp(), qos = 1, retain = True)
                mqtt_client.publish('/energy/pulses',     data,            qos = 1, retain = True)
        else:
            if dbg(0): print(datetimestamp(), f'{handler_uuid} is "{"".join( """0x{:02X},""".format(x) for x in ndata)}"', flush=True)

dev_emerald = RemoteDevice(DEV_EMERALD)
if dbg(2): print(datetimestamp(), "dev_emerald trying to connect", flush=True)
dev_emerald.connect()
if dbg(2): print(datetimestamp(), "dev_emerald connected", flush=True)

mqtt_client = mqtt_client_object()
mqtt_client.connect()
if mqtt_client.connected():
    if dbg(2): print(datetimestamp(), "MQTT connected OK", flush=True)
else:
    if dbg(2): print(datetimestamp(), "MQTT connect failed", flush=True)

if dbg(5):
    # Get commands and properties available
    adapter = dev_emerald.bus.get('org.bluez', '/org/bluez/hci0')
    dev     = dev_emerald.bus.get('org.bluez', '/org/bluez/hci0/dev_' + DEV_EMERALD.replace(':','_'))

    dirAdaptor = dir(adapter)
    print(datetimestamp(), "Adaptor =============================================", flush=True)
    for i in dirAdaptor:
        print(datetimestamp(), i, end = "\n", flush=True)
    print(datetimestamp(), "Device  =============================================", flush=True)
    dirDev     = dir(dev)
    for i in dirDev:
        print(datetimestamp(), i, end = "\n", flush=True)
    print(datetimestamp(), "Adaptor UUIDs ========================================", flush=True)
    # List Adaptor UUIDs
    lstUUIDs = adapter.UUIDs
    waitCounter = 0
    while len(lstUUIDs) == 0:
        print(datetimestamp(), "UUIDs = 0", flush=True)
        time.sleep(1)
        lstUUIDs = adapter.UUIDs
        waitCounter += 1
        if waitCounter > 9:
            exit(1)
    lstUUIDs = adapter.UUIDs
    for i in range(len(lstUUIDs)):
        print(datetimestamp(), lstUUIDs[i], flush=True)
    print(datetimestamp(), "Device UUIDs ========================================", flush=True)
    # List Device UUIDs
    lstUUIDs = dev.UUIDs
    waitCounter = 0
    while len(lstUUIDs) == 0:
        print(datetimestamp(), "UUIDs = 0", flush=True)
        time.sleep(1)
        lstUUIDs = dev.UUIDs
        waitCounter += 1
        if waitCounter > 9:
            exit(1)
    lstUUIDs = dev.UUIDs
    for i in range(len(lstUUIDs)):
        print(datetimestamp(), lstUUIDs[i], flush=True)
    print(datetimestamp(), "Emerald UUIDs paths =================================", flush=True)
    dev_emerald.print_remote_UUIDs()
    print(datetimestamp(), "Emerald UUID values  ================================", flush=True)
    for uuid in dev_emerald.uuids:
        dev_emerald.get_gatt_details(uuid)
        print(datetimestamp(), uuid,":",bytes(dev_emerald.read()), flush=True)
    print(datetimestamp(), "Emerald Manufacturer string =========================", flush=True)
    dev_emerald.get_gatt_details(dev_emerald.CHAR_UUID_MANUFACTURER)
    print(datetimestamp(), bytes(dev_emerald.read()))
    print(datetimestamp(), "Emerald Serial number ===============================", flush=True)
    dev_emerald.get_gatt_details(dev_emerald.CHAR_UUID_SERIAL)
    print(datetimestamp(), bytes(dev_emerald.read()))
    print(datetimestamp(), "Emerald Version number ==============================", flush=True)
    dev_emerald.get_gatt_details(dev_emerald.CHAR_UUID_VERSION)
    print(datetimestamp(), bytes(dev_emerald.read()))
    print(datetimestamp(), "Emerald 00002a05-0000-1000-8000-00805f9b34fb ========", flush=True)
    dev_emerald.get_gatt_details(dev_emerald.CHAR_UUID_2A05)
    print(datetimestamp(), bytes(dev_emerald.read()))
    print(datetimestamp(), "Emerald Read data ===================================", flush=True)
    dev_emerald.get_gatt_details(dev_emerald.CHAR_UUID_TIME_READ)
    print(datetimestamp(), bytes(dev_emerald.read()))
    print(datetimestamp(), "Emerald 00010203-0405-0607-0809-0a0b0c0d2b12 ========", flush=True)
    dev_emerald.get_gatt_details(dev_emerald.CHAR_UUID_10203)
    print(datetimestamp(), bytes(dev_emerald.read()))

def mainloop_idle_work():
    #
    # Ref: https://stackoverflow.com/questions/20291653/pygtk-gobject-idle-add-and-timeout-add-with-threads
    #      https://www.programcreek.com/python/example/84576/gi.repository.GLib.idle_add
    #
    if dbg(2): print(datetimestamp(), "Mainloop Idle Worker", flush=True)
    GLib.idle_add(mainloop_idle_work)

def mainloop_timer(mainloop):
    #
    # Ref: https://docs.gtk.org/glib/func.timeout_add_seconds.html
    #
    if dbg(5): print(datetimestamp(), "Mainloop Timer", flush=True)

    dev_emerald.get_gatt_details(dev_emerald.CHAR_UUID_TIME_WRITE)
    try:
        # dev_emerald.write(dev_emerald.cmdGetDeviceTime)
        # dev_emerald.write(dev_emerald.cmdGetImpulse)
        if dev_emerald.is_connected():
            dev_emerald.write(dev_emerald.cmdGetUpdatedPower)
        else:
            if dbg(0): print(datetimestamp(), "mainloop_timeout is_connected():", dev_emerald.is_connected(), flush=True)
            mainloop.quit()
    except Exception as e:
        if dbg(0): print(datetimestamp(), "Unknown Exception:", str(e), flush=True)
        mainloop.quit()

    if dbg(5):
        if mainloop.is_running():
            print(datetimestamp(), "Mainloop context:", mainloop.get_context() , flush=True)
    if dbg(9): print(datetimestamp(), "GLib main depth:", GLib.main_depth(), flush=True)
    if dbg(9): print(datetimestamp(), "GLib main current source:", GLib.main_current_source(), flush=True)
    GLib.timeout_add_seconds(60, mainloop_timer, mainloop)

dev_emerald.start_notify()
dev_emerald.set_current_datetime()
time.sleep(10)
dev_emerald.set_auto_upload(1)

# Debug junk to list methods
# get_methods(GLib)

mainloop = GLib.MainLoop()
# GLib.idle_add(mainloop_idle_work)
GLib.timeout_add_seconds(5, mainloop_timer, mainloop)

while True:
    try:
        mainloop.run()
        if dbg(0): print(datetimestamp(), "Mainloop looping:", dev_emerald.is_connected(), flush=True)
        if dev_emerald.is_connected() == False:
            dev_emerald.connect()
        else:
            break
    except KeyboardInterrupt:
        if dbg(0): print(datetimestamp(), "Keyboard Interrupt:", flush=True)
        mainloop.quit()
        break
    except Exception as e:
        if dbg(0): print(datetimestamp(), "Unknown Exception:", str(e), flush=True)
        mainloop.quit()
        break

if dbg(2): print(datetimestamp(), "=====================================================", flush=True)
mqtt_client.disconnect()
dev_emerald.disconnect()
if dbg(0): print ("Done", flush=True)
