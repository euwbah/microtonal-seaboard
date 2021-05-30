import os.path
import traceback
from enum import Enum

from rtmidi import MidiIn, MidiOut
from rtmidi.midiutil import open_midiinput, open_midioutput

import convert
from handler import MidiInputHandler
from mapping import Mapping, MapParsingError
from probe_ports import print_all_midi_ports
from split import SplitData

import tkinter.filedialog as filedialog

class SlideMode(Enum):
    NONE = 1        # default cc74 to 64
    PRESS = 2       # cc74 is mapped to Channel Pressure
    RELATIVE = 3    # calculated with respect to initial locked cc74 value (initial position is 64)
    ABSOLUTE = 4    # zero damns given, just forward all cc74 messages as is.

class CONFIGS:
    MPE_MODE = True
    SLIDE_MODE = SlideMode.RELATIVE
    SPLITS = SplitData()
    PITCH_BEND_RANGE = 24
    MAPPING: Mapping = None
    TOGGLE_SUSTAIN = False


def select_splits():
    while True:
        split_pos_strs = input('enter channel split position(s) or leave blank for 1 output channel only: ').split(' ')

        if len(split_pos_strs) > 15:
            print('Too many split positions! Maximum 15 split positions. (16 channels)')
            continue

        splitpos = []

        prev_s = 0
        for s in split_pos_strs:
            try:
                pos = convert.notename_to_midinum(s)
                if pos > prev_s:
                    splitpos.append(pos)
                else:
                    print('Split positions must be in ascending order!')
                    continue
            except Exception:
                print(f'{s} is not a valid note name')
                continue
        break

    splitpos.append(128)

    CONFIGS.SPLITS = SplitData()  # reset splits

    prev_split_pos = 0
    for ch, s in enumerate(splitpos):
        while True:
            i = input(f'enter midi output offset for split range channel {ch} '
                  f'(range {convert.midinum_to_12edo_name(prev_split_pos)} - '
                  f'{convert.midinum_to_12edo_name(s - 1)})')

            try:
                offset = int(i)
                CONFIGS.SPLITS.add_split(splitpos[ch], offset)
            except ValueError:
                print('enter a valid number!')
                continue
            break

        prev_split_pos = s


def select_mapping(search_default=False):
    print('')
    print('SEABOARD MAPPING SELECTION')
    print('')

    if search_default:
        if os.path.isfile('mappings/default.sbmap'):
            print('default.sbmap mapping found. Using default mapping.')
            try:
                CONFIGS.MAPPING = Mapping('mappings/default.sbmap')
                print('Loaded mapping successfully\n')
                return
            except MapParsingError as e:
                print(e)
                print('Unable to parse default map')
            except Exception:
                print('unknown error:')
                traceback.print_exc()

    while True:
        path = filedialog.askopenfilename(
            title='Choose seaboard map file',
            initialdir='./',
            filetypes=(('Seaboard map files', '*.sbmap'),)
        )

        if not os.path.isfile(path):
            print(f"{path} doesn't exist!")

        try:
            CONFIGS.MAPPING = Mapping(path)
            print('Loaded mapping successfully\n')
            return
        except MapParsingError as e:
            print(e)
        except Exception:
            print('unknown error:')
            traceback.print_exc()


def select_pitch_bend_range():
    while True:
        try:
            i = input('Enter pitch bend +/- range as per Equator/VST/ROLI Dashboard: ').strip()

            pb = int(i)

            if pb <= 1:
                print('Pitch bend range has to be 1 or more')
                continue

            CONFIGS.PITCH_BEND_RANGE = pb
            return
        except Exception:
            pass


if __name__ == '__main__':
    print('microtonal seaboard retuner v0.1')

    select_mapping(search_default=True)

    print('')
    print('MIDI IN/OUT DEVICE SELECTION')
    print('')

    print('Select the Seaboard MIDI input device:')
    seaboard: MidiIn = open_midiinput()

    print('Select the virtual MIDI output port that gets sent to the DAW/VST/Program:')
    virtual_port: MidiOut = open_midioutput()

    print('')
    select_pitch_bend_range()

    print('')
    print('Starting microtonal message forwarding in MPE mode...')

    seaboard.set_callback(MidiInputHandler(virtual_port))

    print("""
    supported commands:
    mpe                     set to mpe mode (default)
    midi                    set to midi mode
    slide none|prs|rel|abs  set slide message forwarding mode.
                                none: cc74 is always 64
                                 prs: cc74 mapped to press dimension
                                 rel: (default) cc74 emulates relative slide mode
                                 abs: cc74 emulates absolute slide mode
    split                   set split points (for midi mode)
    map                     select new .sbmap file
    pb                      change pitch bend amount
    sus                     toggles sustain pedal polarity
    exit                    exit the program""")

    while True:
        s = input('>> ').strip().lower()

        if s == 'exit':
            print('closing port connections')
            del virtual_port
            del seaboard
            exit(0)
        elif s == 'mpe':
            print('MPE mode active')
            CONFIGS.MPE_MODE = True
        elif s == 'midi':
            print('MIDI mode active')
            CONFIGS.MPE_MODE = False
        elif s.startswith('slide'):
            if 'none' in s:
                CONFIGS.SLIDE_MODE = SlideMode.NONE
                print('Defaulting slide dimension (cc74) to 64')
            elif 'prs' in s:
                CONFIGS.SLIDE_MODE = SlideMode.PRESS
                print('Forwarding press dimension to cc74')
            elif 'rel' in s:
                CONFIGS.SLIDE_MODE = SlideMode.RELATIVE
                print('Relative slide mode activated')
            elif 'abs' in s:
                CONFIGS.SLIDE_MODE = SlideMode.ABSOLUTE
                print('Absolute slide mode activated')
        elif s == 'split':
            select_splits()
        elif s == 'map':
            select_mapping()
        elif s == 'pb':
            select_pitch_bend_range()
        elif s == 'sus':
            CONFIGS.TOGGLE_SUSTAIN = not CONFIGS.TOGGLE_SUSTAIN
            print(f'Invert sustain: {"on" if CONFIGS.TOGGLE_SUSTAIN else "off"}')
