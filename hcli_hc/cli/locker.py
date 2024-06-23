import time
import logger
import threading

logging = logger.Logger()


# gently lockers the grbl serial device along to help avoid stalling in a busy loop
class Locker:

    locker_start_time = None
    threadlock = None
    lock = None

    def __init__(self):
        self.lock = True
        self.threadlock = threading.Lock()
        self.locker_start_time = 0
        return

    # Sets the locker to the current time to initiate the locker countdown
    def start(self):
        self.locker_start_time = time.monotonic()  # Get the current time at the start to evaluate lockdown countdown
        self.lock = False

    # If the lockdown countdown has elapsed, we lock the locker.
    def count(self):
        if not self.locked():
            current_time = time.monotonic()
            elapsed_time = current_time - self.locker_start_time
            logging.debug("[ hc ] elapsed time: " + str(elapsed_time))

            if elapsed_time >= 5:
                self.locker_start_time = time.monotonic()
                self.lock = True
                logging.info("[ hc ] jogger locked: " + str(self.lock) + ". press 'esc' to unlock.")

    def locked(self):
        with self.threadlock:
            return self.lock
