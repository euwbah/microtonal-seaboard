from rtmidi import (API_LINUX_ALSA, API_MACOSX_CORE, API_RTMIDI_DUMMY,
                    API_UNIX_JACK, API_WINDOWS_MM, MidiIn, MidiOut,
                    get_compiled_api)


def print_all_midi_ports():
    for name, class_ in (("input", MidiIn), ("output", MidiOut)):
        try:
            midi = class_()
            ports = midi.get_ports()
        except Exception as exc:
            print("Could not probe MIDI %s ports: %s" % (name, exc))
            continue

        if not ports:
            print("No MIDI %s ports found." % name)
        else:
            print("Available MIDI %s ports:\n" % name)

            for port, name in enumerate(ports):
                print("[%i] %s" % (port, name))

        print('')
        del midi
