# Sequencer Enhancement Plan

This document outlines a plan to enhance the LinnStrument's built-in sequencer to be more like the Elektron Digitakt's sequencer.

## Analysis and Decision

After analyzing the existing LinnStrument sequencer and the features of the Elektron Digitakt, the decision is to **enhance the existing sequencer**.

The current sequencer is already a powerful, expressive, and polyphonic step sequencer that is deeply integrated with the LinnStrument's hardware. Rewriting it from scratch would be a major undertaking and would likely lead to losing some of the existing functionality.

The key features of the Digitakt that are missing from the LinnStrument's sequencer are:

*   **Conditional Triggers:** The ability to set rules for when a step will trigger (e.g., probability, play every 4th cycle, etc.).
*   **Extensive Parameter Locks:** The ability to lock any sound parameter on a specific step. The LinnStrument sequencer already locks expressive data (X, Y, Z), but the Digitakt's parameter locks are more general.
*   **Micro-timing:** The ability to nudge steps off the grid for more complex rhythms.

By enhancing the existing sequencer with these features, we can get the best of both worlds: the expressive power of the LinnStrument and the pattern-creation capabilities of the Digitakt.

## Implementable Features

The following is a list of features that I am confident I can implement correctly by extending the existing sequencer code.

### 1. Conditional Triggers

I will add a new data structure to each step event to store a "condition". This condition will be evaluated when the sequencer is about to play a step, and the step will only be played if the condition is met.

**Implementation Plan:**

1.  **Add a `condition` field to the `StepEvent` struct.** This field will be an enum that represents the type of condition (e.g., `ALWAYS`, `PROBABILITY`, `FILL`, `EVERY_X_CYCLES`). It will also have a value associated with it (e.g., the probability percentage, the number of cycles).
2.  **Modify the sequencer logic to evaluate the condition.** In `ls_sequencer.ino`, before a step is played, I will add a check for the condition.
3.  **Create a UI for setting conditions.** I will use the LinnStrument's grid to create a UI for setting the condition for a selected step. This will likely involve a new display mode.

### 2. Basic Parameter Locks

I can extend the existing parameter locking mechanism to support more parameters. The sequencer already locks expressive data, so the foundation is there. I will start by adding the ability to lock the following parameters:

*   **Sample Selection:** Change the sample played on a specific step. (This would require a sample-based instrument to be used with the LinnStrument).
*   **Filter Cutoff and Resonance:** If the sound generator has a filter.
*   **Envelope Parameters:** Attack, decay, sustain, release.

**Implementation Plan:**

1.  **Extend the `StepEvent` struct** to store the locked parameter values.
2.  **Modify the sound generation code** to use the locked parameter values from the `StepEvent` if they exist.
3.  **Create a UI for setting parameter locks.** Similar to conditional triggers, this will require a new display mode where the user can select a step and then use the faders to set the parameter locks.

## Hard-to-Implement Features

The following features are more complex and would require more significant changes to the existing codebase.

### 1. Micro-timing

**Challenge:** The current sequencer is based on a fixed grid of 24 PPQN (pulses per quarter note). Implementing micro-timing would require a higher-resolution clock or a different way of representing time.

**Brief Plan:**

1.  **Increase the sequencer's timing resolution.** This would involve changing the clock division and updating all the timing-related calculations in the firmware. A significant refactoring would be needed.
2.  **Store a "nudge" value for each step.** This value would represent the offset from the grid.
3.  **Update the sequencer logic** to apply the nudge value when playing a step.
4.  **Create a UI for setting the nudge value.** This could be done with a fader when a step is selected.

### 2. Per-Track Track Lengths

**Challenge:** The current sequencer has a single length for the entire pattern. Implementing per-track track lengths would require a major change to the sequencer's data structures and playback logic.

**Brief Plan:**

1.  **Add a `length` property to each track** in the sequencer's data structure.
2.  **Modify the sequencer's playback logic** to handle different track lengths. This would involve keeping track of the position of each track independently.
3.  **Create a UI for setting the track length.** This could be done in a settings page for each track.

### 3. Full-featured Parameter Locks (for all parameters)

**Challenge:** While locking a few parameters is feasible, locking *any* parameter would require a more generic mechanism. This would involve a way to reference any parameter in the sound engine from the sequencer.

**Brief Plan:**

1.  **Implement a generic parameter addressing system.** This could be a system of IDs or names for each parameter in the sound engine.
2.  **Create a data structure for parameter locks** that can store a parameter ID and a value.
3.  **Modify the `StepEvent` struct** to include a list of parameter locks.
4.  **Update the sound engine** to check for and apply parameter locks before rendering a note.
5.  **Create a UI for selecting a parameter and setting its lock.** This would be the most challenging part, as it would require a way to browse and select from a large number of parameters.
