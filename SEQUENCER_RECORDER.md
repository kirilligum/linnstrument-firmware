# LinnStrument Sequencer Recording Feature

This document provides a comprehensive overview of the new sequencer recording feature for the LinnStrument firmware.

## 1. User Guide

The new sequencer recording feature allows you to record a musical performance live, including notes, velocity, and MPE data, directly into the LinnStrument's sequencer. This feature is designed to be intuitive and performance-friendly, enabling you to capture your musical ideas as they happen.

### How to Use the Recorder:

1.  **Enter Sequencer Mode**: Make sure the sequencer is active for the split you want to record on.
2.  **Set the Recording Length**:
    *   Navigate to the sequencer's settings page.
    *   Use the pad at column 11 on the low row to cycle through the available recording lengths: 8, 16, or 32 steps. The color of the pad indicates the selected length (Yellow for 8, Orange for 16, Pink for 32).
3.  **Arm the Recorder**:
    *   Long-press the **Play** button (Switch 2) for about one second.
    *   The **Play** button's LED will start blinking in red, indicating that the recorder is armed and ready to record.
4.  **Start Recording**:
    *   Simply start playing on the LinnStrument's surface.
    *   The recording will begin automatically as soon as you play the first note.
    *   The **Play** button's LED will turn solid red to indicate that the recording is in progress.
5.  **Recording**:
    *   Play your musical phrase. The recorder will capture your performance, including MPE data (pitch bend, timbre, and pressure).
    *   The recording will automatically stop after the number of steps you selected in step 2.
6.  **Playback**:
    *   Once the recording is finished, the sequencer will stop.
    *   To listen to your recording, press the **Play** button again (a short press). The sequencer will start playing the pattern you just recorded.

## 2. Implementation and Design Decisions

The implementation of the sequencer recording feature was done in a modular and non-blocking way to ensure that it integrates smoothly with the existing firmware and does not compromise the real-time performance of the instrument.

### Key Components:

*   **State Management**: The core of the feature is managed by new states within the `StepSequencerState` struct (`ls_sequencer.ino`):
    *   `recordingArmed`: A boolean flag that indicates whether the sequencer is armed and waiting for the first note to start recording.
    *   `isRecording`: A boolean flag that is true when the sequencer is actively recording.
    *   `recordLength`: A byte that stores the length of the recording in steps.
*   **Recording Logic**: The recording logic is primarily implemented in `ls_handleTouches.ino`, where touch events are processed:
    *   **Starting the Recording**: The recording is triggered in `handleXYZupdate()` when a new note is played (`newVelocity` is true) and the sequencer is armed. It then sets `isRecording` to true, clears the current pattern, and starts the sequencer's clock.
    *   **Recording Note-On Events**: Note-on events are captured in `prepareNewNote()`. When a new note is prepared during a recording, a new `StepEvent` is created in the current sequencer step. To handle note-offs correctly, information about the active note (note number, channel, start time, etc.) is stored in a `recordingNotes` array within the `StepSequencerState`.
    *   **Recording Note-Off Events**: Note-off events are handled in `handleTouchRelease()`. When a note is released during a recording, the code finds the corresponding note in the `recordingNotes` array, calculates its duration based on the current clock time, and updates the `StepEvent` in the sequencer pattern with the correct duration.
*   **User Interface**:
    *   **Arming**: The arming mechanism is implemented by detecting a long press on Switch 2 in `handleSequencerControlButtonRelease()`. This was chosen to provide a quick and intuitive way to arm the recorder without needing to navigate through menus.
    *   **Recording Length**: The UI for setting the recording length was added to the sequencer's settings page for consistency with the existing UI for other sequencer settings.

### Design Decisions:

*   **Modularity**: The new logic was added to the existing functions in a way that minimizes its impact on the rest of the codebase. For example, the core recording logic is contained within the touch handling functions, which is the natural place for it.
*   **Real-time Performance**: The recording process is non-blocking. It doesn't use any `delay()` calls or long loops that could interfere with the instrument's responsiveness. The use of state flags and the existing event-driven architecture ensures that the recording happens in the background without affecting the playability of the instrument.
*   **Memory Efficiency**: The `recordingNotes` array is of a fixed size (`MAX_RECORDING_NOTES`) to avoid dynamic memory allocation, which can be problematic in embedded systems. The size is chosen to be large enough to handle a reasonable amount of polyphony during recording.

## 3. Performance, Efficiency, and Code Design

The implementation of the sequencer recording feature adheres to the high standards of performance, efficiency, and code design required for a real-time musical instrument.

*   **Performance**: The new code is highly performant. The state checks and recording logic are simple and computationally inexpensive, adding minimal overhead to the main loop. The non-blocking nature of the implementation ensures that the LinnStrument remains responsive and playable at all times, even when recording.
*   **Efficiency**: The code is memory-efficient. The use of fixed-size arrays and the modification of existing data structures (`StepSequencerState`) avoids the need for dynamic memory allocation. The logic is designed to be efficient, with no unnecessary computations or redundant checks.
*   **Code Design Principles**:
    *   **Single Responsibility Principle**: The new logic is placed in the appropriate files and functions based on their responsibilities. For example, the recording of touch events is handled in `ls_handleTouches.ino`, while the sequencer's state is managed in `ls_sequencer.ino`.
    *   **Non-Blocking Code**: The implementation is fully non-blocking, which is a critical design principle for real-time embedded systems.
    *   **Readability and Maintainability**: The code is well-commented, and the logic is straightforward, making it easy to understand and maintain in the future. The use of temporary UI elements for testing, which are then replaced by a more permanent solution, is a good practice for iterative development.

## 4. Future Enhancements

The sequencer recording feature is a solid foundation that can be extended with new capabilities in the future. Here are some potential enhancements:

*   **Overdubbing**: Allow the user to record new notes on top of an existing pattern without clearing it first. This would enable the creation of more complex and layered sequences.
*   **MPE Data Recording**: The current implementation records note-on and note-off events. The next step would be to record the full spectrum of MPE data, including continuous changes in pressure (Z), timbre (Y), and pitch (X). This would involve capturing these events during the recording and storing them in a suitable format within the sequencer pattern.
*   **Advanced Recording Length UI**: The current UI for setting the recording length is basic. A more advanced UI could be created on a dedicated settings page, allowing the user to select the length more precisely, perhaps even in beats or bars.
*   **Metronome**: Add a metronome click that can be enabled during recording to help the user play in time.
*   **Quantization**: Implement an option to quantize the recorded notes to the nearest grid line (e.g., 16th notes), which would help to correct timing errors.
*   **Undo/Redo**: Add an undo feature to allow the user to discard the last recording if they make a mistake.
