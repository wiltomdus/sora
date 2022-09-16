"""Module for notification to the user."""

import asyncio
import board
import pwmio


class Notify:
    """Notify class"""

    def __init__(self) -> None:
        self.buzzer = pwmio.PWMOut(board.GP28, frequency=1000, duty_cycle=0)
        # self.buzzer = pwmio.PWMOut(board.GP27, frequency=1000, duty_cycle=0)

    async def buzz(self, duty_cycle=1000, duration=1.5):
        """buzz for duration at frequency"""
        self.buzzer.duty_cycle = duty_cycle
        await asyncio.sleep(duration)
        self.buzzer.duty_cycle = 0
