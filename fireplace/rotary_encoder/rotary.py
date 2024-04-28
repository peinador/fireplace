from typing import List, Optional, Tuple

import time

import RPi.GPIO as GPIO


class Counter:
    def __init__(
        self,
        value: Optional[float] = None,
        range: Tuple[float, float] = (0, 100),
        step: float = 1,
        callbacks: List[function] = [],
    ):
        self.value = value if value is not None else 0
        self.CLK_Last = GPIO.HIGH
        self.dtLastState = GPIO.HIGH
        self.step = step
        self.range = range
        self.callbacks = callbacks

    def callbacks(self):
        for fun in self.callbacks:
            fun(self.value)

    def up(self):
        self.value = min(self.value + self.step, self.range[1])
        self.callbacks()

    def down(self):
        self.value = max(self.value - self.step, self.range[0])
        self.callbacks()

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
