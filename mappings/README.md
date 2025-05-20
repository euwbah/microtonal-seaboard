# Seaboard Mappings & Velocity Curves

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
   of them have to be mapped in order for the program to work.
   The left-out notes will default to the standard behavior
   and tuning.

### Key split data example

For example, this is [line 92 of the default 31 edo mapping](https://github.com/euwbah/microtonal-seaboard/blob/master/mappings/default.sbmap#L92):

`A4    30 -38.7097   -1  50   0.0000    0  73  38.7097    1  98   0.0000    0 128  38.7097    1`

The first value of the line, `A4` is the note name of which this split data pertains to. The split
information only applies to this one key. Capitalisation does not matter.

After this, the values are presented in groups of threes.

The value `30` represents that the following tuning data only applies when the Slide value (CC74) is
below 30 (exclusive). This is the area right at the bottom of the white keys on the seaboard.

The next value `-38.7097` represents the cent offset of this note with respect to the 12 edo
equivalent on the same key. In 31 edo, this is the note A-down. The cent offset is used to calculate
the amount of pitch bend to send when in MPE mode.

The final value of the triple is `-1`, and this says that the output of this key when in MIDI mode
is 1 note below A4 (that is, Ab4).

Looking at the next 3 values, `50 0.0000 0`, tells us that for the Slide values 30-49 (inclusive),
which is the middle section of the white key, we will apply a tuning offset of 0 cents in MPE mode,
and an output of A4 in MIDI mode. In 31 edo, this is the note A-natural.

The next 3 values, `73 38.7097 1` gives us the note A-up, and will be applied for Slide values 50-72
(inclusive), which is the part of the white key right below where the black keys begin.

### Huh?

Don't worry if this is all too cryptic. If you want a mapping for your seaboard, simply [file an
issue](https://github.com/euwbah/microtonal-seaboard/issues/new) with the "Mapping Request" label,
detailing:

- The tuning system (+ base tuning frequency)
- The mapping points, e.g.: _"white key: down = 0-29, natural = 30-55, up = 56-127_
  - To know exactly what Slide values are being sent when you press a key at a certain vertical
    position, you can use a [MIDI monitoring tool](https://www.morson.jp/pocketmidi-webpage/) and
    filter to view only Control Change messages that are CC74.

- If the tuning system is meant to work with MIDI-only synths (e.g. Pianoteq/Kontakt/ZynAddSubFX),
  which 12 edo note to anchor the tuning system to.

I will try my best to get it done :)

## Velocity curve `.vel` file format

The `vel` command lets you load a `.vel` file to set velocity curves per cc74 (vertical slide) regions per physical key (there are 49 on the RISE 49). You can specify as many vertical regions as you want per key, but too many vertical regions will increase latency for that key in particular.

The file format is as follows:

```txt
<Key 0 (lowest C, octave -1 relative to octave switch)>
<Key 1 C#>
...
<Key 47 B>
<Key 48 (highest C, octave 4 relative to octave switch)>
<Curve 0>
<Curve 1>
...
```

There should be exactly 49 + C lines (C is the number of velocity curves). No empty lines or comments allowed.

Each of the 49 `<Key>` lines are formatted as pairs of numbers, space separated:

```txt
<CC74 least inclusive upper bound 1> <Curve index 1> <CC74 least inclusive upper bound 2> <Curve index 2> ...
```

For example,

```txt
50 0 127 1
```

says that for that key, any CC74 value &le; 50 will use velocity curve 0 (first velocity curve), and CC74 values from 51--127 will use velocity curve 1 (second curve).

- CC74 upper bounds should be specified in **strictly increasing order**
- The **last CC74 number should be 127**.
- **Curve indices are 0-based** (0 is the first velocity curve).
- While there is no limit to the number of CC74 vertical partitions, it is highly recommended to **stick to as few as possible** to reduce performance overhead.


After specifying vertical regions and their curves for 49 keys, we have 1 line per velocity curve.

The curve data is formatted as 128 space separated integers ranging from 0-127

```txt
<Output velocity for vel 0> <vel for vel 1> <vel for vel 2> ... <vel for vel 127>
```

E.g., writing

```txt
127 126 125 124 123 ... 4 3 2 1 0
```

will yield an inverted velocity curve where the higher the input velocity (harder you press), the lower the output velocity (softer the note).

Each Seaboard comes with its own inconsistencies and sensitive/dead regions, so you will need to experiment to set velocity curves for your own Seaboard.

You can use the `debug` command to toggle debug messages that will show the cc74 and velocity of note on events and which velocity curve is being applied.

## Velocity curves

### Velocity curves for euwbah's Seaboard

See `euwbah.vel`

[Curve 0: Light touch for low sensitivity areas](https://www.desmos.com/calculator/scfo7kcuai)

```txt
13 17 20 22 24 26 28 29 31 33 34 36 37 38 40 41 42 44 45 46 48 49 50 51 52 53 55 56 57 58 59 60 61 62 63 64 65 65 66 67 67 68 69 70 70 71 72 72 73 74 74 75 76 76 77 78 78 79 80 81 81 82 83 83 84 85 85 86 87 87 88 89 90 90 91 92 92 93 94 94 95 96 96 97 98 98 99 100 101 101 102 103 103 104 105 105 106 107 107 108 109 110 110 111 112 112 113 114 114 115 116 116 117 118 118 119 120 121 121 122 123 123 124 125 125 126 127 127
```

[Curve 1: medium-light touch for medium-low sensitivity areas](https://www.desmos.com/calculator/o3wzney1qh)

```txt
3 6 8 10 12 14 15 17 19 20 21 23 24 26 27 28 29 31 32 33 34 35 37 38 39 40 41 42 43 44 46 47 48 49 50 51 52 53 54 55 56 57 58 59 60 61 62 63 64 65 66 67 68 68 69 70 71 72 73 74 75 76 77 78 78 79 80 81 82 82 83 84 85 85 86 87 88 88 89 90 91 92 92 93 94 95 95 96 97 98 98 99 100 101 102 102 103 104 105 105 106 107 108 109 109 110 111 112 112 113 114 115 115 116 117 118 119 119 120 121 122 122 123 124 125 125 126 127
```

Curve 2: Default velocity curve

```txt
0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31 32 33 34 35 36 37 38 39 40 41 42 43 44 45 46 47 48 49 50 51 52 53 54 55 56 57 58 59 60 61 62 63 64 65 66 67 68 69 70 71 72 73 74 75 76 77 78 79 80 81 82 83 84 85 86 87 88 89 90 91 92 93 94 95 96 97 98 99 100 101 102 103 104 105 106 107 108 109 110 111 112 113 114 115 116 117 118 119 120 121 122 123 124 125 126 127
```

[Curve 3:  Heavy touch for sensitive regions](https://www.desmos.com/calculator/bverl3ybw2)

```txt
0 1 1 1 2 2 2 3 3 3 4 4 5 5 6 6 7 7 8 8 9 9 10 11 11 12 13 13 14 15 15 16 17 18 18 19 20 21 22 22 23 24 25 26 27 28 28 29 30 31 32 33 34 35 36 37 38 39 40 41 42 43 44 45 46 47 48 49 50 51 53 54 55 56 57 58 59 60 62 63 64 65 66 68 69 70 71 72 74 75 76 77 79 80 81 83 84 85 86 88 89 90 92 93 94 96 97 98 100 101 103 104 105 107 108 110 111 112 114 115 117 118 120 121 123 124 126 127
```

[Curve 4: Very light touch for very low sensitivity areas](https://www.desmos.com/calculator/mrcpttdopu)

```txt
13 18 21 23 26 28 30 31 33 35 36 38 39 41 42 44 45 46 48 49 50 51 53 54 55 56 57 58 60 61 62 63 64 65 66 67 68 69 70 71 72 73 74 75 76 77 78 79 80 80 81 82 83 84 85 86 87 88 88 89 90 91 92 93 93 94 94 95 95 96 97 97 98 98 99 99 100 100 101 101 102 102 103 103 104 105 105 106 106 107 107 108 108 109 109 110 110 111 112 112 113 113 114 114 115 115 116 116 117 117 118 118 119 120 120 121 121 122 122 123 123 124 124 125 125 126 126 127
```
