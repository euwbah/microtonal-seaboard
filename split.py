from typing import Optional, Tuple
import convert
from mapping import Mapping


class SplitData:
    def __init__(self, map: Optional[Mapping] = None):
        '''
        Create a split data object. If a mapping is provided, the split data will
        use the mapping to determine split points automatically for auto split mode.
        '''
        self.__splits = []
        
        # Automatically populate splits if mapping is provided (auto split mode)
        
        if map is not None:
            for oct in range(1, 9):
                # add split points at C1, C2, ..., C8 to form 9 split regions.
                # The range between C4 and C5 should have 0 offset.
                split_midinum = convert.notename_to_midinum(f'C{oct}')
                self.add_split(split_midinum, (5 - oct) * map.edo)
            
            self.add_split(128, (5 - 9) * map.edo)  # add a final split point at 128 to mark the end of the last split region

    def get_num_channels_used(self) -> int:
        return min(1, len(self.__splits))

    def add_split(self, midinum, outputoffset):
        self.__splits.append((midinum, outputoffset))

    def get_split_range(self, inputmidinum) -> Tuple[int, int]:
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
