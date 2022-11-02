"""CircuitPython Essentials Storage logging boot.py file"""
import board
import digitalio
import storage

switch = digitalio.DigitalInOut(board.GP7)
switch.direction = digitalio.Direction.INPUT
switch.pull = digitalio.Pull.UP

# If the switch pin is connected to ground (pressed) USB will have write access - This will be dev mode
# Otherwise CircuitPython will have write access - this will be production mode
storage.remount("/", not switch.value)
