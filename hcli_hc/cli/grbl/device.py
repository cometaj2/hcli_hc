import time
import serial
import logger
import threading

logging = logger.Logger()


# Singleton device for serial port access
class Device:
    instance = None
    rx_buffer_size = 128
    baud_rate = 115200
    device_path = "/dev/tty.usbserial-AR0JI0GV"
    device = None

    def __new__(self):
        if self.instance is None:
            self.instance = super().__new__(self)
            self.instance.lock = threading.Lock()

        return self.instance

    def set(self, device_path):
        with self.lock:
            try:
                self.device_path = device_path.strip('"')
                self.device = serial.Serial(self.device_path, self.baud_rate, timeout=1)
                logging.info("[ hc ] connected to " + self.device_path)
            except:
                logging.info("[ hc ] unable to connect to " + self.device_path)

    def write(self, serialbytes):
        with self.lock:
            self.device.write(serialbytes)

    def readline(self):
        with self.lock:
            return self.device.readline()

    # this is how we should read for buffer data to read per latest version of pyserial (e.g. 3.5).
    def in_waiting(self):
        with self.lock:
            return self.device.in_waiting

    def reset_input_buffer(self):
        with self.lock:
            return self.device.reset_input_buffer()

    def reset_output_buffer(self):
        with self.lock:
            return self.device.reset_output_buffer()

    def close(self):
        with self.lock:
            if self.device:
                result = self.device.close()
                logging.info("[ hc ] disconnected from " + self.device_path)
                return result
            else:
                logging.error("[ hc ] the serial device is unresponsive and can't be used properly. please try to reconnect the cable.")

    def abort(self):
        try:
            self.device.reset_input_buffer()
            self.device.reset_output_buffer()
        except:
            pass
