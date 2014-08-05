import Queue
import time
from cpconsole import CpConsole
from cpmodem import CpModem
from cpcomm import CpComm
import Adafruit_BBIO.UART as UART
import Adafruit_BBIO.GPIO as GPIO

from datetime import datetime


class CpGpioMap():
    GPIO_CELLENABLE = "P9_12"
    GPIO_CELLRESET = "P9_23"
    GPIO_CELLONOFF = "P8_12"
    GPIO_CELLPWRMON = "P9_42"
    

def modemDataReceived(data):
    print 'Callback function modemDataReceived ', data
    
def rfDataReceived(data):
    print 'Callback function rfDataReceived ', data
    
def inetDataReceived(data):
    print 'Callback function inetDataReceived ', data

    
# !!! This method must be called before creating the modem object !!!
def modem_init():

    print 'Setting up UART1...'
    UART.setup("UART1")
    print 'Setting up UART2...'
    UART.setup("UART2")
    print 'Setting up UART4...'
    UART.setup("UART4")

    print 'Initializing GPIO(s)'
    
    GPIO.setup(CpGpioMap.GPIO_CELLENABLE, GPIO.OUT) #CELL_ENABLE
    GPIO.setup(CpGpioMap.GPIO_CELLRESET, GPIO.OUT) #CELL_RESET
    GPIO.setup(CpGpioMap.GPIO_CELLONOFF, GPIO.OUT) #CELL_ONOFF
    GPIO.setup(CpGpioMap.GPIO_CELLPWRMON, GPIO.IN) #CELL_PWRMON
    
    GPIO.output(CpGpioMap.GPIO_CELLENABLE, GPIO.LOW)
    GPIO.output(CpGpioMap.GPIO_CELLRESET, GPIO.LOW)
    GPIO.output(CpGpioMap.GPIO_CELLONOFF, GPIO.LOW)
    
    while True:
        if GPIO.input(CpGpioMap.GPIO_CELLPWRMON):
            print "GPIO_CELLPWRMON=LOW"
            break
        else:
            GPIO.output(CpGpioMap.GPIO_CELLENABLE, GPIO.HIGH)
            time.sleep(.01) # 10ms
            GPIO.output(CpGpioMap.GPIO_CELLENABLE, GPIO.LOW)
            time.sleep(.002) # 2ms
            
    while True:
        print "TOGGLE GPIO_CELLONOFF:HIGH wait 3 sec."
        GPIO.output(CpGpioMap.GPIO_CELLONOFF, GPIO.HIGH)
        time.sleep(3)
        print "TOGGLE GPIO_CELLONOFF:LOW wait 2 sec."
        GPIO.output(CpGpioMap.GPIO_CELLONOFF, GPIO.LOW)
        time.sleep(2)
        if GPIO.input(CpGpioMap.GPIO_CELLPWRMON):
            print "GPIO_CELLPWRMON=HIGH"
            break
        
    print 'Modem Initialized'
    
if __name__ == '__main__':
    
    modem_init()
    
    #device = '/dev/tty.usbserial-FTELSNMW'

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
    exit()
    
    


    
