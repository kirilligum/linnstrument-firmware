import unittest
import mido
from linnstrument import LinnStrument, MidiMode, LoudnessExpression, TimbreExpression, ConditionType

class TestLinnStrument(unittest.TestCase):

    def setUp(self):
        self.midi_messages = []
        def midi_callback(msg):
            self.midi_messages.append(msg)
        self.ls = LinnStrument(midi_out_callback=midi_callback)

    def test_initialization(self):
        self.assertEqual(self.ls.model, 200)
        self.assertEqual(self.ls.num_cols, 26)
        self.assertEqual(self.ls.num_rows, 8)

    def test_touch_release(self):
        touch_id = self.ls.touch(5, 2, 100)
        self.assertIsNotNone(touch_id)
        self.assertEqual(len(self.midi_messages), 1)

        note_on_msg = self.midi_messages[0]
        self.assertEqual(note_on_msg.type, 'note_on')
        self.assertEqual(note_on_msg.velocity, 100)

        note_number = self.ls._get_note_number(5, 2)
        self.assertEqual(note_on_msg.note, note_number)

        self.ls.release(touch_id)
        self.assertEqual(len(self.midi_messages), 2)

        note_off_msg = self.midi_messages[1]
        self.assertEqual(note_off_msg.type, 'note_off')
        self.assertEqual(note_off_msg.note, note_number)

    def test_melody(self):
        notes = [(5, 2, 100), (6, 2, 100), (7, 2, 100)]
        touch_ids = []
        for col, row, z in notes:
            touch_id = self.ls.touch(col, row, z)
            touch_ids.append(touch_id)

        # Release the notes
        for touch_id in touch_ids:
            self.ls.release(touch_id)

        self.assertEqual(len(self.midi_messages), 6)
        self.assertEqual(self.midi_messages[0].type, 'note_on')
        self.assertEqual(self.midi_messages[1].type, 'note_on')
        self.assertEqual(self.midi_messages[2].type, 'note_on')
        self.assertEqual(self.midi_messages[3].type, 'note_off')
        self.assertEqual(self.midi_messages[4].type, 'note_off')
        self.assertEqual(self.midi_messages[5].type, 'note_off')

    def test_slide(self):
        touch_id = self.ls.touch(5, 2, 100)
        self.ls.move(touch_id, 6, 3, 110)

        self.assertEqual(len(self.midi_messages), 4) # note_on, pitchwheel, cc, polytouch

        pitchwheel_msg = self.midi_messages[1]
        self.assertEqual(pitchwheel_msg.type, 'pitchwheel')

        # In this simple implementation, pitch bend is proportional to the horizontal distance
        # from the initial touch. (6 - 5) * (8191 / 24) = 341.29
        self.assertAlmostEqual(pitchwheel_msg.pitch, 341, delta=1)

        cc_msg = self.midi_messages[2]
        self.assertEqual(cc_msg.type, 'control_change')
        self.assertEqual(cc_msg.control, self.ls.timbre_cc)
        # y_val = int((3 / 7) * 127) = 54
        self.assertEqual(cc_msg.value, 54)

        polytouch_msg = self.midi_messages[3]
        self.assertEqual(polytouch_msg.type, 'polytouch')
        self.assertEqual(polytouch_msg.value, 110)

    def test_one_channel_mode(self):
        self.ls.midi_mode = MidiMode.ONE_CHANNEL

        touch_id1 = self.ls.touch(5, 2, 100)
        touch_id2 = self.ls.touch(6, 2, 100)

        self.assertEqual(len(self.midi_messages), 2)
        self.assertEqual(self.midi_messages[0].channel, self.ls.main_channel)
        self.assertEqual(self.midi_messages[1].channel, self.ls.main_channel)

        self.ls.release(touch_id1)
        self.ls.release(touch_id2)


class TestSequencer(unittest.TestCase):
    def setUp(self):
        self.midi_messages = []
        def midi_callback(msg):
            self.midi_messages.append(msg)
        self.ls = LinnStrument(midi_out_callback=midi_callback)
        self.seq = self.ls.sequencer

    def test_simple_sequence(self):
        # Program a simple sequence
        pattern = self.seq.patterns[self.seq.current_pattern]
        pattern.steps[0].events[0].note = 60
        pattern.steps[0].events[0].velocity = 100
        pattern.steps[0].events[0].duration = 5

        pattern.steps[2].events[0].note = 62
        pattern.steps[2].events[0].velocity = 100
        pattern.steps[2].events[0].duration = 5

        # Start the sequencer
        self.seq.running = True

        # Run the sequencer for a few ticks
        for _ in range(20):
            self.ls.tick()

        # Check the MIDI output
        self.assertGreater(len(self.midi_messages), 3)

        note_on_1 = self.midi_messages[0]
        self.assertEqual(note_on_1.type, 'note_on')
        self.assertEqual(note_on_1.note, 60)

        note_off_1 = self.midi_messages[1]
        self.assertEqual(note_off_1.type, 'note_off')
        self.assertEqual(note_off_1.note, 60)

        note_on_2 = self.midi_messages[2]
        self.assertEqual(note_on_2.type, 'note_on')
        self.assertEqual(note_on_2.note, 62)

    def test_probability_trigger(self):
        # Program a note with 0% probability
        pattern = self.seq.patterns[self.seq.current_pattern]
        event = pattern.steps[0].events[0]
        event.note = 60
        event.velocity = 100
        event.duration = 5
        event.condition = ConditionType.PROBABILITY
        event.condition_value = 0

        self.seq.running = True
        for _ in range(10):
            self.ls.tick()

        self.assertEqual(len(self.midi_messages), 0)

        # Program a note with 100% probability
        self.seq.position = 0
        self.seq.ticks_until_next_step = 0
        event.condition_value = 100
        for _ in range(10):
            self.ls.tick()

        self.assertGreater(len(self.midi_messages), 0)
        self.assertEqual(self.midi_messages[0].type, 'note_on')

    def test_parameter_lock(self):
        # Program a note with a parameter lock
        pattern = self.seq.patterns[self.seq.current_pattern]
        event = pattern.steps[0].events[0]
        event.note = 60
        event.velocity = 100
        event.duration = 5
        event.locked_param_id = 1 # Filter cutoff
        event.locked_param_value = 123

        self.seq.running = True
        for _ in range(10):
            self.ls.tick()

        self.assertGreater(len(self.midi_messages), 1)

        cc_msg = self.midi_messages[0]
        self.assertEqual(cc_msg.type, 'control_change')
        self.assertEqual(cc_msg.control, 74)
        self.assertEqual(cc_msg.value, 123)

        note_on_msg = self.midi_messages[1]
        self.assertEqual(note_on_msg.type, 'note_on')


if __name__ == '__main__':
    unittest.main()
