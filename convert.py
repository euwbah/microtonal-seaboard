__NOTENAMES = {
    0: 'C',
    1: 'C#',
    2: 'D',
    3: 'Eb',
    4: 'E',
    5: 'F',
    6: 'F#',
    7: 'G',
    8: 'Ab',
    9: 'A',
    10: 'Bb',
    11: 'B'
}

__NOTENUMSLOWERCASE = {
    'b#': 0,
    'c': 0,
    'c#': 1,
    'db': 1,
    'd': 2,
    'd#': 3,
    'eb': 3,
    'e': 4,
    'fb': 4,
    'e#': 5,
    'f': 5,
    'f#': 6,
    'gb': 6,
    'g': 7,
    'g#': 8,
    'ab': 8,
    'a': 9,
    'a#': 10,
    'bb': 10,
    'b': 11,
    'cb': 11
}


def midinum_to_12edo_name(notenum) -> str:
    notenum = int(notenum)
    if not (0 <= notenum <= 127):
        raise ValueError('note number out of range (0-127)')

    octave = -1 + notenum // 12
    note = notenum % 12

    return __NOTENAMES[note] + str(octave)


def notename_to_midinum(notename: str) -> int:
    try:
        note, octave = notename[:-1], int(notename[-1])
        if note.endswith('-'):
            # handle negative octaves
            note = note[:-1]
            octave = -octave
        return __NOTENUMSLOWERCASE[note.lower()] + 12 * (octave + 1)
    except Exception:
        raise ValueError(f'{notename} is an invalid note name')


def cents_to_pitchbend(cents, pb_range) -> int:
    """
    Convert cent offset to pitch bend value (capped to range 0-16383)
    :param cents: cent offset
    :param pb_range: pitch bend range in either direction (+/-) as per setting on Roli Dashboard / Equator
    :return:
    """
    pb = 8192 + 16384 * cents / (pb_range * 200)
    if 0 > pb > 16383:
        print(f'warning: pitchbend range too small to bend {cents} cents')
    return int(max(0, min(16383, pb)))


def raw_pitch_msg_to_pitch_bend(ls7, ms7):
    """
    Convert the raw midi pitch bend message to a single pitch bend value (0-16383)
    :param ls7: Least significant 7 bits (2nd msg byte)
    :param ms7: Most significant 7 bits (3rd msg byte)
    :return: A pitch bend value (0-16383)
    """
    return 2**7 * ms7 + ls7


def pitch_bend_to_raw_pitch_msg(pb) -> (int, int):
    """
    :param pb: pitch bend amount (will be bounded to 0-16383 if it exceeds range)
    :return: (lsb, msb)
    """

    pb = max(0, min(16383, pb))

    return pb % 2 ** 7, pb // 2 ** 7


def to_relative_slide_output(abs74, init74) -> int:
    """
    Converts absolute cc74 slide to relative cc74 slide based
    on initial cc74 position.

    Assumes a graph of 2 linear gradients. Perhaps a better algorithm
    would be to smooth out the curve?

    :param abs74: The absolute cc74 value
    :param init74: The initial cc74 value when the note was struck
    :return: The relative cc74 value to send
    """

    if abs74 == init74:
        return 64
    elif abs74 < init74:
        return min(127, max(0, int(64 * abs74 / init74)))
    elif abs74 > init74:
        return min(127, max(0, int(64 + 64 * (abs74 - init74) / (127 - init74))))


def to_bipolar_slide_output(abs74, init74) -> int:
    """
    Converts absolute cc74 slide to bipolar cc74 slide based
    on initial cc74 position.

    Assumes a graph of 2 linear gradients. Perhaps a better algorithm
    would be to smooth out the curve?

    :param abs74: The absolute cc74 value
    :param init74: The initial cc74 value when the note was struck
    :return: The relative cc74 value to send
    """

    if abs74 == init74:
        return 0
    elif abs74 < init74:
        return min(127, max(0, int(127 * (init74 - abs74) / init74)))
    elif abs74 > init74:
        return min(127, max(0, int(127 * (abs74 - init74) / (127 - init74))))