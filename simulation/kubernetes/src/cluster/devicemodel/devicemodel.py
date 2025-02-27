from .xaviernx import XavierNX
from .rpi import RaspberryPi

device_to_model_mapping = {
    "xaviernx": XavierNX,
    "rpi": RaspberryPi,
}