import io
import re
import time
import logger
import queue as q
import threading

from grbl import device as d
from grbl import nudger as n

logging = logger.Logger()


# Singleton GRBL controller that handles all reads and writes to and from the serial device.
#
# The controller makes use of a streaming queues and realtime queues (both for requests/responses) to
# help buffer against direct access to the GRBL controller, which has a limited and idiosyncratic request and response buffer,
# and to resolve potential concurrency problems. This helps enhance flow control.
class Controller:
    instance = None
    rq = None
    rrq = None
    sq = None
    srq = None
    lock = None
    realtime_thread = None
    paused = None
    device = None
    nudger = None

    def __new__(self):
        if self.instance is None:
            self.instance = super().__new__(self)

            self.device = d.Device() # serial device singleton
            self.nudger = n.Nudger() # helps prevent controller stalling and monitors for long-running operations

            self.rq = q.Queue()  # realtime queue (for realtime commands that need to execute immediately)
            self.rrq = q.Queue() # realtime response queue

            self.sq = q.Queue()  # streaming queue (for longer standing streaming gcode thru)
            self.srq = q.Queue() # streaming response queue

            self.lock = threading.Lock()
            self.write_condition = threading.Condition()

            self.connected = False
            self.trying = False
            self.paused = False
            self.resetting = False

            self.realtime_thread = threading.Thread(target=self.realtime)

        return self.instance

    def start(self):
        if not hasattr(self, 'write_thread') or not self.write_thread.is_alive():
            self.write_thread = threading.Thread(target=self.realtime)
            self.write_thread.start()

    def set(self, device_path):
        self.device.set(device_path)

    def write(self, serialbytes):
        self.sq.put(serialbytes)

    def realtime_write(self, serialbytes):
        self.rq.put(serialbytes)

    def readline(self):
        return self.srq.get()

    def realtime_readline(self):
        return self.rrq.get()

    def unlock(self):
        self.realtime_write(b'$X\n')
        self.realtime_message()

    # induces an immediate GRBL hold state
    def stop(self):
        command = b'!'
        self.device.write(command) # critially requires a direct write to effect the command immediately
        self.paused = True
        logging.info('[ hc ] ' + command.decode() + ' ok')

    # resumes from GRBL hold state
    def resume(self):
        command = b'~'
        self.device.write(command) # critially requires a direct write to effect the command immediately
        self.paused = False
        logging.info('[ hc ] ' + command.decode() + ' ok')

    # returns GRBL status
    def status(self):
        self.realtime_write(b'?')
        self.realtime_message()

    def realtime_message(self):
        while self.rrq.empty():
            time.sleep(0.01)

        while not self.rrq.empty():
            response = self.realtime_readline()
            rs = response.decode()

            logging.info(rs)

            if response.find(b'error') >= 0:
                logging.info("[ hc ] " + rs + " " + error.messages[rs])

            time.sleep(0.01)

    # attempts to connect to a serial device to wake up a GRBL controller
    def connect(self, device_path):
        self.connected = False
        self.trying = True

        self.set(device_path)
        logging.info("[ hc ] wake up grbl...")
        self.abort()
        time.sleep(0.5)

        #bline = b'\r\n\r\n'
        bline = b'\x18'
        self.realtime_write(bline)
        time.sleep(2)

        while not self.rrq.empty():
            response = self.rrq.get()
            logging.info(response.decode())

            if response.find(b'Grbl') >= 0:
                self.connected = True

        if self.connected:
            self.realtime_write(b'$$\n')
            self.realtime_write(b'$I\n')
            self.realtime_write(b'$G\n')
            time.sleep(1)

            while not self.rrq.empty():
                response = self.rrq.get()
                logging.info(response.decode())
        else:
            self.abort()
            self.device.close()
            time.sleep(1)

        self.trying = False
        return self.connected

    # reset remains a direct write to the device to ensure there's no unexpected wait time for soft reset execution.
    def reset(self):
        try:
            self.resetting = True
            self.abort()
            self.nudger.terminate = True

            bline = b'\x18'
            self.device.write(bline)
            time.sleep(2)

            while self.device.in_waiting() > 0:
                response = self.device.readline().strip()
                logging.info(response.decode())
        finally:
            self.resetting = False

    def disconnect(self):
        self.abort()
        self.nudger.terminate = True
        self.connected = False
        self.device.close()

    # sends commands to the grbl read buffer and reads responses.
    # this is the only method that should read/write directly from/to serial grbl.
    def realtime(self):
        try:
            while True:
                if (self.connected or self.trying) and not self.resetting:

                    # Process real-time commands in priority
                    while not self.rq.empty():
                        command = self.rq.get().upper().strip()
                        self.handle_command(command, self.rrq)

                    # Process streaming commands if not paused
                    if not self.sq.empty() and not self.paused:
                        command = self.sq.get().strip()
                        self.handle_command(command, self.srq)

                time.sleep(0.01)
        except TypeError:
            logging.error("[ hc ] unable to communicate over serial port. not a GRBL serial device?")
        except OSError as ose:
            pass
            #logging.info("[ hc ] unable to communicate over serial port: " + str(ose))
        except Exception as e:
            pass

    def handle_command(self, command, response_queue):
        if not (command in {b'!', b'~', b'?'}):
            command += b'\n'

        self.device.write(command)

        if command not in {b'!', b'~'}:
            self.nudger.wait()

            while self.device.in_waiting() > 0:
                bline = self.device.readline().strip()
                if not self.nudger.nudged_response(bline):
                    response_queue.put(b'[ ' + command.strip() + b' ] ' + bline)
                time.sleep(0.01)
        else:
            if command == b'!':
                self.paused = True
            elif command == b'~':
                self.paused = False
            response_queue.put(b'[ hc ] ' + command + b' ok')

    # reports on controller nudging for long-running commands (e.g. $H)
    def nudging(self):
        return self.nudger.nudging

    def abort(self):
        self.rq.queue.clear()
        self.rrq.queue.clear()
        self.sq.queue.clear()
        self.srq.queue.clear()
        self.device.abort()
        self.paused = False
