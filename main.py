# config
PERIPHERAL_MAC_ADDRESS=b'\xFF\xFF\xFF\xFF\xFF\xFF'
WEB_APP_URL='https://script.google.com/macros/s/******/exec'
DEVICE_NAME='******'
WLAN_SSID='******'
WLAN_PASSWD='******'

#  print micropython  version 
import os
print(os.uname())


##
import ubluetooth
import utime
import ustruct

# event codes は 以下を参照
# https://docs.micropython.org/en/latest/library/bluetooth.html#event-handling 
_IRQ_PERIPHERAL_CONNECT = (7)
_IRQ_PERIPHERAL_DISCONNECT = (8)
_IRQ_GATTC_READ_RESULT = (15)
_IRQ_GATTC_READ_DONE = (16)
_IRQ_CONNECTION_UPDATE = (27)


while True:
    ## 1.BLE ON
    ble=ubluetooth.BLE()
    ble.active(True)

    # setting IRQ
    def bt_irq(event, data):
        print("BLE event:" ,event)
        if event == _IRQ_PERIPHERAL_CONNECT:
            # A successful gap_connect().
            conn_handle, addr_type, addr = data
            global conn_state
            conn_state = 0
            global handle
            handle=conn_handle
        elif event == _IRQ_PERIPHERAL_DISCONNECT:
            # Connected peripheral has disconnected.
            conn_handle, addr_type, addr = data
            global conn_state
            conn_state = -1
        elif event == _IRQ_GATTC_READ_RESULT:
            # A gattc_read() has completed.
            conn_handle, value_handle, char_data = data
            global temp
            global humid
            (temp, humid, unknown1, unknown2, unknown3) = ustruct.unpack('<hhBBB', char_data)
        elif event == _IRQ_GATTC_READ_DONE:
            # A gattc_read() has completed.
            # Note: Status will be zero on success, implementation-specific value otherwise.
            conn_handle, value_handle, status = data
            global rstatus
            rstatus=status
        elif event == _IRQ_CONNECTION_UPDATE:
            # The remote device has updated connection parameters.
            conn_handle, conn_interval, conn_latency, supervision_timeout, status = data


    ble.irq(bt_irq)

    ##  2. BLE connect
    addr_type=0 

    # conn_state  0:connected , -1:connecting  , -2:disconnected
    conn_state=-1
    ble.gap_connect(addr_type, PERIPHERAL_MAC_ADDRESS)
    while( conn_state != 0 ):
        print("BLE connecting ..")
        if( conn_state == -2):
            conn_state =-1
            ble.gap_connect(addr_type, PERIPHERAL_MAC_ADDRESS)
        utime.sleep_ms(1000)

    ### 3. BLE read ( GATT Client ) 
    # INKBIRD IBS-TH1PLUS =　0x2d
    value_handle=0x2d

    rstatus=-1
    ble.gattc_read(handle,value_handle)
    ### wait read 
    while(rstatus!=0):
        utime.sleep_ms(2000)

    ### output
    print(temp/100 , humid/100)


    ## 4.BLE disconnect 
    ble.gap_disconnect(handle)

    # 5. BLE OFF
    ble.active(False)

    ###################################
    # 6.WLAN connect

    def do_connect():
        import network
        wlan = network.WLAN(network.STA_IF)
        wlan.active(True)
        if not wlan.isconnected():
            print('connecting to network..')
            wlan.connect( WLAN_SSID, WLAN_PASSWD)
            while not wlan.isconnected():
                pass
        print('network config:', wlan.ifconfig())

    do_connect()

 
    # 7. POST data
    import urequests
    import ujson

    # upload to the spreadsheet
    data = {
        'DeviceName': DEVICE_NAME,
        'Date_Master': '',
        'Date': '',
        'SensorType': '' ,
        'Temperature': str(temp/100),
        'Humidity': str(humid/100),
        'Light': '',
        'UV': '',
        'Pressure': '',
        'Noise': '',
        'BatteryVoltage': ''
     }

    response = urequests.post( WEB_APP_URL, data=ujson.dumps(data))

    response.close()

    # 8.Sleep 
    sleep_time= 30*60      #30 min
    while(sleep_time > 0):
        print(sleep_time)
        sleep_time=sleep_time-1
        utime.sleep(1)  # 1sec 
