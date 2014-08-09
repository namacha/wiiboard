# -*- coding: utf-8 -*-

import threading
import bluetooth


COMMAND_REPORTING = '52120432'
COMMAND_STATUS = '521500'
COMMAND_CALIBRATION = '521704A400240018'
COMMAND_LED = '5211%x0'

TYPE_CALIBRATION = 21
TYPE_STATUS = 20
TYPE_DATA = 32

POSITION_TOPRIGHT = 0
POSITION_TOPLEFT = 1
POSITION_BOTTOMRIGHT = 2
POSITION_BOTTOMLEFT = 3


DEVICE_NAME = 'Nintendo RVL-WBC-01'


class BoardNotFoundException(Exception):

    def __str__(self):
        return "BalanceBoard not found."


class Weights(object):

    def __repr__(self):
        a = "<Weights: %s %s %s %s>"
        return a % (str(self.topright),
                    str(self.topleft),
                    str(self.bottomright),
                    str(self.bottomleft)
                    )

    def __init__(self, value, raw_value):
        self.topright = value[0]
        self.topleft = value[1]
        self.bottomright = value[2]
        self.bottomleft = value[3]
        self.raw_topright = raw_value[0]
        self.raw_topleft = raw_value[1]
        self.raw_bottomright = raw_value[2]
        self.raw_bottomleft = raw_value[3]
        self._total = 0

    @property
    def total(self):
        return self._total

    @total.getter
    def total(self):
        return (self.topright +
                self.topleft +
                self.bottomright +
                self.bottomright)


class Board(object):

    def __repr__(self):
        return "<BalanceBoard: %s at %s>" % (self.ADDR, hex(id(self)))

    def __init__(self, ADDR=None):
        self.ADDR = ADDR
        self.batt = -1
        self.led = 0
        self.connected = False
        self.calibration = [[10000 for i in range(4)] for j in range(3)]
        self.calibration_completed = [False, False]
        self.initialdata = []
        self.f_disconnect = False
        self._weights = Weights((0, 0, 0, 0), (0, 0, 0, 0))
        self.last_received = ''
        self._button = False
        self.connect()
        self.initialize()
        self.t = threading.Thread(target=self.worker)
        self.t.setDaemon(True)
        self.t.start()

    @property
    def weights(self):
        return self._weights

    @weights.getter
    def weights(self):
        w = self._weights
        data = self.last_received
        intype = self.hexdecode(data)[2:4]
        if intype == str(TYPE_DATA):
            w = self.parse_sample_line(data)
        return Weights(*w)

    @property
    def button(self):
        return self._button

    @button.getter
    def button(self):
        w = self._button
        data = self.last_received
        intype = self.hexdecode(data)[2:4]
        if intype == str(TYPE_DATA):
            if self.hexdecode(data[3]) == '08':
                w = True
            else:
                w = False
        return w

    def connect(self):
        if self.ADDR is None:
            addr = self.discover()
            if addr is None:
                raise BoardNotFoundException
            self.ADDR = addr
        self.recv_sock = bluetooth.BluetoothSocket(bluetooth.L2CAP)
        self.send_sock = bluetooth.BluetoothSocket(bluetooth.L2CAP)
        self.recv_sock.connect((self.ADDR, 0x13))
        self.send_sock.connect((self.ADDR, 0x11))
        self.connected = True

    def disconnect(self):
        self.f_disconnect = True
        self.recv_sock.close()
        self.send_sock.close()

    def receive_initial_data(self):
        ls = [self.receive() for i in range(10)]
        self.initialdata = ls

    def initialize(self):
        if self.connected:
            self.send(COMMAND_STATUS)
            self.send(COMMAND_CALIBRATION)
            self.send(COMMAND_REPORTING)
            self.receive_initial_data()
            for line in self.initialdata:
                intype = int(self.hexdecode(line)[2:4])
                if intype == TYPE_STATUS:
                    self.set_batt_level(line)
                elif intype == TYPE_CALIBRATION:
                    packet_length = (int(self.hexdecode(line[4]), 16) / 16 + 1)
                    self.parse_calibration_response(
                        line[7:(7 + packet_length)]
                    )

    def hexdecode(self, data):
        return data.encode('hex')

    def hexencode(self, data):
        return data.decode('hex')

    def discover(self):
        addr = None
        device_list = bluetooth.discover_devices(duration=4, lookup_names=True)
        for device in device_list:
            if device[1] == DEVICE_NAME:
                addr = device[0]
        return addr

    def send(self, value):
        self.send_sock.send(self.hexencode(value))

    def receive(self):
        return self.recv_sock.recv(25)

    def toggle_led(self):
        v = 1 if (not self.led) else 0
        self.send(COMMAND_LED % v)
        self.led = not self.led
        return True

    def led_on(self):
        self.send(COMMAND_LED % 1)
        return True

    def led_off(self):
        self.send(COMMAND_LED % 0)
        return True

    def set_batt_level(self, data):
        self.batt = data.encode('hex')[-2:]
        return False

    def parse_calibration_response(self, data):
        if len(data) == 16:
            index = 0
            for i in range(2):
                for n in range(4):
                    self.calibration[i][n] = ((int(data[index].encode('hex'), 16) << 8) +
                                              int(data[index + 1].encode('hex'), 16))
                    index += 2
            self.calibration_completed[0] = True
        else:
            index = 0
            for i in range(4):
                self.calibration[2][i] = ((int(data[index].encode('hex'), 16) << 8) +
                                          int(data[index + 1].encode('hex'), 16))
                index += 2
            self.calibration_completed[1] = True

    def parse_sample(self, val, pos):
        weight = 0.0
        if val < self.calibration[0][pos]:
            weight = 0.0
        elif val < self.calibration[1][pos]:
            weight = 17 * ((val - self.calibration[0][pos]) /
                           float(self.calibration[1][pos] -
                           self.calibration[0][pos]))
        else:
            weight = 17 + 17 * ((val - self.calibration[1][pos]) /
                                float(self.calibration[2][pos] -
                                self.calibration[1][pos]))
        return weight

    def parse_sample_line(self, data):
        data = data[4:]
        ls = []
        for i in range(0, 8, 2):
            value = ((int(self.hexdecode(data[i]), 16) << 8) +
                     int(self.hexdecode(data[i + 1]), 16))
            ls.append(value)
        # raw value
        r_tr = ls[0]
        r_tl = ls[1]
        r_br = ls[2]
        r_bl = ls[3]
        # kgm value
        tr = self.parse_sample(ls[0], POSITION_TOPRIGHT)
        tl = self.parse_sample(ls[1], POSITION_TOPLEFT)
        br = self.parse_sample(ls[2], POSITION_BOTTOMRIGHT)
        bl = self.parse_sample(ls[3], POSITION_BOTTOMLEFT)
        return (tr, tl, br, bl), (r_tr, r_tl, r_br, r_bl)

    def worker(self):
        while not self.f_disconnect:
            self.last_received = self.receive()
