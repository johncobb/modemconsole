import threading
import time
import Queue
from datetime import datetime
from cpmodem import CpModem
from cpmodem import CpModemResponses
from cpmodem import CpModemResult
from cpmodem import CpModemResultCode

class CpStateResult:
    UNKNOWN = 0
    SUCCESS = 1
    TIMEOUT = 2
    ERROR = 3
    

class CpComm(threading.Thread):
    
    def __init__(self, modem, *args):
        self._target = self.comm_handler
        self._args = args
        self.__lock = threading.Lock()
        self.closing = False # A flag to indicate thread shutdown
        self.modem = modem
        self.modemResult = CpModemResult()
        self.STATEFUNC = 0
        self.timestamp = 0
        self.timeout = 0
        self.commCallbackHandler = None
        self.waitForModemCallback = False
        self.CONFIG_INDEX = 0
        threading.Thread.__init__(self)
        
    def run(self):
        self._target(*self._args)
    
    def shutdown_thread(self):
        print 'shutting down CpComm...'
        self.__lock.acquire()
        self.closing = True
        self.__lock.release()
        
    def comm_handler(self):
        while not self.closing:
            if(self.STATEFUNC != 0):
                self.STATEFUNC()
            time.sleep(.0001)
            
    def comm_istimeout(self):
        if((datetime.now() - self.timestamp).seconds < self.timeout):
            return False
        else:
            return True
        
    def comm_enter_state(self, statefunc, timeout):
        self.STATEFUNC = statefunc
        self.timestamp = datetime.now()
        self.timeout = timeout
        
    def comm_exit_state(self):
        self.STATEFUNC = 0
        self.timeout = 0.0
        self.modemResult.Data = ""
        self.modemResult.ResultCode = CpModemResultCode.RESULT_UNKNOWN
        self.commCallbackHandler = None
    
    def comm_timeout(self):
        if((datetime.now() - self.timestamp).seconds >= self.timeout):
            return True
        else:
            return False
        
    global waitForModemCallback
    
    # Initialize the modem and prepare it for communications
    # These are synchronous calls so there is no need to setup callbacks
    def comm_init(self):
        self.modem.modem_init()
        self.modem.modem_reset()
        # Modem has reset so let's try to communicate with it
        self.comm_at()
        pass
    
    # Initialize the modem and prepare it for communications
    # These are synchronous calls so there is no need to setup callbacks
    def comm_reset(self):
        self.modem.modem_reset()
        # Modem has reset so let's try to communicate with it
        self.comm_at()

    # Handle the data passed back from the modem
    # Handler used to trigger the STATEFUNC callback
    # which is waiting for waitForCallback to go False
    def handle_modem_callback(self, result):
        self.modemResult = result
        self.waitForCallback = False
        
    # Handle each tick the thread fires to determine result... 
    # Needs timeout implementation
    def handle_comm_at(self):
        if(self.comm_timeout() == True):
            self.comm_exit_state()
            self.comm_reset()
            return CpStateResult.TIMEOUT
            
        if (self.waitForModemCallback == False):
            if(self.modemResult.ResultCode == CpModemResultCode.RESULT_OK):
                self.comm_exit_state()
                return CpStateResult.SUCCESS
            else:
                self.comm_exit_state()
                return CpStateResult.ERROR
            
        else:
            return CpStateResult.UNKNOWN
        
    
    # Register handle_comm_at for the STATEFUNC to call each pass through the thread
    # Register the handle_modem_callback command so we can process the data
    def comm_at(self):
        self.waitForCallback = True
        self.comm_enter_state(self.handle_comm_at, 2)
        self.modem.modem_send_at(self.handle_modem_callback)

    
    def reset_modem_response_timeout(self):
        pass
    
    def modem_response_timeout(self):
        return False
    
    def handle_comm_modem_response(self, result):
        self.waitForModemCallback = False
        self.modemResult = result
        pass
    
    
    def handle_comm_config(self):
        # See if we're waiting for a response from modem
        if(self.waitForModemCallback == True):
            # Make sure we haven't timed out
            if(self.modem_response_timeout() == True):
                # Timeout occurred so reset the modem
                self.comm_exit_state()
                self.comm_reset()
                return
        
        # We made it this far so we must have a reponse
        if(self.waitForModemCallback == False):
            if(self.modemResult.ResultCode == CpModemResultCode.RESULT_ERROR):
                # We have an error so reset the modem
                print 'Houston we have a problem', self.modemResult
                self.comm_exit_state()
                self.comm_reset()
                return
            
            # The modem responded successfully to our command
            if (self.modemResult.ResultCode == CpModemResultCode.RESULT_OK):
                # Point to the next function in fmap
                self.CONFIG_INDEX += 1
                # Once we reach function 0 we are done so... Bail :)
                if(self.modem.fmap[self.CONFIG_INDEX] == 0):
                    self.comm_exit_state()
                    return
                
                # Otherwise reset the timer and process the next function in fmap
                self.reset_modem_response_timeout()
                self.waitForModemCallback = True
                self.modem.fmap[self.CONFIG_INDEX](self.handle_comm_modem_response)
            
    def comm_config(self):
        # Sanity check
        self.CONFIG_INDEX = 0
        # Go ahead and call the first function in fmap
        self.modem.fmap[self.CONFIG_INDEX](self.handle_comm_modem_response)
        self.comm_enter_state(self.handle_comm_config, 0)
        #self.commCallbackHandler = callback


    
    def comm_connect(self):
        print 'comm_connect'
        self.waitForCallback = True
        self.comm_enter_state(self.handle_comm_connect, 2)
        self.modem.modem_socketdial(self.handle_modem_callback)
        
    def handle_comm_connect(self):
        if(self.comm_timeout() == True):
            self.comm_exit_state()
            self.comm_reset()
            return CpStateResult.TIMEOUT
            
        if (self.waitForModemCallback == False):
            if(self.modemResult.ResultCode == CpModemResultCode.RESULT_CONNECT):
                self.comm_exit_state()
                return CpStateResult.SUCCESS
            else:
                self.comm_exit_state()
                return CpStateResult.ERROR
        else:
            return CpStateResult.UNKNOWN
        
    def comm_suspend(self):
        print 'comm_suspend'
        self.waitForCallback = True
        self.comm_enter_state(self.handle_comm_suspend, 2)
        self.modem.modem_socketsuspend(self.handle_modem_callback)
    
    def handle_comm_suspend(self):
        if(self.comm_timeout() == True):
            self.comm_exit_state()
            self.comm_reset()
            return CpStateResult.TIMEOUT
            
        if (self.waitForModemCallback == False):
            if(self.modemResult.ResultCode == CpModemResultCode.RESULT_OK):
                return CpStateResult.SUCCESS
            else:
                return CpStateResult.ERROR
        else:
            return CpStateResult.UNKNOWN
        
    def comm_resume(self):
        print 'comm_resume'
        self.waitForCallback = True
        self.comm_enter_state(self.handle_comm_resume, 2)
        self.modem.modem_socketresume(self.handle_modem_callback)

    def handle_comm_resume(self):
        if(self.comm_timeout() == True):
            self.comm_exit_state()
            self.comm_reset()
            return CpStateResult.TIMEOUT
            
        if (self.waitForModemCallback == False):
            if(self.modemResult.ResultCode == CpModemResultCode.RESULT_NOCARRIER):
                # We were unable to resume so we need to start with a new connection
                return CpStateResult.ERROR
                
            if(self.modemResult.ResultCode == CpModemResultCode.RESULT_CONNECT):
                return CpStateResult.SUCCESS
            else:
                return CpStateResult.ERROR
        else:
            return CpStateResult.UNKNOWN
        
    def comm_close(self):
        print 'comm_close'
        self.waitForCallback = True
        self.comm_enter_state(self.handle_comm_close, 2)
        self.modem.modem_socketclose(self.handle_modem_callback)
        
    def handle_comm_close(self):
        if(self.comm_timeout() == True):
            self.comm_exit_state()
            self.comm_reset()
            return CpStateResult.TIMEOUT
            
        if (self.waitForModemCallback == False):
            if(self.modemResult.ResultCode == CpModemResultCode.RESULT_OK):
                return CpStateResult.SUCCESS
            else:
                return CpStateResult.ERROR
        else:
            return CpStateResult.UNKNOWN
        
        
    def comm_http(self):
        print 'comm_connect'
        self.waitForCallback = True
        self.comm_enter_state(self.handle_comm_http, 5)
        self.modem.modem_sendhttp(self.handle_modem_callback)
        
    def handle_comm_http(self):
        if(self.comm_timeout() == True):
            self.comm_exit_state()
            self.comm_reset()
            return CpStateResult.TIMEOUT
            
        if (self.waitForModemCallback == False):
            if(self.modemResult.ResultCode == CpModemResultCode.RESULT_CONNECT):
                self.comm_exit_state()
                return CpStateResult.SUCCESS
            else:
                self.comm_exit_state()
                return CpStateResult.ERROR
        else:
            return CpStateResult.UNKNOWN
    
    #packet = "{'shortAddr': 34133, 'extAddr': 34133, 'nodeType': 2, 'temperature': 91, 'softVersion': 16843008, 'battery': 19461, 'light': 15, 'messageType': 1, 'workingChannel': 15, 'lqi': 255, 'rssi': 196, 'parentShortAddr': 0, 'panId': 4660, 'type': 1, 'channelMask': 32768, 'size': 12}"  
    packet = "{\"shortAddr\": 34133, \"extAddr\": 34133, \"nodeType\": 2, \"temperature\": 91, \"softVersion\": 16843008, \"battery\": 19461, \"light\": 15, \"messageType\": 1, \"workingChannel\": 15, \"lqi\": 255, \"rssi\": 196, \"parentShortAddr\": 0, \"panId\": 4660, \"type\": 1, \"channelMask\": 32768, \"size\": 12}"  
    
    def comm_post(self):
        print 'comm_post'
        self.waitForCallback = True
        self.comm_enter_state(self.handle_comm_post, 5)
        self.modem.modem_sendpost(self.handle_modem_callback, self.packet)
        
    def handle_comm_post(self):
        if(self.comm_timeout() == True):
            self.comm_exit_state()
            self.comm_reset()
            return CpStateResult.TIMEOUT
            
        if (self.waitForModemCallback == False):
            if(self.modemResult.ResultCode == CpModemResultCode.RESULT_CONNECT):
                self.comm_exit_state()
                return CpStateResult.SUCCESS
            else:
                self.comm_exit_state()
                return CpStateResult.ERROR
        else:
            return CpStateResult.UNKNOWN
    

    comm_send_index = 0
    
    def comm_send(self):
        print 'comm_connect'
        self.waitForCallback = True
        self.comm_enter_state(self.handle_comm_send, 15) # Note: 15 seconds is a long time to wait
        self.modem.modem_socketdial(self.handle_modem_callback)
        self.comm_send_index = 0
        
        
    def handle_comm_send(self):
        if(self.comm_timeout() == True):
            self.comm_exit_state()
            self.comm_reset()
            return CpStateResult.TIMEOUT
        
            if(self.comm_send_index == 0):
                if (self.waitForModemCallback == False):
                    if(self.modemResult.ResultCode == CpModemResultCode.RESULT_CONNECT):
                        self.modem.modem_sendpost(self.handle_modem_callback, self.packet)
                        self.comm_send_index += 1
                        return CpStateResult.SUCCESS
                    else:
                        self.comm_exit_state()
                        return CpStateResult.ERROR
                else:
                    return CpStateResult.UNKNOWN
            elif(self.comm_send_index == 1):
                    if (self.waitForModemCallback == False):
                        if(self.modemResult.ResultCode == CpModemResultCode.RESULT_OK):
                            self.comm_send_index += 1
                            return CpStateResult.SUCCESS
                        else:
                            self.comm_exit_state()
                            return CpStateResult.ERROR
                    else:
                        return CpStateResult.UNKNOWN
            elif(self.comm_send_index == 2):
                    self.comm_exit_state()
                    return CpStateResult.SUCCESS

