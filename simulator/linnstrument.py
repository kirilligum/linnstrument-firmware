import mido
from enum import Enum

class MidiMode(Enum):
    ONE_CHANNEL = 0
    CHANNEL_PER_NOTE = 1
    CHANNEL_PER_ROW = 2
    MPE = 3

class LoudnessExpression(Enum):
    POLY_AFTERTOUCH = 0
    CHANNEL_AFTERTOUCH = 1
    CC = 2

class TimbreExpression(Enum):
    POLY_AFTERTOUCH = 0
    CHANNEL_AFTERTOUCH = 1
    CC = 2

class Touch:
    """
    Represents a single touch on the LinnStrument surface.
    """
    def __init__(self, touch_id, col, row, z, note, channel):
        self.touch_id = touch_id
        self.col = col
        self.row = row
        self.z = z
        self.note = note
        self.channel = channel
        self.initial_col = col
        self.initial_row = row

class LinnStrument:
    """
    A simulator for the Roger Linn Design LinnStrument.
    """
    def __init__(self, model=200, midi_out_callback=None):
        if model not in [128, 200]:
            raise ValueError("Invalid model. Must be 128 or 200.")
        self.model = model
        self.num_cols = 17 if model == 128 else 26
        self.num_rows = 8

        self.midi_out_callback = midi_out_callback

        # Global settings
        self.split_active = False
        self.split_point = 13
        self.row_offset = 5 # fourths tuning

        # Per-split settings (for now, we'll just use one split)
        self.midi_mode = MidiMode.MPE
        self.main_channel = 1
        self.per_note_channels = list(range(2, 17))
        self.bend_range = 24
        self.send_x = True
        self.send_y = True
        self.send_z = True
        self.loudness_expression = LoudnessExpression.POLY_AFTERTOUCH
        self.loudness_cc = 11
        self.timbre_expression = TimbreExpression.CC
        self.timbre_cc = 74

        # State
        self.grid = [[None for _ in range(self.num_rows)] for _ in range(self.num_cols)]
        self.touches = {}
        self.next_touch_id = 0
        self.available_channels = self.per_note_channels.copy()

    def _send_midi(self, msg):
        if self.midi_out_callback:
            self.midi_out_callback(msg)
        else:
            print(f"Sending MIDI: {msg}")

    def _get_note_number(self, col, row):
        lowest_note = 30 # F#2
        note = lowest_note + (row * self.row_offset) + col -1
        return note

    def touch(self, col, row, z):
        """
        Simulates a new touch on the surface.
        """
        if not (0 <= col < self.num_cols and 0 <= row < self.num_rows):
            raise ValueError("Invalid column or row")
        if not (0 <= z <= 127):
            raise ValueError("Invalid pressure (z). Must be between 0 and 127.")

        if self.grid[col][row] is not None:
            # A touch already exists at this position
            return None

        touch_id = self.next_touch_id
        self.next_touch_id += 1

        note = self._get_note_number(col, row)

        if self.midi_mode == MidiMode.MPE:
            if not self.available_channels:
                return None # No available channels
            channel = self.available_channels.pop(0)
        elif self.midi_mode == MidiMode.CHANNEL_PER_NOTE:
            if not self.available_channels:
                return None # No available channels
            channel = self.available_channels.pop(0)
        else: # ONE_CHANNEL or CHANNEL_PER_ROW
            channel = self.main_channel

        touch = Touch(touch_id, col, row, z, note, channel)
        self.touches[touch_id] = touch
        self.grid[col][row] = touch_id

        # Send Note On
        velocity = z
        msg = mido.Message('note_on', note=note, velocity=velocity, channel=channel)
        self._send_midi(msg)

        return touch_id

    def move(self, touch_id, col, row, z):
        """
        Simulates moving an existing touch.
        """
        if touch_id not in self.touches:
            return

        touch = self.touches[touch_id]

        # Update grid if touch moves to a new cell
        if touch.col != col or touch.row != row:
            self.grid[touch.col][touch.row] = None
            self.grid[col][row] = touch_id

        touch.col = col
        touch.row = row
        touch.z = z

        # Send MIDI messages for X, Y, Z changes
        # X (Pitch Bend)
        if self.send_x:
            # A simple implementation: pitch bend is proportional to the horizontal distance from the initial touch
            bend = (col - touch.initial_col) * (8191 / self.bend_range)
            msg = mido.Message('pitchwheel', pitch=int(bend), channel=touch.channel)
            self._send_midi(msg)

        # Y (Timbre)
        if self.send_y:
            # A simple implementation: Y is mapped to a CC value
            y_val = int((row / (self.num_rows -1)) * 127)
            if self.timbre_expression == TimbreExpression.CC:
                msg = mido.Message('control_change', control=self.timbre_cc, value=y_val, channel=touch.channel)
                self._send_midi(msg)
            elif self.timbre_expression == TimbreExpression.POLY_AFTERTOUCH:
                 msg = mido.Message('polytouch', note=touch.note, value=y_val, channel=touch.channel)
                 self._send_midi(msg)
            elif self.timbre_expression == TimbreExpression.CHANNEL_AFTERTOUCH:
                 msg = mido.Message('aftertouch', value=y_val, channel=touch.channel)
                 self._send_midi(msg)


        # Z (Loudness)
        if self.send_z:
            if self.loudness_expression == LoudnessExpression.POLY_AFTERTOUCH:
                msg = mido.Message('polytouch', note=touch.note, value=z, channel=touch.channel)
                self._send_midi(msg)
            elif self.loudness_expression == LoudnessExpression.CHANNEL_AFTERTOUCH:
                msg = mido.Message('aftertouch', value=z, channel=touch.channel)
                self._send_midi(msg)
            elif self.loudness_expression == LoudnessExpression.CC:
                msg = mido.Message('control_change', control=self.loudness_cc, value=z, channel=touch.channel)
                self._send_midi(msg)


    def release(self, touch_id):
        """
        Simulates releasing a touch.
        """
        if touch_id not in self.touches:
            return

        touch = self.touches[touch_id]

        # Send Note Off
        msg = mido.Message('note_off', note=touch.note, velocity=0, channel=touch.channel)
        self._send_midi(msg)

        # Clean up
        self.grid[touch.col][touch.row] = None
        del self.touches[touch_id]

        if self.midi_mode in [MidiMode.MPE, MidiMode.CHANNEL_PER_NOTE]:
            self.available_channels.append(touch.channel)
            self.available_channels.sort()


if __name__ == '__main__':
    def print_midi(msg):
        print(f"MIDI Out: {msg}")

    ls = LinnStrument(midi_out_callback=print_midi)
    print(f"Created LinnStrument simulator for model {ls.model}")
    print(f"Grid size: {ls.num_cols}x{ls.num_rows}")
    print(f"MIDI Mode: {ls.midi_mode.name}")
    print(f"Bend Range: {ls.bend_range}")

    print("\n--- Testing touch, move, and release ---")
    touch_id = ls.touch(5, 2, 100)
    if touch_id is not None:
        ls.move(touch_id, 6, 2, 110)
        ls.release(touch_id)
