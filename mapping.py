import re

import configs
import convert


class MapParsingError(Exception):
    def __init__(self, msg):
        super().__init__('Error parsing mapping. ' + msg)

class Mapping:
    def __init__(self, sbm_file_path):
        self.__keys = {}
        """
                data format:
                {
                    midinote: [(exclusive upper bound of cc74 representing current split, 
                                cent offsets, 
                                number of steps from A4 in MIDI mode (if the mapping doesn't support MIDI mode,
                                this will all be 0, or whatever placeholder value the mapping uses)]
                }

                e.g.:
                ```
                {
                    60: [(30, -10, 0), (60, 0, 1), (90, 10, 2), (128, 0, 3)]
                }
                ```
                represents cent offsets on the note C4 based on the following cc74 ranges (inclusive):
                - 0-29: -10 cents, will play A4 in MIDI mode
                - 30-59: 0 cents, will play Bb4 in MIDI mode
                - 60-89: 10 cents, will play B4 in MIDI mode
                - 90-127: 0 cents, will play C5 in MIDI mode
        """

        self.load_mapping(sbm_file_path)

    def load_mapping(self, sbm_file_path):
        self.__keys = {}

        with open(sbm_file_path,mode='r') as f:
            linecount = 0
            while line := f.readline():
                linecount += 1

                line = line.strip()

                if len(line) == 0 or line.startswith('#'):
                    # ignore blank lines and comments
                    continue
                elif line.startswith('/'):
                    print(line[1:].rstrip())
                    continue

                notename, *data = re.split('\\s+', line.strip())

                if len(data) % 3 != 0 or len(data) == 0:
                    raise MapParsingError(f'line {linecount}: incorrect number of arguments')

                try:
                    midinote = convert.notename_to_midinum(notename)

                    if midinote in self.__keys:
                        raise MapParsingError(f'line {linecount}: duplicate key entry')
                except ValueError:
                    raise MapParsingError(f'line {linecount}: invalid note name')

                # group data into arrays of 3 representing one area on a key
                segments = [tuple(data[n:n+3]) for n in range(0, len(data), 3)]

                previous_cc74 = 0

                split_points = []
                last_split_point = 0
                for cc74, cents, steps in segments:
                    try:
                        cc74 = int(cc74)
                    except Exception:
                        raise MapParsingError(f'line {linecount}: invalid cc74 split point: {cc74}')

                    if 1 > cc74 > 128:
                        raise MapParsingError(f'line {linecount}: cc74 split point out of range (1-128): {cc74}')

                    if cc74 <= previous_cc74:
                        raise MapParsingError(f'line {linecount}: cc74 split point not in ascending order: {cc74}')

                    previous_cc74 = cc74

                    try:
                        cents = float(cents)
                    except Exception:
                        raise MapParsingError(f'line {linecount}: invalid cents value: {cents}')

                    try:
                        steps = int(steps)
                    except Exception:
                        raise MapParsingError(f'line {linecount}: invalid steps value: {steps}')

                    split_points.append((cc74, cents, steps))
                    last_split_point = cc74

                if last_split_point != 128:
                    raise MapParsingError(f'line {linecount}: last cc74 split point of a key must be 128')

                self.__keys[midinote] = split_points

        print('Mapping loaded!')

    def calc_pitchbend(self, midinote, cc74):
        """
        Looks up the input note and cc74 in the mapping table and calculates
        the pitch bend information to send

        :param midinote: midi note number of input
        :param cc74: cc74 value of input
        :return: pitch bend amount to send (0-16383)
        """

        if midinote not in self.__keys:
            return 8192

        for split_pos, cents, steps in self.__keys[midinote]:
            if cc74 < split_pos:
                return convert.cents_to_pitchbend(cents, configs.CONFIGS.PITCH_BEND_RANGE)

        raise RuntimeError(f'Impossible state error: calc_pitchbend could not find split pos'
                           f'of {convert.midinum_to_12edo_name(midinote)}, cc74: {cc74}')

    def calc_notes_from_a4(self, midinote, cc74):
        """
        Get the step offset from A4 to send to output in MIDI mode.
        :param midinote: midi note number of input
        :param cc74: cc74 value of input
        :return: number of midi notes from A4 (midi note - 69)
        """

        if midinote not in self.__keys:
            return midinote

        for split_pos, cents, steps in self.__keys[midinote]:
            if cc74 < split_pos:
                return steps

        raise RuntimeError(f'Impossible state error: calc_midi_output could not find split pos'
                           f'of {convert.midinum_to_12edo_name(midinote)}, cc74: {cc74}')