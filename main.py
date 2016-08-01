import Queue
import time
from cpconsole import CpConsole
from cpmodem import CpModem
from cpcomm import CpComm
#import Adafruit_BBIO.UART as UART
#import Adafruit_BBIO.GPIO as GPIO
import wiringpi as GPIO

from datetime import datetime

class CpGpioMap():

    GPIO_CELLENABLE = 17
    GPIO_CELLRESET = 6
    GPIO_CELLONOFF = 5
    GPIO_CELLPWRMON = 26
    GPIO_LED1 = 23
    GPIO_LED2 = 24
#
#class CpGpioMap():
#    GPIO_CELLENABLE = "P9_12"
#    GPIO_CELLRESET = "P9_23"
#    GPIO_CELLONOFF = "P8_12"
#    GPIO_CELLPWRMON = "P9_42"
    

def modemDataReceived(data):
    print 'Callback function modemDataReceived ', data
    
def rfDataReceived(data):
    print 'Callback function rfDataReceived ', data
    
def inetDataReceived(data):
    print 'Callback function inetDataReceived ', data

    
# !!! This method must be called before creating the modem object !!!
def modem_init():




    #print 'Setting up UART1...'
    #UART.setup("UART1")
    #print 'Setting up UART2...'
    #UART.setup("UART2")
    #print 'Setting up UART4...'
    #UART.setup("UART4")

    device = "/dev/ttyAMA0"
    #GPIO.Serial(device, 115200)

    print 'Initializing GPIO(s)'

    GPIO.pinMode(CpGpioMap.GPIO_CELLENABLE, GPIO.OUTPUT)
    GPIO.pinMode(CpGpioMap.GPIO_CELLRESET, GPIO.OUTPUT)
    GPIO.pinMode(CpGpioMap.GPIO_CELLONOFF, GPIO.OUTPUT)
    GPIO.pinMode(CpGpioMap.GPIO_CELLPWRMON, GPIO.INPUT)

    GPIO.digitalWrite(CpGpioMap.GPIO_CELLENABLE, GPIO.GPIO.LOW)
    GPIO.digitalWrite(CpGpioMap.GPIO_CELLRESET, GPIO.GPIO.LOW)
    GPIO.digitalWrite(CpGpioMap.GPIO_CELLONOFF, GPIO.GPIO.LOW)

    
   # while True:
   #     if GPIO.digitalRead(CpGpioMap.GPIO_CELLPWRMON):
   #         print "GPIO_CELLPWRMON=LOW"
   #         break
   #     else:
   #         GPIO.digitalWrite(CpGpioMap.GPIO_CELLENABLE, GPIO.GPIO.HIGH)
   #         time.sleep(.01) # 10ms
   #         GPIO.digitalWrite(CpGpioMap.GPIO_CELLENABLE, GPIO.GPIO.LOW)
   #         time.sleep(.002) # 2ms
            
    while True:
        print "TOGGLE GPIO_CELLONOFF:HIGH wait 3 sec."
        GPIO.digitalWrite(CpGpioMap.GPIO_CELLONOFF, GPIO.GPIO.HIGH)
        time.sleep(3)
        print "TOGGLE GPIO_CELLONOFF:LOW wait 2 sec."
        GPIO.digitalWrite(CpGpioMap.GPIO_CELLONOFF, GPIO.GPIO.LOW)
        time.sleep(2)
        if GPIO.digitalRead(CpGpioMap.GPIO_CELLPWRMON):
            print "GPIO_CELLPWRMON=HIGH"
            break
        
    print 'Modem Initialized'
    
if __name__ == '__main__':

    GPIO.wiringPiSetupGpio()

    #GPIO.pinMode(23, GPIO.OUTPUT)
    
    #while True:
    #    GPIO.digitalWrite(23, GPIO.GPIO.LOW)
    #    time.sleep(1)
    #    GPIO.digitalWrite(23, GPIO.GPIO.HIGH)
    #    time.sleep(1)
    #    print "toggle led"

    
    modem_init()
   
    print "Modem init complete!"

    #while(True):
    #    time.sleep(1)
    #    print "running..."

    #exit()

    device = '/dev/ttyAMA0'


    modemThread = CpModem(modemDataReceived)
    modemThread.start()
    
    commThread = CpComm(modemThread)
    commThread.start()
    
    consoleThread = CpConsole(modemThread, commThread)
    consoleThread.start()
    

    
    while(consoleThread.isAlive()):
        '''
        if (modemThread.data_buffer.qsize() > 0):
            modem_command = modemThread.data_buffer.get(True)
            modemThread.data_buffer.task_done()
            print 'modem response', modem_command
        '''
        time.sleep(.005)

    print 'Exiting App...'
    print 'Exiting App...'
    exit()
    
    


