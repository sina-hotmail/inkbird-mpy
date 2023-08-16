# config
import settings
PERIPHERAL_MAC_ADDRESS=settings.PERIPHERAL_MAC_ADDRESS
WEB_APP_URL=settings.WEB_APP_URL
DEVICE_NAME=settings.DEVICE_NAME
WLAN_SSID=settings.WLAN_SSID
WLAN_PASSWD=settings.WLAN_PASSWD



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
            conn_state = -2
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
    conn_time = 30
    # conn_state  0:connected , -1:connecting  , -2:disconnected
    conn_state=-1
    ble.gap_connect(addr_type, PERIPHERAL_MAC_ADDRESS)
    while( conn_state != 0 ):
        print("BLE connecting ..",conn_time)
        if( conn_state == -2):
            conn_state =-1
            ble.gap_connect(addr_type, PERIPHERAL_MAC_ADDRESS)
        
        conn_time = conn_time -1
        if(conn_time < 0):
            break
        utime.sleep_ms(1000)


    if( conn_state == 0):

        ### 3. BLE read ( GATT Client ) 
        rstatus=-1
        ble.gattc_read(handle,  0x2d )  # INKBIRD IBS-TH1PLUS is　0x2d
        ### wait read 
        while(rstatus!=0):
            utime.sleep_ms(2000)
        
        ### output
        print(temp/100 , humid/100)

        ## 4.BLE disconnect 
        ble.gap_disconnect(handle)

    # 5. BLE OFF
    ble.active(False)

    ##########
    # 1 BLE ON
    ble.active(True)

    ##  irq seup for 0x03
    def bt_irq_x03(event, data):
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
            conn_state = -2
        elif event == _IRQ_GATTC_READ_RESULT:
            # A gattc_read() has completed.
            conn_handle, value_handle, char_data = data
            global batt
            (batt,) = ustruct.unpack('B', char_data)
        elif event == _IRQ_GATTC_READ_DONE:
            # A gattc_read() has completed.
            # Note: Status will be zero on success, implementation-specific value otherwise.
            conn_handle, value_handle, status = data
            global rstatus2
            rstatus2=status

    ble.irq(bt_irq_x03)


    ##  2. BLE connect
    addr_type=0 
    conn_time = 30
    # conn_state  0:connected , -1:connecting  , -2:disconnected
    conn_state=-1
    ble.gap_connect(addr_type, PERIPHERAL_MAC_ADDRESS)
    while( conn_state != 0 ):
        print("BLE connecting ..",conn_time)
        if( conn_state == -2):
            conn_state =-1
            ble.gap_connect(addr_type, PERIPHERAL_MAC_ADDRESS)
        
        conn_time = conn_time -1
        if(conn_time < 0):
            break
        utime.sleep_ms(1000)

    if( conn_state == 0):
        ### 3. BLE read ( GATT Client ) 
        rstatus2=-1
        ble.gattc_read(handle,  0x03 )  # INKBIRD IBS-TH1PLUS battery
        ### wait read 
        while(rstatus2!=0):
            utime.sleep_ms(1000)

        print( batt )

        ## 4.BLE disconnect 
        ble.gap_disconnect(handle)

    # 5. BLE OFF
    ble.active(False)


    if( (rstatus==0) and (rstatus2==0) ): 
        ###################################
        # 6.WLAN connect

        import network
        wlan = network.WLAN(network.STA_IF)
        wlan.active(True)

        def do_connect():
            if not wlan.isconnected():
                print('connecting to network..')
                wlan.connect( WLAN_SSID, WLAN_PASSWD)
                while not wlan.isconnected():
                    pass
            print('network config:', wlan.ifconfig())

        do_connect()

        # get NTPtime
        from machine import RTC
        import ntptime
        rtc = RTC()
        ntptime.settime()
        (year, month, day, weekday, hours, minutes, seconds, subseconds)=rtc.datetime()
        strDate = str(year)+'-'+str(month) + '-' + str(day) + ' ' + str(hours) + ':' +str(minutes) + ':' +str(seconds)
 
        # 7. POST data
        import urequests
        import ujson

        # upload to the spreadsheet
        data = {
            'DeviceName': DEVICE_NAME,
            'Date_Master': strDate ,
            'Date': strDate,
            'SensorType': '' ,
            'Temperature': str(temp/100),
            'Humidity': str(humid/100),
            'Light': '',
            'UV': '',
            'Pressure': '',
            'Noise': '',
            'BatteryVoltage': str(batt)
        }

        response = urequests.post( WEB_APP_URL, data=ujson.dumps(data))

        response.close()
    
        #  WLAN disconnect
        wlan.disconnect()

        wlan.active(False)

    # 8.Sleep 
    sleep_time= 30*60      #30 min
    while(sleep_time > 0):
        print(sleep_time)
        sleep_time=sleep_time-1
        utime.sleep(1)  # 1sec 
