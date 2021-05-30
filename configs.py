from enum import Enum

from mapping import Mapping
from split import SplitData


class SlideMode(Enum):
    FIXED = 1       # default cc74 to n
    PRESS = 2       # cc74 is mapped to Channel Pressure
    RELATIVE = 3    # calculated with respect to initial locked cc74 value (initial position is 64)
    ABSOLUTE = 4    # zero damns given, just forward all cc74 messages as is.
    BIPOLAR = 5     # starts at 0, either extreme will equal 127


class CONFIGS:
    MPE_MODE = True
    SLIDE_MODE = SlideMode.RELATIVE
    SLIDE_FIXED_N = 64
    SPLITS = SplitData()
    PITCH_BEND_RANGE = 24
    MAPPING: Mapping = None
    TOGGLE_SUSTAIN = False
