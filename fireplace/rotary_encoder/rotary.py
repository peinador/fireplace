from typing import Callable, List, Optional, Tuple

import logging
import time

import RPi.GPIO as GPIO


class Counter:
    def __init__(
        self,
        value: Optional[float] = None,
        range: Tuple[float, float] = (0, 100),
        step: float = 1,
        callbacks: List[Callable[[float], None]] = [],
    ):
        self.value = value if value is not None else 0
        self.step = step
        self.range = range
        self.callbacks = callbacks

    def run_callbacks(self):
        for fun in self.callbacks:
            fun(self.value)

    def up(self):
        self.value = min(self.value + self.step, self.range[1])
        self.run_callbacks()

    def down(self):
        self.value = max(self.value - self.step, self.range[0])
        self.run_callbacks()

    def __repr__(self) -> str:
        return str(self.value)


def create_encoder_callback(
    counter: Counter,
    CLK_PIN=23,
    DT_PIN=8,
    logger: Optional[logging.Logger] = None,
    debounce_ms: float = 5.0,
):
    last_trigger_time = [0.0]  # Use list to allow mutation in closure
    last_clk = [GPIO.input(CLK_PIN)]  # Track last CLK state

    def encoder_callback(channel):
        # Non-blocking debounce: ignore triggers within debounce window
        current_time = time.time() * 1000  # Convert to milliseconds
        if current_time - last_trigger_time[0] < debounce_ms:
            return
        last_trigger_time[0] = current_time

        CLK_State = GPIO.input(CLK_PIN)
        DT_State = GPIO.input(DT_PIN)

        # Only act on CLK falling edge (HIGH -> LOW transition)
        if last_clk[0] == GPIO.HIGH and CLK_State == GPIO.LOW:
            # Direction is determined by DT state at the moment of CLK falling edge
            if DT_State == GPIO.HIGH:
                counter.up()
            else:
                counter.down()

            if logger is not None:
                logger.info(f"counter: {counter.value}")

        last_clk[0] = CLK_State

    return encoder_callback
