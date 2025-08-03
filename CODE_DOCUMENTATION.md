# LinnStrument Firmware Code Documentation

This document provides a comprehensive overview of the LinnStrument firmware source code.

## 1. High-Level Architecture

The LinnStrument firmware is an Arduino-based C++ application running on an Arduino Due. It's a real-time system that continuously scans the touch surface, processes user input, and sends MIDI messages. The architecture is modular, with different functionalities encapsulated in separate `.ino` files that are included in the main `linnstrument-firmware.ino` file.

The core components of the firmware are:

*   **Touch Sensor Scanning:** The firmware continuously scans the touch-sensitive surface to detect touches, their position (X and Y), and pressure (Z). This is handled in `ls_sensor.ino`.
*   **Touch Handling:** Once a touch is detected, `ls_handleTouches.ino` processes it. This includes debouncing, calculating velocity, and determining the musical note to be played.
*   **MIDI Engine:** The MIDI engine, primarily in `ls_midi.ino`, is responsible for generating and sending MIDI messages based on the user's performance. It supports various MIDI modes, including MPE (MIDI Polyphonic Expression).
*   **Sequencer:** The firmware includes a polyphonic step sequencer (`ls_sequencer.ino`) that can record, play, and edit musical patterns.
*   **LED Feedback:** The LEDs on the LinnStrument's surface provide visual feedback to the user. `ls_leds.ino` controls the LEDs to show notes, settings, and sequencer patterns.
*   **Settings Management:** The device's settings are managed in `ls_settings.ino` and can be stored in flash memory using the `DueFlashStorage` library.
*   **Display Modes:** The LinnStrument has various display modes for changing settings, selecting presets, etc. These are managed in `ls_displayModes.ino`.

The main execution flow is controlled by the `loop()` function in `linnstrument-firmware.ino`. This function continuously scans the sensor, processes touches, and updates the LEDs and other system components.

## 2. File Descriptions

Here's a breakdown of the key `.ino` files in the project:

*   **`linnstrument-firmware.ino`**: The main entry point of the firmware. It includes all other `.ino` files, defines global constants and data structures, and contains the `setup()` and `loop()` functions.
*   **`ls_arpeggiator.ino`**: Implements the arpeggiator functionality.
*   **`ls_calibration.ino`**: Handles the calibration of the touch sensor.
*   **`ls_clock.ino`**: Manages the internal and external MIDI clock for tempo synchronization.
*   **`ls_displayModes.ino`**: Contains the logic for the different display modes, allowing the user to view and edit various settings.
*   **`ls_handleTouches.ino`**: This is a crucial file that processes the raw touch data from the sensor. It handles touch detection, release, and movement, and it's where the musical interpretation of touches begins.
*   **`ls_leds.ino`**: Controls the LEDs on the LinnStrument's surface. It provides functions for setting the color and state (on, off, blinking) of individual LEDs.
*   **`ls_lowRow.ino`**: Implements the special functionalities of the low row of pads, which can be configured for different purposes like sustain, arpeggiator control, etc.
*   **`ls_midi.ino`**: Manages all MIDI communication. It sends MIDI messages for notes, MPE data, and control changes. It also handles incoming MIDI messages.
*   **`ls_sequencer.ino`**: Implements the step sequencer. It manages sequencer state, patterns, steps, and events.
*   **`ls_settings.ino`**: Handles the device's settings, including loading from and saving to flash memory.
*   **`ls_sensor.ino`**: Interfaces with the touch sensor hardware to read the raw touch data.
*   **`ls_switches.ino`**: Manages the foot switches and panel switches.
*   **`user_firmware_mode.txt`**: A description of the user firmware mode. Note: this is a .txt file, not a .ino file.
*   **`libraries/DueFlashStorage`**: A library for reading and writing data to the flash memory of the Arduino Due.
## 3. Key Data Structures

*   **`TouchInfo`**: Defined in `linnstrument-firmware.ino`, this struct holds all the information about a single touch on the surface, including its raw and calibrated coordinates (X, Y, Z), note, channel, velocity, and state (e.g., `touchedCell`, `untouchedCell`). It's a large, bit-packed struct designed to be memory-efficient.

*   **`SplitSettings`**: Also in `linnstrument-firmware.ino`, this struct contains the settings for a single split, such as MIDI mode, channels, bend range, and colors. The LinnStrument can have two splits, allowing the user to play two different sounds on different parts of the surface.

*   **`GlobalSettings`**: This struct holds the global settings that apply to the entire instrument, like the split point, active note lights, and switch assignments.

*   **`StepEvent`**: Defined in `linnstrument-firmware.ino`, this struct represents a single event within a sequencer step. It's a bit-packed struct that stores the note, duration, velocity, pitch offset, and timbre. The data is packed into a 6-byte array to save memory. Here's a breakdown of the bit fields:
    *   `note` (7 bits): The MIDI note number (0-127).
    *   `duration` (10 bits): The duration of the note in 24 PPQ ticks.
    *   `velocity` (7 bits): The note-on velocity (1-127).
    *   `pitchOffset` (8 bits, signed): The pitch bend offset in semitones.
    *   `timbre` (7 bits): The timbre value (Y-axis), typically mapped to a CC message.
    *   `row` (3 bits): The row on which the note was played.

*   **`StepData`**: This struct, also in `linnstrument-firmware.ino`, holds all the events for a single step in the sequencer. It's an array of `StepEvent` structs, with `MAX_SEQUENCER_STEP_EVENTS` defining the polyphony per step.

*   **`SequencerPattern`**: This struct defines a single sequencer pattern, containing the step data for all steps (`MAX_SEQUENCER_STEPS`), step size, direction, and other pattern-level settings.

*   **`StepSequencerState`**: Located in `ls_sequencer.ino`, this struct manages the real-time state of the sequencer for one split, including the current position, running state, and the state of each active event (`StepEventState`).

## 4. Core Logic Flow

1.  **Initialization (`setup()`)**: In `linnstrument-firmware.ino`, the `setup()` function initializes the hardware (SPI, MIDI ports), loads settings from flash, and sets up the initial state of the device. It performs a series of checks at startup to detect if the user is holding down certain buttons, which can trigger special modes like firmware update or global reset.

2.  **Main Loop (`loop()`)**: The `loop()` function is the heart of the firmware. It's designed to be non-blocking to ensure real-time performance. It continuously performs the following actions:
    *   **Sensor Scan**: The firmware iterates through each cell of the touch surface one by one (`nextSensorCell()`). For each cell, it selects the corresponding row and column via SPI and reads the raw X, Y, and Z values from the sensor's ADC.
    *   **Touch Processing**: For the currently selected cell, it compares the new sensor readings with the previous state to detect changes.
        *   If a **new touch** is detected (`handleNewTouch()` in `ls_handleTouches.ino`), it calculates the initial velocity based on the rate of change of the pressure (Z). It then determines the note to play based on the cell's position and the current split's settings. Finally, it triggers a `noteOn` MIDI event.
        *   If an **existing touch** is updated (`handleXYZupdate()`), it checks for changes in the X, Y, or Z values. If a significant change is detected, it sends out the corresponding MPE MIDI messages:
            *   **X-axis (Pitch Bend)**: A change in the X position is translated into a MIDI pitch bend message.
            *   **Y-axis (Timbre)**: A change in the Y position is sent as a CC message or channel pressure, depending on the settings.
            *   **Z-axis (Pressure)**: A change in pressure is sent as polyphonic aftertouch or channel pressure.
        *   If a **touch is released** (`handleTouchRelease()`), it triggers a `noteOff` MIDI event.
    *   **Continuous Tasks**: To avoid blocking the main loop, long-running or periodic tasks are handled in the `performContinuousTasks()` function. This function is called every few iterations of the main loop. It's responsible for:
        *   Refreshing the LEDs (`checkRefreshLedColumn()`).
        *   Handling pending MIDI output (`handlePendingMidi()`).
        *   Processing incoming MIDI messages (`handleMidiInput()`).
        *   Advancing the arpeggiator (`performCheckAdvanceArpeggiator()`).
        *   Advancing the sequencer (`performCheckAdvanceSequencer()`).
        *   Checking the foot switches.

3.  **MIDI Handling**:
    *   **Outgoing MIDI**: Functions like `midiSendNoteOn()`, `midiSendPitchBend()`, etc., are called from the touch handling logic. These functions don't send the MIDI data directly. Instead, they add the data to a FIFO queue (`midiOutQueue`).
    *   **MIDI Queue**: The `handlePendingMidi()` function, called from `performContinuousTasks()`, is responsible for sending the messages from the queue over the selected MIDI port (USB or DIN). This queuing mechanism prevents the main loop from being blocked by slow MIDI communication and helps to ensure that MIDI messages are sent with the correct timing.
    *   **Incoming MIDI**: The `handleMidiInput()` function is also called from `performContinuousTasks()` to read and process any incoming MIDI data from the serial port. This can include MIDI clock, note data, or CC messages for controlling the LinnStrument's parameters remotely.
## 5. Sequencer Internals

The sequencer is a powerful feature of the LinnStrument firmware. Here's how it works:
*   **State Management**: The `StepSequencerState` struct (`ls_sequencer.ino`) holds the current state of the sequencer for each split. This includes whether it's running, the current position, and the state of each event being played.
*   **Patterns and Steps**: A `SequencerProject` contains two `StepSequencer` instances (one for each split). Each `StepSequencer` has multiple `SequencerPattern`s. Each pattern is an array of `StepData`, and each `StepData` contains an array of `StepEvent`s. This hierarchical structure allows for complex polyphonic and expressive sequences.
*   **Clocking**: The sequencer is advanced by the `checkAdvanceSequencer()` function, which is called from `performContinuousTasks()`. It uses the `clock24PPQ` (24 pulses per quarter note) counter from `ls_clock.ino` to determine when to advance to the next step.
*   **Playback**: When the sequencer advances to a new step, it iterates through the `StepEvent`s for that step and sends the corresponding `noteOn` MIDI messages. It also keeps track of the duration of each event and sends a `noteOff` when the duration has elapsed.
*   **Editing**: The sequencer has a UI for editing patterns. When in editing mode, touching the pads on the surface can add, remove, or modify events in the current pattern. The `handleSequencerTouch()` function in `ls_sequencer.ino` handles these editing actions.
