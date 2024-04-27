from typing import Optional

import time

import RPi.GPIO as GPIO


class Counter:
    def __init__(self, value: Optional[int] = None):
        self.value = value if value is not None else 0
        self.CLK_Last = GPIO.HIGH
        self.dtLastState = GPIO.HIGH

    def up(self):
        self.value += 1

    def down(self):
        self.value -= 1

    def __repr__(self) -> str:
        return str(self.value)


def create_encoder_callback(counter: Counter, CLK_PIN=23, DT_PIN=8):
    def encoder_callback(channel):
        CLK_State = GPIO.input(CLK_PIN)
        DT_State = GPIO.input(DT_PIN)
        if DT_State != counter.dtLastState:
            counter.dtLastState = DT_State
            time.sleep(0.002)  # debounce time
            DT_State = GPIO.input(DT_PIN)
            if CLK_State != counter.CLK_Last and DT_State == counter.dtLastState:
                if CLK_State != DT_State:
                    counter.up()
                else:
                    counter.down()
        print("counter:", counter)
        counter.CLK_Last = CLK_State

    return encoder_callback
