from typing import Optional


class ChannelWrapper:
    def __init__(self):
        self.cc74 = 0

        self.note_on = False
        """
        flag that affects whether cc74 messages or pitch bend messages get passed through
        if not on, cc74 messages pass, else, pitch bend messages will pass.
        """

        self.midi_note_sent = 0
        """
        Represents the midi note number that was sent as a result
        of the input on this current channel.
        
        In MIDI mode, this note number does not correlate to the
        input note that was received on this channel
        
        This is used to turn off the appropriate midi note
        should there be a 'on' event on two notes on the same channel
        on the input when in MIDI mode.
        
        This prevents hanging notes in MIDI mode when there are more than
        16 simultaneous input notes.
        """

        self.channel_sent = 0
        """
        Represents the channel that this note was sent to.
        
        In MIDI mode, the channel of the input note does not
        correlate to the channel of the output note.
        
        This keeps track of the channel the note was sent on
        so that the appropriate midi note can be turned off.
        
        This prevents hanging notes in MIDI mode when there are more than
        16 simultaneous input notes.
        """

        self.base_pitch = 8192
        """
        base pitch bend based on keyboard mapping.
        updated after note on event.
        """


class KeyTracker:
    """
    Deals with interfacing & correlation of output events with input events.
    """
    def __init__(self):
        self.__notes: dict[int, ChannelWrapper] = {}
        for ch in range(0, 16):
            self.__notes[ch] = ChannelWrapper()

    def register_on(self, in_channel, midi_num, send_channel, pitch_offset=8192):
        """
        :param in_channel: The input channel this note was received on
        :param midi_num: The output midi note number of this note
        :param send_channel: The output channel this note will be sent to
        :param pitch_offset: The initial base pitch offset (only in MPE mode)
        """
        n = self.__notes[in_channel]
        n.midi_note_sent = midi_num
        n.note_on = True
        n.base_pitch = pitch_offset
        n.channel_sent = send_channel

    def register_off(self, in_channel):
        """
        :param in_channel: The input channel the note off event was received on
        """
        self.__notes[in_channel].note_on = False

    def register_cc74(self, in_channel, cc74) -> Optional[int]:
        """
        Register cc74 event on an input channel
        :param in_channel: The input channel the cc74 event was received on
        :param cc74: The cc74 value
        :return: None if the cc74 was updated, or the locked cc74 value if the note is currently active.
        """
        n = self.__notes[in_channel]
        if not n.note_on:
            n.cc74 = cc74
            return None

        return n.cc74

    def get_initial_cc74(self, in_channel) -> int:
        return self.__notes[in_channel].cc74

    def get_base_pitch(self, in_channel) -> int:
        return self.__notes[in_channel].base_pitch

    def get_output_channel(self, in_channel) -> int:
        """
        Get the channel of the note that was sent as a result of
        receiving a note on a particular input channel.
        :param in_channel: The input channel the note was received on
        :return: The output channel the note was sent on.
        """
        return self.__notes[in_channel].channel_sent

    def check_existing(self, in_channel) -> Optional[ChannelWrapper]:
        """
        Check if there is an active note caused by a specific input channel.
        :param in_channel: Input channel this note was received on.
        :return: ChannelWrapper object or none.
        """
        n = self.__notes[in_channel]
        if n.note_on:
            return n
        return None

