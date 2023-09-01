import re
import queue as q
import time
import logger
import queue as q
import error
from functools import partial

from grbl import controller as c
from grbl import nudger as n

logging = logger.Logger()


# Singleton Jogger to track jogging motion. The jogger errs on the side of caution and should stops if it's not getting a heartbeat.
class Jogger:
    instance = None
    heartbeat = None
    is_running = None
    start_time = None
    expire_count = None
    jogger_queue = None
    jog_count = None
    feed = None
    mode = None
    scale = None
    unit = None

    def __new__(self):
        if self.instance is None:

            self.instance = super().__new__(self)
            self.heartbeat = False
            self.controller = c.Controller()
            self.feed = 2000
            self.scale = 3
            self.imperial = 25.4
            self.metric = 1
            self.mode = "continuous"
            self.unit = "imperial"

            self.is_running = False

            self.expire_count = 0
            self.jog_count = 0

            self.jogger_queue = q.Queue()

        return self.instance

    def put(self, boolean):
        self.jogger_queue.put(boolean)
        return

    def empty(self):
        return self.jogger_queue.empty()

    def clear(self):
        return self.jogger_queue.queue.clear()

    def heart(self, heartbeat):
        self.heartbeat = heartbeat
        if self.heartbeat == True:
            logging.debug("[ hc ] true heart")
            self.start_time = time.monotonic()  # Get the current time at the start to evaluate stalling and nudging
            self.expire_count = 0
        elif self.heartbeat == False:
            logging.debug("[ hc ] false heart")
            bline = b'!'
            self.controller.realtime_write(bline)
            self.clear()
            self.jog_count = 0;

    def expire(self):
        if not self.heartbeat == False:
            current_time = time.monotonic()
            elapsed_time = (current_time - self.start_time)

            if elapsed_time >= 1/4:
                self.start_time = time.monotonic()
                self.expire_count += 1
                logging.info("[ hc ] jogger expiration")
                if self.mode == "continuous":
                    self.heart(False)
                self.is_running = False
                self.jog_count = 0;
                self.clear()

    # We intentionally try to expire by default to stop continuous jogging if no heartbeat signal has been received in awhile
    # We want to avoid crashing the CNC by waiting for a positive stop signal.
    def jog(self):
        try:
            self.is_running = True
            self.heartbeat = True

            self.start_time = time.monotonic()  # Get the current time at the start to evaluate stalling and nudging

            line = ""

            # continuous jogging cycle (we actively try to terminate in short order)
            while self.is_running and self.heartbeat == True:
                if not self.jogger_queue.empty():
                    heartbeat = self.jogger_queue.get()
                    self.heart(heartbeat[0])
                    if self.heartbeat == True and self.jog_count == 0:
                        self.jog_count += 1
                        self.controller.realtime_write(heartbeat[1])
                        line = heartbeat[1].decode().strip()
                        logging.info("[ hc ] " + line)

                self.expire()
                time.sleep(0.0001)

            while self.controller.rrq.empty():
                time.sleep(0.02)

            while not self.controller.rrq.empty():
                response = self.controller.realtime_readline().strip()
                rs = response.decode()

                logging.info(rs)

                if rs.find('MSG:Reset') >= 0:
                    raise Exception()

                if error.match(rs):
                    raise Exception()

                time.sleep(0.2)

        except Exception as e:
            self.abort()

    def abort(self):
        self.clear()
        self.controller.reset()
        self.is_running = False

    # real-time jogging by continuously reading the inputstream
    def parse(self, inputstream):
        cases = {
            b'\x1b[D': lambda chunk: self.modal_execute("xleft"),
            b'\x1b[C': lambda chunk: self.modal_execute("xright"),
            b'\x1b[A': lambda chunk: self.modal_execute("yup"),
            b'\x1b[B': lambda chunk: self.modal_execute("ydown"),
            b';':      lambda chunk: self.modal_execute("zup"),
            b'/':      lambda chunk: self.modal_execute("zdown"),
            b'-':      lambda chunk: self.set_feed(-250),
            b'=':      lambda chunk: self.set_feed(250),
            b'[':      lambda chunk: self.set_scale(-1),
            b']':      lambda chunk: self.set_scale(1),
            b's':      lambda chunk: self.jogger_status(),
            b'u':      lambda chunk: self.toggle_unit(),
            b'i':      lambda chunk: self.set_mode("incremental"),
            b'c':      lambda chunk: self.set_mode("continuous")
        }

        for chunk in iter(partial(inputstream.read, 16384), b''):
            logging.debug("[ hc ] chunk " + str(chunk))
            first = chunk[:1]
            if first == b'\x1b':
                action = cases.get(chunk[:3], lambda chunk: None)
            else:
                action = cases.get(chunk[:1], lambda chunk: None)
            action(chunk)

            time.sleep(0.0001)

        return

    #inches (0.001, 0.01, 0.1, 1)
    #$J=G91G21X0.0254F2000
    #$J=G91G21X0.254F2000
    #$J=G91G21X2.54F2000
    #$J=G91G21X25.4F2000

    #mm (0.1, 1, 10, 100)
    #$J=G91G21X0.1F2000
    #$J=G91G21X1F2000
    #$J=G91G21X10F2000
    #$J=G91G21X100F2000
    def modal_execute(self, axis):
        incremental = {
            "xright": b'$J=G91 G21 X' + str(self.conversion()).encode() + b' F' + str(self.feed).encode() + b'\n',
            "xleft" : b'$J=G91 G21 X-' + str(self.conversion()).encode() + b' F' + str(self.feed).encode() + b'\n',
            "yup"   : b'$J=G91 G21 Y' + str(self.conversion()).encode() + b' F' + str(self.feed).encode() + b'\n',
            "ydown" : b'$J=G91 G21 Y-' + str(self.conversion()).encode() + b' F' + str(self.feed).encode() + b'\n',
            "zup"   : b'$J=G91 G21 Z' + str(self.conversion()).encode() + b' F' + str(self.feed).encode() + b'\n',
            "zdown" : b'$J=G91 G21 Z-' + str(self.conversion()).encode() + b' F' + str(self.feed).encode() + b'\n'
        }

        continuous = {
            "xright": b'$J=G91 G21 X1000 F' + str(self.feed).encode() + b'\n',
            "xleft" : b'$J=G91 G21 X-1000 F' + str(self.feed).encode() + b'\n',
            "yup"   : b'$J=G91 G21 Y1000 F' + str(self.feed).encode() + b'\n',
            "ydown" : b'$J=G91 G21 Y-1000 F' + str(self.feed).encode() + b'\n',
            "zup"   : b'$J=G91 G21 Z1000 F' + str(self.feed).encode() + b'\n',
            "zdown" : b'$J=G91 G21 Z-1000 F' + str(self.feed).encode() + b'\n'
        }

        if self.mode == "continuous":
            self.execute(continuous.get(axis))
        elif self.mode == "incremental":
            self.execute(incremental.get(axis))

    def execute(self, gcode):
        if gcode is not None:
            self.put([True, gcode])
        else:
            if self.mode == "continuous":
                self.put([False, b'\n']) 

    def set_mode(self, mode):
        self.mode = mode
        self.jogger_status()
        return self.mode

    def set_feed(self, feed):
        self.feed += feed
        if self.feed > 2000: self.feed = 2000
        if self.feed <= 0: self.feed = 1
        self.jogger_status()
        return self.feed

    def set_scale(self, increment):
        self.scale += increment
        if self.scale < 1: self.scale = 1
        if self.scale > 4: self.scale = 4
        self.jogger_status()
        return self.scale

    def toggle_unit(self):
        if self.unit == "imperial":
            self.unit = "metric"
        elif self.unit == "metric":
            self.unit = "imperial"
        self.jogger_status()
        return

    def conversion(self):
        if self.unit == "imperial":
            result = self.imperial / (10 ** (abs(self.scale - 4)))
        if self.unit == "metric":
            result = self.metric * (10 ** (self.scale - 2))
        return result

    def jogger_status(self):
        logging.info("[ hc ] ------------------------------------------")
        logging.info("[ hc ] jogger mode: " + str(self.mode))
        logging.info("[ hc ] jogger unit: " + str(self.unit))
        logging.info("[ hc ] jogger feed: " + str(self.feed))
        if self.mode == "incremental":
            if self.unit == "imperial":
                logging.info("[ hc ] jogger scale: " + str(10 ** (self.scale - 4)) + "\"")
            elif self.unit == "metric":
                logging.info("[ hc ] jogger scale: " + str(self.metric * (10 ** (self.scale - 2))) + "mm")
