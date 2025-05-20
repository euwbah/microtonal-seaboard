"""
Velocity curve settings.

A velocity curve is a list of 128 integers that maps velocity values from 0-127.

Several velocity curves are defined
"""

import os
from typing import Optional


class VelocityCurves:
    def __init__(self, file_path: Optional[str] = None):
        """
        Load a velocity curve from a file. If none, sets the default curve.
        """
        self.vel_curves: list[list[int]] = []
        """
        An array of velocity curves.

        E.g., vel_curves[0][35] = 40 will cause velocity curve 0 to output vel 40 when input velocity is 35.

        Each velocity curve is a list of 128 integers, the index is the input
        velocity and the value at that index is the output velocity.
        """
        self.key_vel_curves: Optional[list[list[tuple[int, int]]]] = None
        """
        One list of tuples for each of the 49 keys on the Rise 49.

        If None, the default velocity curve is used.

        Otherwise, each entry is a tuple (CC74 least inclusive upper bound, curve index)

        where curve index refers to the index in vel_curves.
        """

        if file_path is not None:
            self.load(file_path)
            self.file_name = os.path.basename(file_path)
        else:
            self.set_default()
            self.file_name = 'default'

    def set_default(self):
        self.vel_curves = []
        self.key_vel_curves = None

    def load(self, file_path: str):
        """
        Load a velocity curve from a file.

        File format:

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

        Each key data line is formatted as space separated numbers:

        <CC74 least inclusive upper bound 1> <Curve index 1> <CC74 least inclusive upper bound 2> <Curve index 2> ...

        CC74 upper bounds should be specified in strictly increasing order. The last CC74 number should be 127.
        Curve indices are 0-based. While there is no limit to the number of CC74 vertical partitions, it is
        highly recommended to stick to as few as possible to reduce performance overhead.

        Each curve data line is formatted as 128 space separated integers from 0-127
        <Output velocity for vel 0> <vel for vel 1> <vel for vel 2> ... <vel for vel 127>

        :param filename: The name of the file to load.
        """

        with open(file_path, 'r') as f:
            try:
                kvc = []
                curves = []
                max_curve_index = -1
                for key in range(0, 49):
                    line_parts = [p for p in f.readline().strip().split(' ') if len(p.strip()) != 0]
                    assert len(line_parts) > 0, f'Key {key} (line {key + 1}) is empty'
                    assert len(line_parts) % 2 == 0, f'Key {key} (line {key + 1}) has invalid format'
                    prev_cc74 = 0
                    cc74_index_pairs = []
                    for i in range(0, len(line_parts), 2):
                        try:
                            cc74 = int(line_parts[i])
                            if not 0 <= cc74 <= 127:
                                raise ValueError
                        except ValueError:
                            print(f'Key {key} (line {key + 1}) has invalid CC74 value {line_parts[i]}. Must be an integer between 0-127')
                            print('Using default velocity curve')
                            self.set_default()
                            return

                        try:
                            curve_index = int(line_parts[i + 1])
                            if curve_index < 0:
                                raise ValueError
                        except ValueError:
                            print(f'Key {key} (line {key + 1}) has invalid curve index {line_parts[i + 1]}. Must be an integer >= 0')
                            print('Using default velocity curve')
                            self.set_default()
                            return

                        if curve_index > max_curve_index:
                            max_curve_index = curve_index

                        assert curve_index >= 0, f'Key {key} (line {key + 1}) has invalid curve index {curve_index}'

                        assert cc74 > prev_cc74, f'Key {key} (line {key + 1}) has invalid CC74 value {cc74} which is <= previous {prev_cc74}. Must be specified in strictly increasing order.'
                        cc74_index_pairs.append((cc74, curve_index))

                    assert cc74_index_pairs[-1][0] == 127, f'Key {key} (line {key + 1}) has invalid last CC74 value {cc74_index_pairs[-1][0]}. The last CC74 value must be 127.'

                    kvc.append(cc74_index_pairs)

                while (line := f.readline()) != '':
                    line_parts = [p for p in line.strip().split(' ') if len(p.strip()) != 0]
                    assert len(line_parts) == 128, f'Curve {len(curves)} (line {len(curves) + 50}) has invalid format. Expected 128 space-separated integers between 0-127 (incl.)'
                    try:
                        curve = [int(p) for p in line_parts]
                    except ValueError:
                        print(f'Curve {len(curves)} (line {len(curves) + 50}) has invalid format. Expected 128 space-separated integers between 0-127 (incl.)')
                        print('Using default velocity curve')
                        self.set_default()
                        return
                    assert all(0 <= p <= 127 for p in curve), f'Curve {len(curves)} (line {len(curves) + 50}) has invalid format. Velocity values must be between 0-127 (incl.)'
                    curves.append(curve)

                assert len(curves) > max_curve_index, f'Required {max_curve_index + 1} velocity curves to be defined, but only {len(curves)} were found. Please check the file format.'

                print(f'Loaded {len(curves)} velocity curves for 49 keys.')
                self.key_vel_curves = kvc
                self.vel_curves = curves
            except AssertionError as e:
                print(f'Vel curve format error: {e}')
                print('Using default velocity curve')
                self.set_default()

    def get_velocity(self, midi_note: int, velocity: int, octave_offset: int, cc74: int, debug: bool = False) -> int:
        """
        Get the output velocity for a given input velocity, midi note, and cc74 value.
        """
        if self.key_vel_curves is None:
            return velocity

        physical_key_idx = midi_note - 12 * (octave_offset) # 0 is the lowest key on the seaboard, 48 is the highest.

        if physical_key_idx < 0 or physical_key_idx > 48:
            print(f'WARNING: physical key index {physical_key_idx} out of range. Try pressing the octave switch to update octave offset.')
            return velocity

        # find the curve index for the given cc74 value
        curve_index = 0
        for cc74_bound, idx in self.key_vel_curves[physical_key_idx]:
            if cc74 <= cc74_bound:
                curve_index = idx
                break

        if debug:
            print(f'Key {physical_key_idx} (midi {midi_note}, oct {octave_offset}) curve index {curve_index}, cc74 {cc74}')

        return self.vel_curves[curve_index][velocity]
