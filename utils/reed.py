import asyncio
import keypad

class Reed:
    
    def __init__(self):
        self.async_event = asyncio.Event()

    async def wait(self, pin):
            """Reed switch interrup """
            await asyncio.sleep(5) # wait for 5 seconds to prevent double detection
            with keypad.Keys((pin,), value_when_pressed=False) as keys:
                while self.async_event.is_set():
                    keypad_event = keys.events.get()
                    if keypad_event and keypad_event.pressed:
                        print("Reed switch triggered!")
                        self.async_event.clear()
                        break
                    await asyncio.sleep(0)