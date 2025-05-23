import threading
import time
import rtmidi.midiconstants as midi
from rtmidi import MidiIn, MidiOut # type: ignore

import convert
import ws_server
from keytracker import KeyTracker, ChannelWrapper
from configs import SlideMode, CONFIGS

EVENT_MASK = 0b11110000
CHANNEL_MASK = 0b00001111
MIDI_NOTE_A4 = convert.notename_to_midinum('a4')
ALL_CHANNELS = -1

tracker = KeyTracker()


class MidiInputHandler():
    def __init__(self, out_port: MidiOut):
        self.out_port = out_port
        self._wallclock = time.time()
        self.octave_offset = 4
        """
        The lowest note on the Rise 49 is C with octave one less than this.

        CC 06 (Data Entry MSB) gives the octave offset when it is updated.
        """

    def __call__(self, event, data=None):
        mapping = CONFIGS.MAPPING
        message, deltatime = event
        self._wallclock += deltatime

        msg_type, channel = EVENT_MASK & message[0], CHANNEL_MASK & message[0]

        def tune_and_send_note(note, vel, cc74):
            edosteps_from_a4 = mapping.calc_notes_from_a4(note, cc74)
            scaled_vel = CONFIGS.VELOCITY_CURVES.get_velocity(note, vel, self.octave_offset, cc74, CONFIGS.DEBUG)

            pitchbend = None

            if CONFIGS.MPE_MODE:
                pitchbend = mapping.calc_pitchbend(note, cc74)
                # pitch bend has to go before the note on event
                # otherwise equator might not register it.
                self.send_pitch_bend(channel, pitchbend)
                self.send_note_on(channel, note, scaled_vel)

                if CONFIGS.SLIDE_MODE == SlideMode.FIXED:
                    self.send_cc(channel, 74, CONFIGS.SLIDE_FIXED_N)
                # NOTE: the vel parameter is raw, before applying velocity curve
                tracker.register_on(note, vel, channel, note, channel, edosteps_from_a4, pitchbend)

                # pitch bend has to go after note on event
                # otherwise strobe 2 complete disregards it
                # because of this we have to send it twice
                self.send_pitch_bend(channel, pitchbend)
            else:
                if CONFIGS.AUTO_SPLIT is not None:
                    send_ch, send_note_offset = CONFIGS.AUTO_SPLIT.get_split_range(note)
                else:
                    send_ch, send_note_offset = CONFIGS.SPLITS.get_split_range(note)

                send_note = edosteps_from_a4 + MIDI_NOTE_A4 + send_note_offset

                if 0 > send_note > 127:
                    send_note = max(0, min(127, send_note))
                    print('Midi note out of range! Consider using mutliple vst instances in different octaves '
                          'and split ranges with pitch offsets when in MIDI mode.')
                self.send_note_on(send_ch, send_note, scaled_vel)

                # if a note overrides another active note in the same input channel,
                # stop that note. Prevents ghosts that hang around.
                if existing := tracker.check_existing(channel):
                    print(f'max channel used: sent {existing.edosteps_from_a4} off')
                    self.send_note_off(existing.channel_sent, existing.midi_note_sent, 0)
                    ws_server.send_note_off(existing.edosteps_from_a4, 0)

                def do_later():
                    time.sleep(0.001)
                    self.send_cc(channel, 74, CONFIGS.SLIDE_FIXED_N)

                if CONFIGS.SLIDE_MODE == SlideMode.FIXED:
                    threading.Thread(target=do_later).start()

                # NOTE: the vel parameter is raw, before applying velocity curve
                tracker.register_on(note, vel, channel, send_note, send_ch, edosteps_from_a4)

            ws_server.send_note_on(edosteps_from_a4, scaled_vel)

            if CONFIGS.DEBUG:
                print(f'recv: (note {note}, vel {vel}, cc74 {cc74}), sent: (note {edosteps_from_a4}, {f"pb {pitchbend}, " if CONFIGS.MPE_MODE else ""}vel {scaled_vel})')

        if msg_type == midi.NOTE_ON:
            note, vel = message[1:3]
            if not tracker.check_waiting_for_cc74(channel):
                cc74 = tracker.get_initial_cc74(channel)
                tune_and_send_note(note, vel, cc74)
            else:
                tracker.register_received(note, vel, channel)

                print(f'debug: note on before cc74: '
                      f'{convert.midinum_to_12edo_name(note)}')

        elif msg_type == midi.NOTE_OFF:
            note, vel = message[1:3]

            if CONFIGS.MPE_MODE:
                self.send_note_off(channel, note, vel)

            if existing := tracker.check_existing(channel):
                if not CONFIGS.MPE_MODE:
                    self.send_note_off(existing.channel_sent, existing.midi_note_sent, vel)

                ws_server.send_note_off(existing.edosteps_from_a4, vel)
            else:
                print('warning: unable to find existing note to turn off in websocket/MIDI mode. '
                      'There may be a stuck note present.')

            tracker.register_off(channel)

        elif msg_type == midi.CONTROL_CHANGE:
            cc, value = message[1:3]
            c = channel if CONFIGS.MPE_MODE else ALL_CHANNELS

            def send_preempt_defaults():
                if CONFIGS.SLIDE_MODE == SlideMode.ABSOLUTE:
                    self.send_cc(c, cc, value)
                elif CONFIGS.SLIDE_MODE == SlideMode.RELATIVE:
                    self.send_cc(c, cc, 64)
                elif CONFIGS.SLIDE_MODE == SlideMode.PRESS or\
                        CONFIGS.SLIDE_MODE == SlideMode.BIPOLAR:
                    self.send_cc(c, cc, 0)

            if cc == 74:
                if init74_or_note := tracker.register_cc74(channel, value):
                    if type(init74_or_note) is int:
                        # The note is currently active
                        if CONFIGS.SLIDE_MODE == SlideMode.ABSOLUTE:
                            self.send_cc(c, cc, value)
                        elif CONFIGS.SLIDE_MODE == SlideMode.RELATIVE:
                            self.send_cc(c, cc, convert.to_relative_slide_output(value, init74_or_note))
                        elif CONFIGS.SLIDE_MODE == SlideMode.BIPOLAR:
                            self.send_cc(c, cc, convert.to_bipolar_slide_output(value, init74_or_note))
                    elif type(init74_or_note) is ChannelWrapper:
                        # Note was awaiting cc74 to be forwarded.
                        send_preempt_defaults()
                        tune_and_send_note(init74_or_note.midi_note_received,
                                           init74_or_note.on_velocity_received,
                                           value)

                        print(f'debug: resolved note on before cc74: '
                              f'{convert.midinum_to_12edo_name(init74_or_note.midi_note_received)}')

                else:
                    # in these other cases, a note is about to happen.
                    # send the correct preemptive cc74 messages according
                    # to slide mode.
                    send_preempt_defaults()

            elif cc == midi.SUSTAIN:  # CC 64
                sustain_value = value if not CONFIGS.TOGGLE_SUSTAIN else 127 - value
                self.send_cc(c, cc, sustain_value)
                ws_server.send_cc(cc, sustain_value)
            elif cc == 6: # Data Entry MSB, octave switch
                self.octave_offset = value
                self.send_cc(c, cc, value)
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

            if CONFIGS.SLIDE_MODE == SlideMode.PRESS and msg_type == midi.CHANNEL_PRESSURE:
                if CONFIGS.MPE_MODE:
                    # note: channel pressure only has 1 data byte, of which represents
                    #       the value
                    self.send_cc(channel, 74, message[1])
                else:
                    self.send_cc(ALL_CHANNELS, 74, message[1])

    def send_note_on(self, channel, note, vel):
        if channel == ALL_CHANNELS:
            if CONFIGS.AUTO_SPLIT is not None:
                self.out_port.send_message([midi.NOTE_ON + 0, note, vel])
            else:
                for c in range(0, CONFIGS.SPLITS.get_num_channels_used()):
                    self.out_port.send_message([midi.NOTE_ON + c, note, vel])
        else:
            self.out_port.send_message([midi.NOTE_ON + channel, note, vel])

    def send_note_off(self, channel, note, vel):
        if channel == ALL_CHANNELS:
            if CONFIGS.AUTO_SPLIT is not None:
                self.out_port.send_message([midi.NOTE_OFF + 0, note, vel])
            else:
                for c in range(0, CONFIGS.SPLITS.get_num_channels_used()):
                    self.out_port.send_message([midi.NOTE_OFF + c, note, vel])
        else:
            self.out_port.send_message([midi.NOTE_OFF + channel, note, vel])

    def send_cc(self, channel, cc, val):
        if channel == ALL_CHANNELS:
            if CONFIGS.AUTO_SPLIT is not None:
                self.out_port.send_message([midi.CONTROL_CHANGE + 0, cc, val])
            else:
                for c in range(0, CONFIGS.SPLITS.get_num_channels_used()):
                    self.out_port.send_message([midi.CONTROL_CHANGE + c, cc, val])
        else:
            self.out_port.send_message([midi.CONTROL_CHANGE + channel, cc, val])

        ws_server.send_cc(cc, val);

    def send_pitch_bend(self, channel, pitchbend):
        lsb, msb = convert.pitch_bend_to_raw_pitch_msg(pitchbend)
        if channel == ALL_CHANNELS:
            if CONFIGS.AUTO_SPLIT is not None:
                self.out_port.send_message([midi.PITCH_BEND + 0, lsb, msb])
            else:
                for c in range(0, CONFIGS.SPLITS.get_num_channels_used()):
                    self.out_port.send_message([midi.PITCH_BEND + c, lsb, msb])
        else:
            self.out_port.send_message([midi.PITCH_BEND + channel, lsb, msb])

    def send_raw(self, msg):
        self.out_port.send_message(msg)



