
import os, sys
import time
import serial
import RPi.GPIO as GPIO


class TelitGpio():
    GPIO_CELLENABLE = 17
    GPIO_CELLRESET = 6
    GPIO_CELLONOFF = 5
    GPIO_CELLPWRMON = 26
    GPIO_LED1 = 23
    GPIO_LED2 = 24


class Telit():
    def __init__(self, port='/dev/ttyAMA0', baudrate=115200):
        self.debug = True
        self.comm = serial.Serial(port, baudrate)

    def __del__(self):
        #self.disable_rtscts()
        pass


    def initialize(self):
        GPIO.setmode(GPIO.BOARD)
        GPIO.setwarnings(False)
        '''
        GPIO.setup(UbloxGpioMap.GPIO_POWERPIN, GPIO.OUT)
        GPIO.setup(UbloxGpioMap.GPIO_RESETPIN, GPIO.OUT)
        GPIO.output(UbloxGpioMap.GPIO_POWERPIN, False)
        GPIO.output(UbloxGpioMap.GPIO_RESETPIN, False)
        self.enable_rtscts()
        '''

        GPIO.pinMode(TelitGpio.GPIO_CELLENABLE, GPIO.OUTPUT)
        GPIO.pinMode(TelitGpio.GPIO_CELLRESET, GPIO.OUTPUT)
        GPIO.pinMode(TelitGpio.GPIO_CELLONOFF, GPIO.OUTPUT)
        GPIO.pinMode(TelitGpio.GPIO_CELLPWRMON, GPIO.INPUT)

        GPIO.digitalWrite(CpGpioMap.GPIO_CELLENABLE, GPIO.GPIO.LOW)
        GPIO.digitalWrite(CpGpioMap.GPIO_CELLRESET, GPIO.GPIO.LOW)
        GPIO.digitalWrite(CpGpioMap.GPIO_CELLONOFF, GPIO.GPIO.LOW)

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
