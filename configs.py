import os
from enum import Enum
from typing import Optional

import dill

from mapping import Mapping
from split import SplitData
from velcurve import VelocityCurves


class SlideMode(Enum):
    FIXED = 1       # default cc74 to n
    PRESS = 2       # cc74 is mapped to Channel Pressure
    RELATIVE = 3    # calculated with respect to initial locked cc74 value (initial position is 64)
    ABSOLUTE = 4    # zero damns given, just forward all cc74 messages as is.
    BIPOLAR = 5     # starts at 0, either extreme will equal 127


class CONFIGS:
    '''
    Static Singleton class for storing global configuration data.
    '''
    MPE_MODE: bool = True
    SLIDE_MODE: SlideMode = SlideMode.RELATIVE
    SLIDE_FIXED_N: int = 64
    SPLITS: SplitData = SplitData()
    AUTO_SPLIT: Optional[SplitData] = None
    '''
    If not None, the SplitData will configure MIDI mode to output each octave in its own channel, and SPLITS will be ignored.
    The interval between C4 and C5 in the mapping will be used to determine octave offset in edosteps.
    This is useful for Pianoteq which allows multi-channel mode where channel N+1 is pitched
    one octave higher than channel N. (useful for very large edos)
    '''
    PITCH_BEND_RANGE: int = 24
    MAPPING: Mapping
    TOGGLE_SUSTAIN: bool = False
    VELOCITY_CURVES: VelocityCurves = VelocityCurves()
    VELOCITY_SMOOTHING: bool = True
    """
    If true, use a moving average of "Press" dimension (aftertouch) to control the steepness of the velocity curve.

    Turning this on attempts to reduce the effect of inaccurate velocity sensing on certain areas of the seaboard.
    """
    DEBUG: bool = False


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
            c: dict = dill.load(f)
            CONFIGS.MPE_MODE = c['MPE_MODE']
            CONFIGS.SLIDE_MODE = c['SLIDE_MODE']
            CONFIGS.SLIDE_FIXED_N = c['SLIDE_FIXED_N']
            CONFIGS.SPLITS = c['SPLITS']
            CONFIGS.AUTO_SPLIT = c['AUTO_SPLIT']
            CONFIGS.PITCH_BEND_RANGE = c['PITCH_BEND_RANGE']
            CONFIGS.MAPPING = c['MAPPING']
            CONFIGS.TOGGLE_SUSTAIN = c['TOGGLE_SUSTAIN']
            CONFIGS.VELOCITY_CURVES = c['VELOCITY_CURVES']
            CONFIGS.DEBUG = c['DEBUG']
            CONFIGS.VELOCITY_SMOOTHING = c.get('VELOCITY_SMOOTHING', True)

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
            'AUTO_SPLIT': CONFIGS.AUTO_SPLIT,
            'PITCH_BEND_RANGE': CONFIGS.PITCH_BEND_RANGE,
            'MAPPING': CONFIGS.MAPPING,
            'TOGGLE_SUSTAIN': CONFIGS.TOGGLE_SUSTAIN,
            'VELOCITY_CURVES': CONFIGS.VELOCITY_CURVES,
            'VELOCITY_SMOOTHING': CONFIGS.VELOCITY_SMOOTHING,
            'DEBUG': CONFIGS.DEBUG
        }
        dill.dump(c, f)
