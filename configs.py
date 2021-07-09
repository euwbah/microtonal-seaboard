import os
from enum import Enum

import dill

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


def read_configs() -> bool:
    """
    Read saved CONFIG state.
    :return: True if successfully read a config file from 'config.dill'
    """
    if not os.path.isfile('config.dill'):
        return False

    print('loading saved configurations from config.dill')

    try:
        with open('config.dill', 'rb') as f:
            c = dill.load(f)
            CONFIGS.MPE_MODE = c['MPE_MODE']
            CONFIGS.SLIDE_MODE = c['SLIDE_MODE']
            CONFIGS.SLIDE_FIXED_N = c['SLIDE_FIXED_N']
            CONFIGS.SPLITS = c['SPLITS']
            CONFIGS.PITCH_BEND_RANGE = c['PITCH_BEND_RANGE']
            CONFIGS.MAPPING = c['MAPPING']
            CONFIGS.TOGGLE_SUSTAIN = c['TOGGLE_SUSTAIN']

    except Exception:
        print('failed to load saved configurations. Delete config.dill.')
        return False

    return True


def save_configs():
    print('saving settings into config.dill')

    with open('config.dill', 'wb') as f:
        c = {
            'MPE_MODE': CONFIGS.MPE_MODE,
            'SLIDE_MODE': CONFIGS.SLIDE_MODE,
            'SLIDE_FIXED_N': CONFIGS.SLIDE_FIXED_N,
            'SPLITS': CONFIGS.SPLITS,
            'PITCH_BEND_RANGE': CONFIGS.PITCH_BEND_RANGE,
            'MAPPING': CONFIGS.MAPPING,
            'TOGGLE_SUSTAIN': CONFIGS.TOGGLE_SUSTAIN
        }
        dill.dump(c, f)
