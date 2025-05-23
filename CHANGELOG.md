# Changelog

### v0.6.1

- Fixed autosplit not sending `ALL_CHANNELS` on/off/cc/pitchbend messages (e.g., in MIDI mode) if SPLIT was never configured before. Now autosplit will send `ALL_CHANNELS` on channel 1 by default.

### v0.6

- Update to Python 3.12, updated dependencies.
- Fixed Windows build batch script.
- Add per-key velocity curve configuration.

### v0.3.0

- Added config persistence with the `save` command.
- Fix minor text error when configuring splits
- Splits are fully tested and working with Pianoteq's multi-channel mapping feature.

### v0.2.2

- Fixed noticeable delay between note on and pitch bend retuning.
- Tested Strobe 2 and Equator compatibility.

### v0.2: Initial beta release
