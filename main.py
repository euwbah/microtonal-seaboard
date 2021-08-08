import os.path
import traceback

from rtmidi import MidiIn, MidiOut
from rtmidi.midiutil import open_midiinput, open_midioutput

import configs
import convert
import ws_server
from configs import SlideMode, CONFIGS
from handler import MidiInputHandler
from mapping import Mapping, MapParsingError
from split import SplitData

import tkinter.filedialog as filedialog
import tkinter as tk

root = tk.Tk()
root.withdraw()

def select_splits():
    while True:
        split_pos_strs = input('enter channel split position(s) or leave blank for 1 output channel only: ').split(' ')

        if len(split_pos_strs) > 15:
            print('Too many split positions! Maximum 15 split positions. (16 channels)')
            continue

        splitpos = []

        prev_s = 0
        problem = False
        for s in split_pos_strs:
            try:
                pos = convert.notename_to_midinum(s)
                if pos > prev_s:
                    splitpos.append(pos)
                else:
                    print('Split positions must be in ascending order!')
                    problem = True
                    break
            except Exception:
                print(f'{s} is not a valid note name')
                problem = True
                break

        if not problem:
            break

    splitpos.append(128)

    CONFIGS.SPLITS = SplitData()  # reset splits

    prev_split_pos = 0
    for ch, s in enumerate(splitpos):
        while True:
            i = input(f'enter midi output offset for split range channel {ch + 1} '
                  f'(range {convert.midinum_to_12edo_name(prev_split_pos)} - '
                  f'{convert.midinum_to_12edo_name(s - 1)}): ')

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

    root.deiconify()

    if search_default:
        if os.path.isfile('mappings/default.sbmap'):
            try:
                CONFIGS.MAPPING = Mapping('mappings/default.sbmap')
                print('default.sbmap mapping found. Using default mapping.')
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
            break
        except MapParsingError as e:
            print(e)
        except Exception:
            print('unknown error:')
            traceback.print_exc()

    root.withdraw()


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


def intable(s):
    """Check if a string can be converted to an int"""
    try:
        int(s)
        return True
    except ValueError:
        return False


if __name__ == '__main__':
    print('microtonal seaboard retuner v0.3.0')

    has_read_configs = configs.read_configs()

    if not has_read_configs:
        select_mapping(search_default=True)

    print('')
    print('MIDI IN/OUT DEVICE SELECTION')
    print('')

    print('Select the Seaboard MIDI input device:')
    seaboard: MidiIn = open_midiinput()[0]

    print('Select the virtual MIDI output port that gets sent to the DAW/VST/Program:')
    virtual_port: MidiOut = open_midioutput()[0]

    if not has_read_configs:
        print('')
        select_pitch_bend_range()

    print('')

    print(f'Starting microtonal message forwarding in '
          f'{"MPE" if CONFIGS.MPE_MODE else "MIDI"} mode...')

    ws_server.start_ws_server()

    seaboard.set_callback(MidiInputHandler(virtual_port))

    print("""
    supported commands:
    mpe                         set to mpe mode (default)
    midi                        set to midi mode
    slide <n>|prs|rel|abs|bip   set slide message forwarding mode.
                                    <n>: fixed slide value (choose from 0-127)
                                    prs: map to press dimension
                                    rel: emulate relative slide mode
                                    abs: emulate absolute slide mode
                                    bip: (default) emulate bipolar mode
    split                       set split points (for midi mode)
    map                         select new .sbmap file
    pb                          change pitch bend amount
    sus                         toggles sustain pedal polarity
    save                        saves all current settings
    exit                        exit the program""")

    while True:
        s = input('>> ').strip().lower()

        if s == 'exit':
            print('closing port connections')
            del virtual_port
            del seaboard
            exit(0)
        if s == 'save':
            configs.save_configs()
        elif s == 'mpe':
            print('MPE mode active')
            CONFIGS.MPE_MODE = True
        elif s == 'midi':
            print('MIDI mode active')
            CONFIGS.MPE_MODE = False
        elif s.startswith('slide'):
            if 'none' in s:
                CONFIGS.SLIDE_MODE = SlideMode.FIXED
                CONFIGS.SLIDE_FIXED_N = 64
                print('Defaulting slide dimension (cc74) to 64')
            elif 'prs' in s or 'press' in s:
                CONFIGS.SLIDE_MODE = SlideMode.PRESS
                print('Forwarding press dimension to cc74')
            elif 'rel' in s or 'relative' in s:
                CONFIGS.SLIDE_MODE = SlideMode.RELATIVE
                print('Relative slide mode activated')
            elif 'abs' in s or 'absolute' in s:
                CONFIGS.SLIDE_MODE = SlideMode.ABSOLUTE
                print('Absolute slide mode activated')
            elif 'bip' in s or 'bipolar' in s:
                CONFIGS.SLIDE_MODE = SlideMode.BIPOLAR
                print('Bipolar slide mode activated')
            else:
                try:
                    n = int(s[5:])
                    if 0 > n > 127:
                        print('Default slide value must be an integer from 0-127 inclusive')
                        continue

                    CONFIGS.SLIDE_MODE = SlideMode.FIXED
                    CONFIGS.SLIDE_FIXED_N = n
                    continue
                except Exception:
                    print("""Unsupported slide mode. Valid slide modes are:
                        <n>: fixed slide value (choose from 0-127)
                        prs: map to press dimension
                        rel: emulate relative slide mode
                        abs: emulate absolute slide mode
                        bip: (default) emulate bipolar mode
                    """)
                    pass
        elif s == 'split':
            select_splits()
        elif s == 'map':
            select_mapping()
        elif s == 'pb':
            select_pitch_bend_range()
        elif s == 'sus':
            CONFIGS.TOGGLE_SUSTAIN = not CONFIGS.TOGGLE_SUSTAIN
            print(f'Invert sustain: {"on" if CONFIGS.TOGGLE_SUSTAIN else "off"}')
