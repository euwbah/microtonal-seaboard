# Microtonal Seaboard Mapper

## Features

- Splits seaboard keys vertically using the Slide dimension & retunes to any arbitrary tuning system
- Cross-platform support: Windows, macOS, Linux (run `main.py`)
- MPE output mode
- MIDI output mode (useful for Pianoteq/Kontakt/etc) where each 'step'
  corresponds to 1 semitone in the output.
- Range splits for MIDI output mode.
  - Open multiple instances of a VST and offset them by +/- 2 octaves to
    get the full range of a piano in 31 edo.
- Different slide (cc74) modes
  - Fixed value of choice
  - Relative
  - Absolute 
  - Link slide to press (channel pressure)
  - Bipolar
- Invert sustain pedal (because I couldn't find this feature .in Equator)

## Quick Start

1. Download the latest relese [here](https://github.com/euwbah/microtonal-seaboard/releases).
   - Make sure it's for the correct operating system.
2. Connect your Seaboard RISE/Block, turn it on.
3. Check ROLI Dashboard/Equator/VST for current pitch bend range setting. Take note of this
   as you'll have to key it in later.
4. **Make sure you set Slide mode to absolute in the ROLI Dashboard**
   
   ![img.png](imgs/slide-mode.png)
   
5. **Set slide sensitivity to max.**
6. Create a [Virtual MIDI Port](https://dialogaudio.com/modulationprocessor/guides/virtual_midi/virtual_midi_setup.php).
   Name it whatever you like.
7. Start the seaboard mapping program. It defaults to this 31 edo mapping:
   - White keys are split into 5 vertical segments. From the bottom:
        1. down
        2. natural
        3. up
        4. natural
        5. up
   - Black keys are split into 3. From the bottom:
        1. sharp
        2. flat
        3. up of the next white key
8. Select the Seaboard MIDI input device
9. Select the virtual MIDI port you created as the output device.
10. Use the virtual MIDI port as the MIDI controller for your DAW/VST/Equator.
   (Check if you're accidentally using both the seaboard and virtual port at
   the same time.)
11. If you want to use a different mapping, enter `map` into the console.
    Refer to the [`.sbmap` file format](#seaboard-map-sbmap-file-format)
    and the [31 edo mapping script](https://github.com/euwbah/microtonal-seaboard/blob/master/mapping_generator/edo31.py)
    on how to create your own mappings, or 
    [file an issue](https://github.com/euwbah/microtonal-seaboard/issues/new)
    with the "Mapping Request" label.
   
## How does it work

The mapper reads input from the seaboard and uses the midi message
CC74 (the 'Slide' dimension) to distinguish vertical sections of each
key. The mapper outputs midi data to a virtual MIDI port that is used
to control the DAW/VST/Equator/Kontakt.

A mapping file (`.sbmap`) dictates the vertical points of which the
key splits. Each split key is assigned a cent offset value (used for MPE mode),
and a step number which represents the number of steps from the note
A4 (used for MIDI mode).

## Checklist:

To make sure this program runs correctly:

- Turn on & connect seaboard before running the mapper.
- Slide sensitivity must be maximum
- Slide mode must be absolute on the ROLI Dashboard
  (slide mode inside Equator's Global settings can be whatever)
- No. midi channels setting on ROLI Dashboard should be set
  to maximum (15)
- The pitch bend range specified must be correct as per
  the ROLI Dashboard, and the pitch bend range of the synth
  used must match the specified range.

## MPE mode: Equator/Strobe 2/MPE synths/DAWs/etc...

It should work out of the box. Remember to enable only the virtual midi port
as the controller and disable the seaboard midi device's input.

The output MPE messages are similar to the MPE messages sent by the
seaboard, with the exception of one extra pitch bend message sent
1ms after the NOTE ON event is sent.

## MIDI mode: Keyscape/Pianoteq/Kontakt/Zynaddsubfx/etc

After starting the mapper and connecting the devices, type `midi` to
enter MIDI mode. MIDI mode maps every split-key partition to a 
certain note output as denoted by the `.sbmap` mapping file.

The default 31 edo mapping `default.sbmap` will map A4 to A4.
Then, any subsequent diesis up will be output as the next semitone.
A^4 = Bb4, A#4 = B4, Bb4 = C5, etc...

By default, only the first MIDI channel of the output
will be used to output plain old MIDI data. More channels
are used depending on the number of keyboard range splits.

Any aftertouch/pitchbend/midi CC messages will be forwarded to
all active output channels simultaneously.

### Range splits: Get more range/keyboard splits in MIDI mode

MIDI only has 127 notes available, that's just 4 octaves of 31 edo
and a bit more.

However, with this mapper, the seaboard is now able to output MIDI
notes spanning a much greater range.

To get more range out of Pianoteq/Kontakt/microtuning synths,
you can open multiple instances of them and set them at different
octaves listening to different MIDI channels of the virtual MIDI
output port.

For example, let's say we have 2 instances of Pianoteq, one set at
-1 octaves listening to MIDI channel 1, and the other set at +1 octave
listening to MIDI channel 2. Then, we can type
the `split` command into the mapper to choose our splits.

The mapper prompts us with 
`enter channel split position(s) or leave blank for 1 output channel only: `.
Let's input `e4`. This means that the notes on the seaboard up to
Eb4 (inclusive) will be sent to MIDI channel 1 on the output,
and the notes E4 and above will be sent to MIDI channel 2. (If more splits
are needed, input the split points separated by spaces)

Next we are prompted:
`enter midi output offset for split range channel 1 (range C-1 - Eb4)`.
We have to input `31` representing an offset of +31 steps. This offsets
the -1 octave of the Pianoteq on channel 1. This way, we get an additional
1 octave range lower than what we had before.

Similarly, we are prompted:
`enter midi output offset for split range channel 2 (range E4 - G9)`.
To which we reply `-31` representing the offset of -31 steps, offsetting
the +1 octave of the Pianoteq on channel 2.

Now we can play with a range of 6 octaves using 2 instances of Pianoteq
listening to 2 different channels.

This feature can also be used 'normally' to create keyboard
splits where each hand plays a different patch.

Any MIDI CCs received will be sent to all active channels at once.
As such, if you're using two instances of Pianoteq, it is crucial
to turn off the sustain pedal noise on either one of the VSTs
as there will be double the sustain pedal noise otherwise. Delicious.

## Other Settings

### Slide modes

#### Fixed slide

Enter `slide 0` to set the Slide amount to 0 for all notes
no matter the Slide input. Values 0-127 are allowed.

#### Press slide

Enter `slide prs` to mirror the Press dimension
to the Slide dimension.

#### Relative slide (default)

Enter `slide rel` to emulate [relative slide mode](https://support.roli.com/support/solutions/articles/36000025050-slide-absolute-vs-relative)

#### Absolute slide

Enter `slide abs` to forward the raw 
[absolute slide](https://support.roli.com/support/solutions/articles/36000025050-slide-absolute-vs-relative) 
messages unchanged.

#### Bipolar slide

Enter `slide bip` to emulate bipolar slide mode.
Initial Strike will yield a Slide value of 0, and sliding
all the way to either to top or bottom will yield the max Slide value of
127.

## Seaboard Map `.sbmap` file format

The mapper loads `.sbmap` files to assign a mapping to the seaboard.
If `mappings/default.sbmap` exists, it will load that mapping on
startup.

Each line of the .sbmap file can either be a descriptive comment,
a comment, or key split data.

Mappings are meant to be generated algorithmically with a script.
Take a look at https://github.com/euwbah/microtonal-seaboard/blob/master/mapping_generator/edo31.py
for an example.

### `/ descriptive comment`

Lines that begin with `/` will be printed in the console
when the mapping is loaded.

### `# comment`

Lines that begin with `#` will be ignored entirely

### Key split data

This line will describe how to split one key.

The values of the key split data are to be separated by spaces
or tabs, and are presented in the following format:

`<note> <p1> <c1> <s1> (<p2> <c2> <s2> ... <pn> <cn> <sn>)`

- `note`: 12edo note name of the key that this split applies to
- `pn`: a cc74 (slide) value representing the exclusive upper bounds
   of the nth vertical split point
- `cn`: (for MPE mode) the cents offset of the output note with respect to the
   key's original tuning in 12 edo.
- `sn`: (for MIDI mode) the output MIDI note represented as number of
   steps from the note A4.
  
Take note of the following constraints:

1. Key split data lines must have at least one split point.
2. The split points must be presented in order of increasing 
   cc74 (Slide) values
3. The final split point must always be 128 representing the
   maxima of the cc74 value range.
4. You can leave out notes in the mapping file. Not all 
   of them have to be mapped. If a note is left out, it
   will take on default behaviour.

For example, this is line 92 of the default 31 edo mapping:

`A4    30 -38.7097   -1  50   0.0000    0  73  38.7097    1  98   0.0000    0 128  38.7097    1`

The first value of the line, `A4` is the note name of which this
split data pertains to. The split information only applies to this
one key. Capitalisation does not matter.

After this, the values are presented in groups of threes.

The value `30` represents that the following tuning data only applies
when the Slide value (CC74) is below 30 (exclusive). This is the area
right at the bottom of the white keys on the seaboard.

The next value `-38.7097` represents the cent offset of this note
with respect to the 12 edo equivalent on the same key.
In 31 edo, this is the note A-down. The cent offset is used to 
calculate the amount of pitch bend to send when in MPE mode.

The final value of the triple is `-1`, and this says that the
output of this key when in MIDI mode is 1 note below A4 (that is, Ab4).

Looking at the next 3 values, `50 0.0000 0`, tells us that for the
Slide values 30-49 (inclusive), which is the middle section of the
white key, we will apply a tuning offset of 0 cents in MPE mode,
and an output of A4 in MIDI mode.
In 31 edo, this is the note A-natural.

The next 3 values, `73 38.7097 1` gives us the note A-up, and will
be applied for Slide values 50-72 (inclusive), which is the part of
the white key right below where the black keys begin.

### Huh?

Don't worry if this is all to cryptic. If you want a mapping for your
seaboard, simply [file an issue](https://github.com/euwbah/microtonal-seaboard/issues/new)
with the "Mapping Request" label, detailing:

- The tuning system (+ base tuning frequency)
- The mapping points, e.g.: 
  _"white key: down = 0-29, natural = 30-55, up = 56-127_
- If the tuning system is meant to work with MIDI-only synths
  (e.g. Pianoteq/Kontakt/ZynSubAddFX), which 12 edo note to 
  anchor the tuning system to.

I will try my best to get it done :)