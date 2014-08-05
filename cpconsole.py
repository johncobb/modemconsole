import threading
import time
import Queue

class CpConsole(threading.Thread):
    
    def __init__(self, modem, comm, *args):
        self._target = self.console_handler
        self._args = args
        self.__lock = threading.Lock()
        self.closing = False # A flag to indicate thread shutdown
        self.modem = modem
        self.comm = comm
        threading.Thread.__init__(self)
        
    def run(self):
        self._target(*self._args)
    
    def comm_callback_handler(self, result):
        print "comm_callback_handler ", result
        
    def shutdown_thread(self):
        print 'shutting down CpConsole...'
        self.modem.shutdown_thread()
        self.comm.shutdown_thread()
            
        while(self.modem.isAlive()):
            print 'waiting for CpModem shutdown isAlive=', self.modem.isAlive()
            time.sleep(.5)

        while(self.comm.isAlive()):
            print 'waiting for CpComm shutdown isAlive=', self.comm.isAlive()
            time.sleep(.5)
        
        print 'waiting for CpModem shutdown isAlive=', self.modem.isAlive()
        print 'waiting for CpComm shutdown isAlive=', self.comm.isAlive()

        self.__lock.acquire()
        self.closing = True
        self.__lock.release()
        
    def console_handler(self):
        
        input=1
        while not self.closing:
            # get keyboard input
            input = raw_input(">> ")
                # Python 3 users
                # input = input(">> ")
            if input == 'exit' or input == 'EXIT':
                self.shutdown_thread()
            else:
                cmd = "%s\r" % input
                self.modem.enqueue_command(cmd)
                #self.taskMgr.enqueue_command(input)
            '''
            elif input == 'commat':
                self.comm.comm_at()
            elif input == 'commcfg':
                self.comm.comm_config()
            elif input == 'commcnx':
                self.comm.comm_connect()
            elif input == 'commres':
                self.comm.comm_resume()
            elif input == 'commsus':
                self.comm.comm_suspend()
            elif input == 'commclose':
                self.comm.comm_close()
            elif input == 'commhttp':
                self.comm.comm_http()
            elif input == 'commpost':
                self.comm.comm_post()
            elif input == 'commsend':
                self.comm.comm_send()
            elif input == '+++':
                self.modem.enqueue_command("+++")
            else:
                cmd = "%s\r" % input
                self.modem.enqueue_command(cmd)
                #self.taskMgr.enqueue_command(input)
            '''
                
            time.sleep(.0001)