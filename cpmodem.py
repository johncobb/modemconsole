import threading
import time
import Queue
import serial
from cpdefs import CpDefs
from datetime import datetime
#import Adafruit_BBIO.UART as UART
#import Adafruit_BBIO.GPIO as GPIO

class CpModemResultCode:
    RESULT_UNKNOWN = 0
    RESULT_OK = 1
    RESULT_ERROR = 2
    RESULT_CONNECT = 3
    RESULT_NOCARRIER = 4
    RESULT_PROMPT = 5
    RESULT_CMGS = 6
    RESULT_CREG = 7
    RESULT_MONI = 8
    RESULT_SGACT = 9
    RESULT_ACK = 10
    RESULT_CMGL = 11
    RESULT_CMGR = 12
    RESULT_HTTPOK = 13
    RESULT_TIMEOUT = 14
    
class CpModemResponses:
    TOKEN_OK = "OK"
    TOKEN_ERROR = "ERROR"
    TOKEN_CONNECT = "CONNECT"
    TOKEN_NOCARRIER = "NO CARRIER"
    TOKEN_PROMPT = ">"
    TOKEN_CMGS = "+CMGS:"
    TOKEN_CREG = "+CREG:"
    TOKEN_MONI = "#MONI:"
    TOKEN_SGACT = "#SGACT:"
    TOKEN_ACK = "ACK"
    TOKEN_CMGL = "+CMGL:"
    TOKEN_CMGR = "+CMGR:"
    TOKEN_HTTPOK = "HTTP/1.1 200 OK"
    
      
    
class CpModemDefs:
    CMD_CTLZ = 0x1b
    CMD_ESC = 0x1a
    CMD_UDPESC = "+++"
    CMD_AT = "AT\r"
    CMD_SETECHOOFF = "ATE0\r"
    CMD_SELINT = "AT#SELINT=2\r"
    CMD_SETMSGFMT = "AT+CMGF=1\r"
    CMD_SETBAND = "AT#BND=1\r"    # 850/1900 default
    #CMD_SETCONTEXT = "AT+CGDCONT=1,\"IP\",\"c1.korem2m.com\"\r"
    CMD_SETCONTEXT = "AT+CGDCONT=1,\"IP\",\"%s\"\r"
    CMD_SETUSERID = "AT#USERID=\"%s\"\r"
    CMD_SETPASSWORD = "AT#PASSW=\"%s\"\r"
    CMD_SETSKIPESC = "AT#SKIPESC=1\r"
    CMD_SETSKTCFG = "AT#SCFG=1,1,512,90,600,2\r"
    CMD_SETAUTOCTX = "AT#SGACTCFG=1,3\r"
    CMD_SETACTCTX = "AT#SGACT=1,1\r"
    CMD_SETDACTCTX = "AT#SGACT=1,0\r"
    CMD_SETMONI = "AT#MONI\r"
    CMD_SETFACTRST = "AT&F\r"
    CMD_QRYCTX = "AT#SGACT?\r"
    CMD_QRYSIG = "AT+CSQ?\r"
    CMD_QRYNET = "AT+CREG?\r"
    #CMD_SKTDIAL = "AT#SD=1,0,80,\"voidworx.com\",0,0\r"
    CMD_SKTDIAL = "AT#SD=1,0,%s,\"%s\",0,0\r"
    CMD_SKTESC = "+++"
    CMD_SKTRESUME = "AT#SO=1\r"
    CMD_SKTCLOSE = "AT#SH=1\r"
    CMD_HTTP = "GET /pings HTTP/1.1\r\nHost: voidworx.com\r\nConnection: keep-alive\r\n\r\n"
    #CMD_HTTPPOST = "POST %s HTTP/1.1\r\ncontent-type:application/x-www-form-urlencoded;charset=utf-8\r\nhost: %s\r\ncontent-length:%d\r\n\r\n%s"
    CMD_HTTPPOST = "POST %s HTTP/1.1\r\ncontent-type:application/json\r\nhost: %s\r\ncontent-length:%d\r\n\r\n%s"


class CpModemResult:
    ResultCode = 0
    Data = ""
    
    
class CpModem(threading.Thread):
    
    def __init__(self, modemResponseCallbackFunc=None, *args):
        self._target = self.modem_handler
        self._args = args
        self.__lock = threading.Lock()
        self.closing = False # A flag to indicate thread shutdown
        self.commands = Queue.Queue(5)
        self.data_buffer = Queue.Queue(128)
        self.modem_timeout = 0
        self.modemResponseCallbackFunc = modemResponseCallbackFunc
        self.modemBusy = False
        self.modemResult = CpModemResult()
        self.modemToken = ""
        #self.data_buffer = ""
        #self.ser = serial.Serial(device, baudrate=115200, parity='N', stopbits=1, bytesize=8, xonxoff=0, rtscts=0)
        self.ser = serial.Serial(CpDefs.ModemPort, baudrate=CpDefs.ModemBaudrate, parity='N', stopbits=1, bytesize=8, xonxoff=0, rtscts=0)
        threading.Thread.__init__(self)
        
        # Note modem_set_autoctctx can be tricky when trying to call activate context
        # Activate context will throw an error if modem_set_activatecontext is called manually
        self.fmap = {0:self.modem_set_echo_off,
                     1:self.modem_set_interface,
                     2:self.modem_set_msg_format,
                     3:self.modem_set_band,
                     4:self.modem_set_context,
                     5:self.modem_set_user_id,
                     6:self.modem_set_password,
                     7:self.modem_set_skipescape,
                     8:self.modem_set_socket_config,
                     9:self.modem_set_autoactctx,
                     10:0}
        
    def run(self):
        self._target(*self._args)
        
    def shutdown_thread(self):
        print 'shutting down CpModem...'
        self.__lock.acquire()
        self.closing = True
        self.__lock.release()
        if(self.ser.isOpen()):
            self.ser.close()
    
    def modem_send(self, cmd):
        print 'sending modem command ', cmd
        #self.__lock.acquire()
        #self.ser.write(cmd + '\r')
        self.ser.write(cmd)
        #self.__lock.release()
    
    
    def modem_handler(self):
        tmp_buffer = ""
        
        if(self.ser.isOpen()):
            self.ser.close()
        
        self.ser.open()
        
        while not self.closing:
            
            if (self.commands.qsize() > 0):
                modem_command = self.commands.get(True)
                self.commands.task_done()
                self.modem_send(modem_command)
                continue
            
            #if(self.ser.outWaiting() > 0):
                #print 'modem.outWaiting=', self.ser.outWaiting()
            
            #self.__lock.acquire()
            while(self.ser.inWaiting() > 0):
                #print 'modem has data!!!'
                tmp_char = self.ser.read(1)
                if(tmp_char == '\r'):
                    #self.data_buffer.put(tmp_buffer, block=True, timeout=1)
                    result = self.modem_parse_result(tmp_buffer)
                    print 'received ', tmp_buffer
                    # Make sure we received something worth processing
                    if(result.ResultCode > CpModemResultCode.RESULT_UNKNOWN):
                        #print 'known result code', result
                        if(self.modemResponseCallbackFunc != None):
                            self.modemResponseCallbackFunc(result)
                            self.modemBusy = False
                    #print 'modem response ', tmp_buffer
                    tmp_buffer= ""
                else:
                    tmp_buffer += tmp_char
            #self.__lock.release()
            time.sleep(.005)
                    
                    
    def enqueue_command(self, cmd):
        try:
            self.modemBusy = True
            self.commands.put(cmd, block=True, timeout=1)
        except:
            self.__lock.acquire()
            print "The queue is full"
            self.__release()
            
    modemTimeout = 0
    
    def set_timeout(self, timeout):
        self.modem_timeout = datetime.now() + timeout
    
    def is_timeout(self):
        if(datetime.now() >= self.modem_timeout):
            return True
        else:
            return False
    
    def is_error(self, token):        
        if(token.find(CpModemResponses.TOKEN_ERROR) > -1):
            return True
        else:
            return False
        
    def modem_parse_result(self, result):
        
        modem_result = CpModemResult()
        
        if(result.find(CpModemResponses.TOKEN_OK) > -1):
            modem_result.Data = result
            modem_result.ResultCode = CpModemResultCode.RESULT_OK
        elif(result.find(CpModemResponses.TOKEN_ERROR) > -1):
            modem_result.Data = result
            modem_result.ResultCode = CpModemResultCode.RESULT_ERROR
        elif(result.find(CpModemResponses.TOKEN_CONNECT) > -1):
            modem_result.Data = result
            modem_result.ResultCode = CpModemResultCode.RESULT_CONNECT   
        elif(result.find(CpModemResponses.TOKEN_NOCARRIER) > -1):
            modem_result.Data = result
            modem_result.ResultCode = CpModemResultCode.RESULT_NOCARRIER
        elif(result.find(CpModemResponses.TOKEN_PROMPT) > -1):
            modem_result.Data = result
            modem_result.ResultCode = CpModemResultCode.RESULT_PROMPT
        elif(result.find(CpModemResponses.TOKEN_CMGS) > -1):
            modem_result.Data = result
            modem_result.ResultCode = CpModemResultCode.RESULT_CMGS
        elif(result.find(CpModemResponses.TOKEN_CREG) > -1):
            modem_result.Data = result
            modem_result.ResultCode = CpModemResultCode.RESULT_CREG
        elif(result.find(CpModemResponses.TOKEN_MONI) > -1):
            modem_result.Data = result
            modem_result.ResultCode = CpModemResultCode.RESULT_MONI
        elif(result.find(CpModemResponses.TOKEN_SGACT) > -1):
            modem_result.Data = result
            modem_result.ResultCode = CpModemResultCode.RESULT_SGACT
        elif(result.find(CpModemResponses.TOKEN_ACK) > -1):
            modem_result.Data = result
            modem_result.ResultCode = CpModemResultCode.RESULT_ACK
        elif(result.find(CpModemResponses.TOKEN_CMGL) > -1):
            modem_result.Data = result
            modem_result.ResultCode = CpModemResultCode.RESULT_CMGL
        elif(result.find(CpModemResponses.TOKEN_CMGR) > -1):
            modem_result.Data = result
            modem_result.ResultCode = CpModemResultCode.RESULT_CMGR
        elif(result.find(CpModemResponses.TOKEN_HTTPOK) > -1):
            modem_result.Data = result
            modem_result.ResultCode = CpModemResultCode.RESULT_HTTPOK 
        else:
            modem_result.Data = result
            modem_result.ResultCode = CpModemResultCode.RESULT_UNKNOWN
                
        return modem_result
            
    
    def modem_init(self):
        pass
        '''
        print 'Setting up UART1...'
        UART.setup("UART1")
        print 'Setting up UART2...'
        UART.setup("UART2")
        print 'Setting up UART4...'
        UART.setup("UART4")
        print 'Setting up UART5...'
        UART.setup("UART5")
        
    
        print 'Initializing GPIO(s)'
        
        GPIO.setup("P9_12", GPIO.OUT) #CELL_ENABLE
        GPIO.setup("P9_23", GPIO.OUT) #CELL_RESET
        GPIO.setup("P8_12", GPIO.OUT) #CELL_ONOFF
        
        GPIO.output("P9_12", GPIO.LOW)
        GPIO.output("P9_23", GPIO.LOW)
        GPIO.output("P8_12", GPIO.LOW)
        
        time.sleep(3)
        
        print 'Setting CELL_ON/OFF HIGH'
        GPIO.output("P8_12", GPIO.HIGH)
        time.sleep(5)
        print 'Wait (5)s...'
        print 'Setting CELL_ON/OFF LOW'
        GPIO.output("P8_12", GPIO.LOW)
        '''
    
    def modem_reset(self):
        
        '''
        print 'Setting CELL_ON/OFF HIGH'
        GPIO.output("P8_12", GPIO.HIGH)
        time.sleep(5)
        print 'Wait (5)s...'
        print 'Setting CELL_ON/OFF LOW'
        GPIO.output("P8_12", GPIO.LOW)
        '''

 
    def modem_send_at(self, callback):
        self.enqueue_command(CpModemDefs.CMD_AT)
        self.modemResponseCallbackFunc = callback
        pass



    def modem_set_echo_off(self, callback):
        self.enqueue_command(CpModemDefs.CMD_SETECHOOFF)
        self.modemResponseCallbackFunc = callback
        pass
        
    def modem_set_interface(self, callback):
        self.enqueue_command(CpModemDefs.CMD_SELINT)
        self.modemResponseCallbackFunc = callback
        pass
        
    def modem_set_msg_format(self, callback):
        self.enqueue_command(CpModemDefs.CMD_SETMSGFMT)
        self.modemResponseCallbackFunc = callback
        pass
    
    def modem_set_band(self, callback):
        self.enqueue_command(CpModemDefs.CMD_SETBAND)
        self.modemResponseCallbackFunc = callback
        pass 
        
    def modem_set_context(self, callback):
        cmd = CpModemDefs.CMD_SETCONTEXT % (CpDefs.Apn)
        self.enqueue_command(cmd)
        self.modemResponseCallbackFunc = callback
        pass   
        
    def modem_set_user_id(self, callback):
        cmd = CpModemDefs.CMD_SETUSERID % (CpDefs.ApnUserid)
        self.enqueue_command(cmd)
        self.modemResponseCallbackFunc = callback
        pass
        
    def modem_set_password(self, callback):
        cmd = CpModemDefs.CMD_SETPASSWORD % (CpDefs.ApnPassword)
        self.enqueue_command(cmd)
        self.modemResponseCallbackFunc = callback
        pass
        
    def modem_set_skipescape(self, callback):
        self.enqueue_command(CpModemDefs.CMD_SETSKIPESC)
        self.modemResponseCallbackFunc = callback
        pass   
        
    def modem_set_socket_config(self, callback):
        self.enqueue_command(CpModemDefs.CMD_SETSKTCFG)
        self.modemResponseCallbackFunc = callback
        pass
        
    def modem_set_autoactctx(self, callback):
        self.enqueue_command(CpModemDefs.CMD_SETAUTOCTX)
        self.modemResponseCallbackFunc = callback
        pass
    
    def modem_set_activatecontext(self, callback):
        self.enqueue_command(CpModemDefs.CMD_SETACTCTX)
        self.modemResponseCallbackFunc = callback
        pass 
    
    def modem_set_deactivatecontext(self, callback):
        self.enqueue_command(CpModemDefs.CMD_SETDACTCTX)
        self.modemResponseCallbackFunc = callback
        pass 
    
    def modem_qry_context(self, callback):
        self.enqueue_command(CpModemDefs.CMD_QRYCTX)
        self.modemResponseCallbackFunc = callback
        pass  
    
    def modem_qry_signal(self, callback):
        self.enqueue_command(CpModemDefs.CMD_QRYSIG)
        self.modemResponseCallbackFunc = callback
        pass   
    
    def modem_qry_network(self, callback):
        self.enqueue_command(CpModemDefs.CMD_QRYNET)
        self.modemResponseCallbackFunc = callback
        pass   
    
    def modem_set_factoryreset(self, callback):
        self.enqueue_command(CpModemDefs.CMD_SETFACTRST)
        self.modemResponseCallbackFunc = callback
        pass
    
    def modem_set_networkmonitoring(self, callback):
        self.enqueue_command(CpModemDefs.CMD_SETMONI)
        self.modemResponseCallbackFunc = callback
        pass    
    
    def modem_socketdial(self, callback):
        cmd = CpModemDefs.CMD_SKTDIAL % (CpDefs.Port, CpDefs.Server)
        self.enqueue_command(cmd)
        self.modemResponseCallbackFunc = callback
        pass  
   
    def modem_socketsuspend(self, callback):
        self.enqueue_command(CpModemDefs.CMD_SKTESC)
        self.modemResponseCallbackFunc = callback
        pass
     
    def modem_socketresume(self, callback):
        self.enqueue_command(CpModemDefs.CMD_SKTRESUME)
        self.modemResponseCallbackFunc = callback
        pass
    
    def modem_socketclose(self, callback):
        self.enqueue_command(CpModemDefs.CMD_SKTCLOSE)
        self.modemResponseCallbackFunc = callback
        pass  
    
    def modem_sendhttp(self, callback):
        self.enqueue_command(CpModemDefs.CMD_HTTP)
        self.modemResponseCallbackFunc = callback
        pass  
    
    def modem_sendpost(self, callback, data):
        cmd = CpModemDefs.CMD_HTTPPOST % (CpDefs.ServerFolder, CpDefs.Server, len(data), data)
        self.enqueue_command(cmd)
        self.modemResponseCallbackFunc = callback
        pass 
        
        
