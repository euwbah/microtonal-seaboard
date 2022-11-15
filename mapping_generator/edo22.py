"""
22 edo mapping for seaboard. White keys form super pyth[7] in C.
pitch bends in MPE mode are based on A4 = 440Hz

Key splits (bottom-to-top):
    White key: down (sharp of tone below), natural, up (flat of tone above),
    Black key: sharp-down/flat-up

Supports MIDI mode, A4 is the anchoring equivalent note.
Each diesis raises midi output by 1 semitone.

Note: in MIDI mode, a +1 octave shift on the VST has to be accounted
      for with -22 semitone output offset configuration in the split offset
      configuration. To get the 'full range' of a piano, one will
      need to open 2 instances of Pianoteq/Kontakt and apply -2/+2
      octave offsets on each instance respectively.
      The split is to be set on the note E4.

"""

import sys
import convert

EDO = 22

ISWHITEKEY_MAP = {
    0: True,
    1: False,
    2: True,
    3: False,
    4: True,
    5: True,
    6: False,
    7: True,
    8: False,
    9: True,
    10: False,
    11: True
}

EDOSTEPS_FROM_A = {
    0: -17,  # C
    1: -15,  # C#
    2: -13,  # D
    3: -11,  # D#
    4: -9,  # E
    5: -8,  # F
    6: -6,   # F#
    7: -4,   # G
    8: -2,   # G#
    9: 0,    # A
    10: 2,   # A#
    11: 4    # B
}

"""
Key splits:

White key into 3 parts: down, natural, up

Black key only has 1 part: sharp-down/flat-up
"""
WHITE_DOWN = 30
WHITE_NAT = 50
WHITE_UP = 128

BLACK = 128

MIDI_NOTE_A4 = convert.notename_to_midinum('a4')


def calc_cent_offset(dieses_from_a4: int, semitones_from_a4: int) -> float:
    return 1200 * (dieses_from_a4 / EDO - semitones_from_a4 / 12)


def calc_semitones_from_a4(midinote) -> int:
    return midinote - MIDI_NOTE_A4


def calc_dieses_from_a4(octave, note) -> int:
    return EDO * (octave - 4) + EDOSTEPS_FROM_A[note]


with open('./mappings/22edo.sbmap', mode='w') as f:
    sys.stdout = f

    print('/   ' + __doc__.strip().replace('\n', '\n/   '))

    for midinote in range(0, 128):
        notename = convert.midinum_to_12edo_name(midinote)
        octave = -1 + midinote // 12
        note = midinote % 12
        semitones_from_a4 = calc_semitones_from_a4(midinote)
        # diesis offset from a4 for the natural or sharp note (if black key)
        nat_diesis = calc_dieses_from_a4(octave, note)

        if ISWHITEKEY_MAP[note]:
            centsdown = calc_cent_offset(nat_diesis - 1, semitones_from_a4)
            centsnat = calc_cent_offset(nat_diesis, semitones_from_a4)
            centsup = calc_cent_offset(nat_diesis + 1, semitones_from_a4)

            # keymap strictly has to be in increasing order
            keymap = [(WHITE_DOWN, centsdown, nat_diesis - 1),
                      (WHITE_NAT, centsnat, nat_diesis),
                      (WHITE_UP, centsup, nat_diesis + 1)]
        else:
            centssharp = calc_cent_offset(nat_diesis, semitones_from_a4)
            keymap = [(BLACK, centssharp, nat_diesis)]

        outputline = f'{notename:<4}'
        for cc74, cents, diesis in keymap:
            outputline += f' {cc74:>3} {cents:>8.4f} {diesis:>4}'

        print(outputline)