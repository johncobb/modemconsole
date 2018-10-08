import Queue
import time
from cpconsole import CpConsole
from cpmodem import CpModem
from cpcomm import CpComm
from datetime import datetime

from lib_module_lara_r2 import *



def modemDataReceived(data):
    print 'Callback function modemDataReceived ', data
    
def inetDataReceived(data):
    print 'Callback function inetDataReceived ', data

    
# !!! This method must be called before creating the modem object !!!
def modem_init():

    u = UbloxLaraR2()
    u.initialize()
    u.reset_power()
    device = "/dev/ttyAMA0"
   


if __name__ == '__main__':

    device = '/dev/ttyAMA0'
    modem_init()



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


