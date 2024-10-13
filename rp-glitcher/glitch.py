import rp2
from machine import Pin, UART
import random
import time

@rp2.asm_pio(set_init=rp2.PIO.OUT_LOW)
def glitch_manual():
    pull(block)         # pull from TX FIFO into OSR, block until we have data
    mov(x, osr)         # move value in OSR into X register

    set(pins, 1)        # pull set pin HIGH

    label("loop")       # loop begin
    jmp(x_dec, "loop")  # loop until X is zero, this is the width of the glitch

    set(pins, 0)        # pull set pin LOW


class Target:
    def __init__(self, baud=9600, txPin=4, rxPin=5, rstPin=8, glitchPin=14) -> None:
        # set up a UART interface with our target
        self.uart = UART(1, baudrate=baud, tx=Pin(txPin), rx=Pin(rxPin))

        # this allows us to reset the target device on demand
        self.rst = Pin(rstPin, Pin.OUT, Pin.PULL_DOWN, value=1)
        #self.rst.init(self.rst.OUT, Pin.PULL_DOWN)

        # the PIO glitching state machine that allows us to precisely control
        # the attached n-channel mosfet
        self.sm_glitch = rp2.StateMachine(0, glitch_manual, set_base=Pin(glitchPin))
        self.sm_glitch.active(1)

    def glitch(self, width=20) -> None:
        # input the glitch width to the glitch state machine's TX FIFO
        self.sm_glitch.put(width)

    def glitch_loop(self, min_width=10, max_width=20) -> None:
        no_data_received = 0
        while True:
            # check serial output
            data = self.read()

            if not data:
                no_data_received += 1
                if no_data_received > 100:  # target not functioning anymore?
                    print("Target reset")
                    self.reset()
                    no_data_received = 0

            else:
                no_data_received = 0
                print(data)
                if b"SUCCESS" in data or b"###" in data:
                    print(data)
                    print(width)
                    break

            width = random.randint(min_width, max_width)

            # glitch the target
            self.glitch(width)
            time.sleep(0.1)

    def read(self):
        return self.uart.read()

    def reset(self) -> None:
        self.rst.off()
        time.sleep(0.2)
        self.rst.on()
        time.sleep(0.1)


t = Target()
