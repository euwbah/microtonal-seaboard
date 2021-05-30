import time
import rtmidi.midiconstants as midi
from rtmidi import MidiIn, MidiOut

import convert
from keytracker import KeyTracker
from main import CONFIGS, SlideMode

EVENT_MASK = 0b11110000
CHANNEL_MASK = 0b00001111
MIDI_NOTE_A4 = convert.notename_to_midinum('a4')
ALL_CHANNELS = -1

tracker = KeyTracker()


class MidiInputHandler():
    def __init__(self, out_port: MidiOut):
        self.out_port = out_port
        self._wallclock = time.time()

    def __call__(self, event, data=None):
        mapping = CONFIGS.MAPPING
        message, deltatime = event
        self._wallclock += deltatime

        msg_type, channel = EVENT_MASK & message[0], CHANNEL_MASK & message[0]

        if msg_type == midi.NOTE_ON:
            note, vel = message[1:3]
            cc74 = tracker.get_initial_cc74(channel)
            if CONFIGS.MPE_MODE:
                pitchbend = mapping.calc_pitchbend(note, cc74)
                self.send_note_on(channel, note, vel)
                self.send_pitch_bend(channel, pitchbend)
                tracker.register_on(channel, note, channel, pitchbend)
            else:
                send_ch, send_note_offset = CONFIGS.SPLITS.get_split_range(note)
                send_note = mapping.calc_notes_from_a4(note, cc74) + MIDI_NOTE_A4 + send_note_offset

                self.send_note_on(send_ch, send_note, vel)

                # if a note overrides another active note in the same input channel,
                # stop that note. Prevents ghosts that hang around.
                if existing := tracker.check_existing(channel):
                    self.send_note_off(existing.channel_sent, existing.midi_note_sent, 0)

                tracker.register_on(channel, send_note, send_ch)

        elif msg_type == midi.NOTE_OFF:
            note, vel = message[1:3]

            if CONFIGS.MPE_MODE:
                self.send_note_off(channel, note, vel)
            else:
                if existing := tracker.check_existing(channel):
                    self.send_note_off(existing.channel_sent, existing.midi_note_sent, vel)
                else:
                    print('warning: unable to find existing note to turn off in MIDI mode. '
                          'There may be a stuck note present.')

            tracker.register_off(channel)

        elif msg_type == midi.CONTROL_CHANGE:
            cc, value = message[1:3]
            c = channel if CONFIGS.MPE_MODE else ALL_CHANNELS
            if cc == 74:
                if init74 := tracker.register_cc74(channel, value):
                    # If case falls through, init74 represents the
                    # initial cc74 strike point, and the note is currently
                    # active
                    if CONFIGS.SLIDE_MODE == SlideMode.ABSOLUTE:
                        self.send_cc(c, cc, value)
                    elif CONFIGS.SLIDE_MODE == SlideMode.RELATIVE:
                        self.send_cc(c, cc, convert.to_relative_slide_output(value, init74))
                else:
                    # in these other cases, a note is about to happen.
                    # send the correct preemptive cc74 messages according
                    # to slide mode.
                    if CONFIGS.SLIDE_MODE == SlideMode.NONE or \
                            CONFIGS.SLIDE_MODE == SlideMode.RELATIVE:
                        self.send_cc(c, cc, 64)
                    elif CONFIGS.SLIDE_MODE == SlideMode.PRESS:
                        self.send_cc(c, cc, 0)
                    elif CONFIGS.SLIDE_MODE == SlideMode.ABSOLUTE:
                        self.send_cc(c, cc, value)

            elif cc == midi.SUSTAIN:  # CC 64
                self.send_cc(c, cc, value if not CONFIGS.TOGGLE_SUSTAIN else 127 - value)
            else:
                self.send_cc(c, cc, value)

        elif msg_type == midi.PITCH_BEND:
            ls7, ms7 = message[1:3]
            pb = convert.raw_pitch_msg_to_pitch_bend(ls7, ms7) - 8192 + tracker.get_base_pitch(channel)

            if tracker.check_existing(channel):
                if CONFIGS.MPE_MODE:
                    self.send_pitch_bend(channel, pb)
                else:
                    # sends pitch bend only on the channel pertaining to the split range
                    self.send_pitch_bend(tracker.get_output_channel(channel), pb)
        else:
            # just forward the message
            self.send_raw(message)

            # If slide mode is set to aftertouch, send cc74 according to aftertouch

            if msg_type == midi.CHANNEL_PRESSURE:
                if CONFIGS.MPE_MODE:
                    self.send_cc(channel, 74, message[2])
                else:
                    self.send_cc(ALL_CHANNELS, 74, message[2])

    def send_note_on(self, channel, note, vel):
        with self.out_port:
            if channel == ALL_CHANNELS:
                for c in range(0, CONFIGS.SPLITS.get_num_channels_used()):
                    self.out_port.send_message([midi.NOTE_ON + c, note, vel])
            else:
                self.out_port.send_message([midi.NOTE_ON + channel, note, vel])

    def send_note_off(self, channel, note, vel):
        with self.out_port:
            if channel == ALL_CHANNELS:
                for c in range(0, CONFIGS.SPLITS.get_num_channels_used()):
                    self.out_port.send_message([midi.NOTE_OFF + c, note, vel])
            else:
                self.out_port.send_message([midi.NOTE_OFF + channel, note, vel])

    def send_cc(self, channel, cc, val):
        with self.out_port:
            if channel == ALL_CHANNELS:
                for c in range(0, CONFIGS.SPLITS.get_num_channels_used()):
                    self.out_port.send_message([midi.CONTROL_CHANGE + c, cc, val])
            else:
                self.out_port.send_message([midi.CONTROL_CHANGE + channel, cc, val])

    def send_pitch_bend(self, channel, pitchbend):
        lsb, msb = convert.pitch_bend_to_raw_pitch_msg(pitchbend)
        with self.out_port:
            if channel == ALL_CHANNELS:
                for c in range(0, CONFIGS.SPLITS.get_num_channels_used()):
                    self.out_port.send_message([midi.PITCH_BEND + c, lsb, msb])
            else:
                self.out_port.send_message([midi.PITCH_BEND + channel, lsb, msb])

    def send_raw(self, msg):
        with self.out_port:
            self.out_port.send_message(msg)



