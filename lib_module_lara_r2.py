import os, sys
import time
import serial
import RPi.GPIO as GPIO


class UbloxGpioMap():
    GPIO_POWERPIN = 29
    GPIO_RESETPIN = 31

class UbloxLaraR2():
    def __init__(self, port='/dev/ttyAMA0', baudrate=115200):
        self.debug = True
        self.comm = serial.Serial(port, baudrate)

    def __del__(self):
        #self.disable_rtscts()
        pass


    def initialize(self):
        GPIO.setmode(GPIO.BOARD)
        GPIO.setwarnings(False)
        GPIO.setup(UbloxGpioMap.GPIO_POWERPIN, GPIO.OUT)
        GPIO.setup(UbloxGpioMap.GPIO_RESETPIN, GPIO.OUT)
        GPIO.output(UbloxGpioMap.GPIO_POWERPIN, False)
        GPIO.output(UbloxGpioMap.GPIO_RESETPIN, False)
        self.enable_rtscts()


    def toggle_power_pin(self):
        GPIO.output(UbloxGpioMap.GPIO_POWERPIN, True)
        time.sleep(0.1)
        GPIO.output(UbloxGpioMap.GPIO_POWERPIN, False)

    def enable_rtscts(self):
        os.system("bin/rpirtscts on")

    def disable_rtscts(self):
        os.system("bin/rpirtscts off")

    def reset_power(self):
        self.debug = False
        if self.debug == True:
            print "waking up..."
        sys.stdout.flush()
        self.toggle_power_pin() 


if __name__ == "__main__":
    print "Initializing modem..."
    lara_r2 = UbloxLaraR2("/dev/ttyAMA0", 115200)
    lara_r2.debug = True
    lara_r2.initialize()
    lara_r2.reset_power()
    
