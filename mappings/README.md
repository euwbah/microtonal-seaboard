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

## Velocity curve `.vel` file format

The `vel` command lets you load a `.vel` file to set velocity curves per cc74 (vertical slide) regions per physical key (there are 49 on the RISE 49). You can specify as many vertical regions as you want per key, but too many vertical regions will increase latency for that key in particular.

The file format is as follows:
```
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

```
<CC74 least inclusive upper bound 1> <Curve index 1> <CC74 least inclusive upper bound 2> <Curve index 2> ...
```

For example,

```
50 0 127 1
```

says that for that key, any CC74 value &le; 50 will use velocity curve 0 (first velocity curve), and CC74 values from 51--127 will use velocity curve 1 (second curve).

- CC74 upper bounds should be specified in **strictly increasing order**
- The **last CC74 number should be 127**.
- **Curve indices are 0-based** (0 is the first velocity curve).
- While there is no limit to the number of CC74 vertical partitions, it is highly recommended to **stick to as few as possible** to reduce performance overhead.


After specifying vertical regions and their curves for 49 keys, we have 1 line per velocity curve.

The curve data is formatted as 128 space separated integers ranging from 0-127

```
<Output velocity for vel 0> <vel for vel 1> <vel for vel 2> ... <vel for vel 127>
```

E.g., writing

```
127 126 125 124 123 ... 4 3 2 1 0
```

will yield an inverted velocity curve where the higher the input velocity (harder you press), the lower the output velocity (softer the note).

Each Seaboard comes with its own inconsistencies and sensitive/dead regions, so you will need to experiment to set velocity curves for your own Seaboard.

You can use the `debug` command to toggle debug messages that will show the cc74 and velocity of note on events and which velocity curve is being applied.
