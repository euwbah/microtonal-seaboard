import threading
import time
from typing import Optional, Union


class ChannelWrapper:
    def __init__(self):
        self._cc74 = 0

        self._note_on = False
        """
        flag that affects whether cc74 messages or pitch bend messages get passed through
        if not on, cc74 messages pass, else, pitch bend messages will pass.
        """

        self._waiting_for_cc74 = True
        """
        Race conditions can cause a note on event to be handled before its corresponding
        cc74 message. Das not gud.
        This flag is set to True upon note off, and will only be set to false when a
        cc74 message has been registered.

        If a cc74 message is registered before a note on event, no problem.
        If a cc74 message is only registered after a note on event, the cc74 message
        has to act as if the note was not yet on, and the appropriate pitch bends and
        base pitch setting must be applied.
        """

        self.midi_note_received = 0
        """
        Stores the midi note that was received in the event that the note cannot
        be immediately forwarded as it is pending a cc74 message.
        """

        self.on_velocity_received = 0
        """
        Stores the raw on velocity that was received in the event that the note cannot be
        immediately forwarded as it is pending a cc74 message.

        This is the raw value before velocity curve is applied.
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

        self.edosteps_from_a4 = 0
        """
        Raw number of edosteps from a4 that was sent to the websocket server
        """


class KeyTracker:
    """
    Deals with interfacing & correlation of output events with input events.
    """
    def __init__(self):
        self.__notes: dict[int, ChannelWrapper] = {}
        for ch in range(0, 16):
            self.__notes[ch] = ChannelWrapper()

    def register_on(self, midi_received, vel, in_channel, midi_sent, send_channel, edosteps_from_a4, pitch_offset=8192):
        """
        Called only after a NOTE ON event has been forwarded.
        If note on received, but still awaiting cc74 message, use
        register_received to register the received pitch.

        :param midi_received: The midi note that was received from input which triggered this event
        :param vel: The velocity that was received
        :param in_channel: The input channel that triggered this event
        :param midi_sent: The output midi note number of this note
        :param send_channel: The output channel this note will be sent to
        :param pitch_offset: The initial base pitch offset (only in MPE mode)
        """
        n = self.__notes[in_channel]
        n.midi_note_received = midi_received
        n.on_velocity_received = vel
        n.midi_note_sent = midi_sent
        n._note_on = True
        n.base_pitch = pitch_offset
        n.channel_sent = send_channel
        n.edosteps_from_a4 = edosteps_from_a4

    def register_received(self, midi_received, vel, in_channel):
        """
        Used when a NOTE ON has been received, but can't be forwarded yet as it is
        still pending a CC74 message.

        :param midi_received: The midi note that was received from input which triggered this event
        :param vel: The velocity that was received
        :param in_channel: The input channel that triggered this event
        """
        n = self.__notes[in_channel]
        n.midi_note_received = midi_received
        n.on_velocity_received = vel

    def register_off(self, in_channel):
        """
        :param in_channel: The input channel the note off event was received on
        """
        n = self.__notes[in_channel]
        n._note_on = False
        n._waiting_for_cc74 = True

    def register_cc74(self, in_channel, cc74) -> Optional[Union[int, ChannelWrapper]]:
        """
        Register cc74 event on an input channel
        :param in_channel: The input channel the cc74 event was received on
        :param cc74: The cc74 value
        :return: None if the cc74 was updated, cc74 value if active, and ChannelWrapper object if waiting for cc74
                 in order for note to be forwarded.
        """
        n = self.__notes[in_channel]
        if not n._note_on:
            n._cc74 = cc74
            n._waiting_for_cc74 = False

            # this cc74 message may appear after a NOTE OFF event due to thread problems
            # to really ensure that waiting_for_cc74 isn't erroneously set to False,
            # wait 20ms and check again that the note is indeed ON.
            def double_check():
                time.sleep(0.02)
                if not n._note_on:
                    n._waiting_for_cc74 = True

            threading.Thread(target=double_check).start()
            return None
        elif n._waiting_for_cc74:
            n._cc74 = cc74
            n._waiting_for_cc74 = False
            return n

        return n._cc74

    def check_waiting_for_cc74(self, in_channel):
        return self.__notes[in_channel]._waiting_for_cc74

    def get_initial_cc74(self, in_channel) -> int:
        return self.__notes[in_channel]._cc74

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
        if n._note_on:
            return n
        return None

