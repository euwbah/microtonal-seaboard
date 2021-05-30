"""
31 edo mapping for seaboard.
pitch bends in MPE mode are based on A4 = 440Hz

Key splits (bottom-to-top):
    White key: down, natural, up, natural, up
    Black key: sharp, flat, up of the next white key

Supports MIDI mode, A4 is the anchoring equivalent note.
Each diesis raises midi output by 1 semitone.

Note: in MIDI mode, a +1 octave shift on the VST has to be accounted
      for with -31 semitone output offset configuration in the split offset
      configuration. To get the 'full range' of a piano, one will
      need to open 2 instances of Pianoteq/Kontakt and apply -2/+2
      octave offsets on each instance respectively.
      The split is to be set on the note E4.

      This way, input notes ranging from C-1 to D#4 will get sent to
      channel 0 with a +62 dieses output offsetting the -2 octaves
      on the VST, and notes input ranging from E4 to G9 will get sent
      to channel 1 with a -62 dieses output offsetting the +2 octaves
      on the VST.

"""

import sys
import convert

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

DIESIS_FROM_A = {
    0: -23,  # C
    1: -21,  # C#
    2: -18,  # D
    3: -16,  # D#
    4: -13,  # E
    5: -10,  # F
    6: -8,   # F#
    7: -5,   # G
    8: -3,   # G#
    9: 0,    # A
    10: 2,   # A#
    11: 5    # B
}

"""
Key splits:

White key into 5 parts: down, natural, up, natural, up

Black key into 3 parts: sharp, flat, up of the next white key
"""
WHITE_DOWN = 30
WHITE_NAT = 50
WHITE_UP = 73
WHITE_NAT_ABOVE = 98
WHITE_UP_ABOVE = 128

BLACK_SHARP = 76
BLACK_FLAT = 109
BLACK_WHITE_UP_COURTESY = 128

MIDI_NOTE_A4 = convert.notename_to_midinum('a4')


def calc_cent_offset(dieses_from_a4: int, semitones_from_a4: int) -> float:
    return 1200 * (dieses_from_a4 / 31 - semitones_from_a4 / 12)


def calc_semitones_from_a4(midinote) -> int:
    return midinote - MIDI_NOTE_A4


def calc_dieses_from_a4(octave, note) -> int:
    return 31 * (octave - 4) + DIESIS_FROM_A[note]


with open('../mappings/default.sbmap', mode='w') as f:
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
                      (WHITE_UP, centsup, nat_diesis + 1),
                      (WHITE_NAT_ABOVE, centsnat, nat_diesis),
                      (WHITE_UP_ABOVE, centsup, nat_diesis + 1)]
        else:
            centssharp = calc_cent_offset(nat_diesis, semitones_from_a4)
            centsflat = calc_cent_offset(nat_diesis + 1, semitones_from_a4)
            centsupnext = calc_cent_offset(nat_diesis + 4, semitones_from_a4)
            keymap = [(BLACK_SHARP, centssharp, nat_diesis),
                      (BLACK_FLAT, centsflat, nat_diesis + 1),
                      (BLACK_WHITE_UP_COURTESY, centsupnext, nat_diesis + 4)]

        outputline = f'{notename:<4}'
        for cc74, cents, diesis in keymap:
            outputline += f' {cc74:>3} {cents:>8.4f} {diesis:>4}'

        print(outputline)