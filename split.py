import convert


class SplitData:
    def __init__(self):
        self.__splits = []

    def get_num_channels_used(self) -> int:
        return min(1, len(self.__splits))

    def add_split(self, midinum, outputoffset):
        self.__splits.append((midinum, outputoffset))

    def get_split_range(self, inputmidinum) -> (int, int):
        """
        Get the 0-indexed output channel number and output offset for the current
        split region given the input midi note. For MIDI mode.
        :param inputmidinum: midi note number of input note
        :return: (channel number, steps offset)
        """

        if len(self.__splits) == 0:
            return 0, 0

        channelnumber = 0

        for midinum, offset in self.__splits:
            if inputmidinum < midinum:
                return channelnumber, offset

            channelnumber += 1

        raise RuntimeError(f'Impossible state error: get_split_range could not find split '
                           f'range of input note {convert.midinum_to_12edo_name(inputmidinum)}')
