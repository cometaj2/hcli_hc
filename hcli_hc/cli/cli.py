import json
import io
import os
import inspect
import sys
import serial
import io
import service
from functools import partial
from serial.tools import list_ports


class CLI:
    commands = None
    inputstream = None
    service = None

    def __init__(self, commands, inputstream):
        self.commands = commands
        self.inputstream = inputstream
        self.service = service.Service()

    def execute(self):

        if len(self.commands) == 1:
            if self.inputstream is not None:

               f = io.BytesIO()
               for chunk in iter(partial(self.inputstream.read, 16384), b''):
                   f.write(chunk)

               command = f.getvalue().decode().strip().upper()
               if command == '!' or command == '~' or command == '?' or command.startswith('$') or command.strip() == '':
                   self.service.simple_command(f)
               else:
                   self.service.stream(f, "sampled: " + command.splitlines()[0])

            return None

        # a named job
        elif self.commands[1] == "-j":
            if len(self.commands) > 2:
                if self.inputstream is not None:

                   f = io.BytesIO()
                   for chunk in iter(partial(self.inputstream.read, 16384), b''):
                       f.write(chunk)

                   command = f.getvalue().decode().strip().upper()
                   self.service.stream(f, self.commands[2])

                return None

        elif self.commands[1] == "scan":
            scanned = json.dumps(self.service.scan(), indent=4) + "\n"

            return io.BytesIO(scanned.encode("utf-8"))

        elif self.commands[1] == "connect":
            def connect_defer():
                if len(self.commands) <= 2:
                    ports = self.service.scan()
                    if ports.items():
                        for i, port in enumerate(ports, start=1):
                            if self.service.connect(ports[str(i)]):
                                break

                elif len(self.commands) > 2:
                    self.service.connect(self.commands[2])

            job = self.service.schedule(lambda: connect_defer())
            return

        elif self.commands[1] == "disconnect":
            self.service.disconnect()
            return

        elif self.commands[1] == "reset":
            self.service.reset()

        elif self.commands[1] == "status":
            self.service.status()

        elif self.commands[1] == "stop":
            self.service.stop()

        elif self.commands[1] == "home":
            self.service.home()

        elif self.commands[1] == "unlock":
            self.service.unlock()

        elif self.commands[1] == "resume":
            self.service.resume()

        elif self.commands[1] == "zero":
            self.service.zero()

        elif self.commands[1] == "logs":
            return self.service.tail()

        elif self.commands[1] == "setzero":
            if len(self.commands) > 2:
                if self.commands[2] == "xyz":
                    self.service.setzeroxyz()

        elif self.commands[1] == "jog":
            if self.inputstream is not None:
               self.service.jog(self.inputstream)

            return None

        elif self.commands[1] == "jobs":
            jobs = json.dumps(self.service.jobs(), indent=4) + "\n"

            return io.BytesIO(jobs.encode("utf-8"))
        return None
