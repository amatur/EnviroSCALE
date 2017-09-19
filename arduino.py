import serial, time
import csv
import sys
import traceback 
import os
###@PI
# from sensors.gps.gps import GPS

USBi = 5
try:
    astring = 'bash /home/pi/EnviroSCALE/shellscripts/arduinotty.sh'
    USBi = int(os.popen(astring).read())
except:
    print "error in reading script"
    traceback.print_exc()
print USBi


while True:
    try:
        time.sleep(1)
        arduino = serial.Serial('/dev/ttyUSB' + str(USBi), 115200, timeout=.05)
        print "Successfully Connected to /dev/ttyUSB" +  str(USBi) + ", baud rate = " + str(115200) + ", timeout = " + str(.05)
        break
    except Exception, e:
        print e
        print "Oops! Connection  to /dev/ttyUSB" +  str(USBi) + " failed. Trying next..."
        time.sleep(4)
        USBi = USBi + 1
        if USBi > 9:
            USBi = 0


###@PI
# gps = GPS()

def read_arduino(choice):
    
    #arduino.reset_input_buffer()
    #arduino.reset_output_buffer()
    time.sleep(3)
    arduino.write(str(choice) + "\n")
    #time.sleep(3)
    while True:
        #print "whil1 1"
        time.sleep(2)

        data = arduino.readline()[:-2]
        #print "data is ", data
        if data.strip() == str(choice):
            break

    data = arduino.readline()[:-2]
    while not data:
        #print "whil1 2"
        time.sleep(0.1)
        data = arduino.readline()[:-2]
        #print "read line pased"

    if data:
        try:
            data_in_float = float(data)
            data_in_int = int(data_in_float)
        except:
            return -1
        if choice == 1:
            return data_in_int / 100, data_in_int % 100;
        else:
            return data_in_float
    else:
        return -1

'''
while True:
    # read_arduino(-1)
    timestamp = int(time.time())
    # latti, longi = gps.read()
    latti, longi = 10, 10
    print int(time.time()), "STARTED"
    s0_temp = read_arduino(1)[0]
    s1_hum =  read_arduino(1)[1]
    s2_ch4_ppm = read_arduino(2)
    s3_lpg_ppm = read_arduino(3)
    s4_co2_ppm = read_arduino(4)
    s5_dust_raw = read_arduino(5)
    s6_ch4_raw = read_arduino(6)
    s7_lpg_raw = read_arduino(7)
    s8_co2_raw = read_arduino(8)
    print int(time.time()), "READ ENDED"
    new_row = (timestamp, latti, longi, s0_temp,
               s1_hum, s2_ch4_ppm, s3_lpg_ppm, s4_co2_ppm, s5_dust_raw, s6_ch4_raw, s7_lpg_raw, s8_co2_raw)
    # with open('data2.csv', 'a') as f:
    #        writer = csv.writer(f)
    #        writer.writerow(new_row)

    print 'Timestamp: {}, Longitude: {}, Latitude: {}, Temp: {}, Humidity: {}, CH4: {} ppm, LPG: {} ppm, CO2: {} ppm, Dust: {} (ADC), CH4: {} (ADC) LPG: {} (ADC), CO2: {} (ADC)'.format(timestamp, longi, latti, s0_temp, s1_hum, s2_ch4_ppm, s3_lpg_ppm, s4_co2_ppm, s5_dust_raw, s6_ch4_raw, s7_lpg_raw, s8_co2_raw)
    time.sleep(1) '''

