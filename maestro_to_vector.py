import music21 as m21
import os
import json
from typing import List, Dict, Union, Any
import random

# --- Main Conversion Function ---


def midi_to_note_vector(midi_filepath: str) -> List[Union[int, List[int]]]:
    """
    Reads a MIDI file, parses it using music21, and returns a sequential
    vector of PITCH INTERVALS (deltas).

    The output structure is a list where each element is:
    - An integer (the interval in semitones) for a single Note.
    - A list of integers (intervals in semitones) for a Chord.

    Intervals are calculated relative to the previously occurring pitch. If the 
    previous event was a chord, the reference pitch is selected as the pitch 
    from that previous chord that is **closest** (smallest absolute distance) 
    to the lowest pitch of the current event.

    Args:
        midi_filepath: The path to the input MIDI file (or a music21 Stream for testing).

    Returns:
        A list of pitch intervals (deltas) represented as integers or lists of integers.
    """

    try:
        # 1. Parse the MIDI file into a music21 Score object
        # Handles both string filepath and direct stream objects (for testing)
        score = m21.converter.parse(midi_filepath)

    except m21.converter.ConverterException as e:
        print(f"Error parsing MIDI file '{midi_filepath}' and skipping: {e}")
        return []

    # Initialize intermediate storage to hold pitches and offset for sorting
    all_note_data: List[Dict[str, Any]] = []

    # 2. Iterate through each Part (or track) in the score
    for part in score.parts:

        # 3. Iterate over all Notes and Chords within this part, flattened by time
        for element in part.flat.notes:

            # Data structure to hold offset (for sorting) and all pitches
            data: Dict[str, Any] = {'offset': element.offset}

            if isinstance(element, m21.note.Note):
                # Data for a single Note: stored as a list for uniformity
                data['pitches'] = [element.pitch.midi]

            elif isinstance(element, m21.chord.Chord):
                # Data for a Chord: a list of MIDI pitches
                data['pitches'] = [p.midi for p in element.pitches]

            all_note_data.append(data)

    # 4. Sort the temporary vector by offset to ensure correct sequence
    all_note_data.sort(key=lambda x: x['offset'])

    # 5. Process the sorted data to calculate relative intervals
    final_vector: List[Union[int, List[int]]] = []

    # Start with a reference pitch: Middle C (MIDI 60). This sets the first interval.
    last_pitches: List[int] = [60]

    for item in all_note_data:
        current_pitches = item['pitches']

        # --- CRITICAL LOGIC: Determine the single reference pitch from the previous event ---
        reference_pitch: int

        if not last_pitches:
            # Should only happen if the first event was skipped/empty, but safe guard here
            reference_pitch = 60
        elif len(last_pitches) == 1:
            # Case 1: The previous event was a single note. Use it as the reference.
            reference_pitch = last_pitches[0]
        else:
            # Case 2: The previous event was a chord (multiple pitches).
            # We must find the pitch from the previous chord that is closest to
            # the current event's lowest pitch (our melodic anchor).

            min_current_pitch = min(current_pitches)

            min_delta_abs = float('inf')
            closest_prev_pitch = last_pitches[0]

            for prev_p in last_pitches:
                # Calculate the absolute difference (delta)
                delta_abs = abs(prev_p - min_current_pitch)

                # Check for the smallest delta (closest pitch)
                if delta_abs < min_delta_abs:
                    min_delta_abs = delta_abs
                    closest_prev_pitch = prev_p

            reference_pitch = closest_prev_pitch
        # --- End Reference Pitch Determination ---

        # Calculate intervals (current pitch - reference pitch)
        intervals = [p - reference_pitch for p in current_pitches]

        # Update state for the next iteration
        last_pitches = current_pitches

        # Append result: single int for single note, list for chord
        if len(intervals) == 1:
            final_vector.append(intervals[0])
        else:
            final_vector.append(intervals)

    return final_vector

# --- Folder Processing Function ---


def process_folder_to_json(root_dir: str, output_filepath: str):
    """
    Traverses a root directory, processes all MIDI files found, and saves the 
    pitch interval vectors to a single JSON file.

    Args:
        root_dir: The starting directory to search for MIDI files.
        output_filepath: The path to save the final JSON file.
    """

    print(f"Starting directory scan in: {root_dir}")
    all_processed_songs = []

    # Traverse the directory tree
    for dirpath, dirnames, filenames in os.walk(root_dir):
        for filename in filenames:
            # 1. Check if the file is a MIDI file
            if filename.lower().endswith(('.mid', '.midi')):
                filepath = os.path.join(dirpath, filename)
                print(f"Processing: {filepath}")

                # 2. Run the processing function
                note_vector = midi_to_note_vector(filepath)

                # 3. Add to the list if the vector is not empty
                if note_vector:
                    song_data = {
                        "filepath": filepath,
                        "vector": note_vector
                    }
                    all_processed_songs.append(song_data)

    # 4. Save the compiled list to a single JSON file
    if all_processed_songs:
        try:
            with open(output_filepath, 'w') as f:
                json.dump(all_processed_songs, f, indent=4)
            print(
                f"\n✅ Successfully processed {len(all_processed_songs)} song(s).")
            print(f"Data saved to: {output_filepath}")
        except Exception as e:
            print(f"\n❌ Error saving JSON file '{output_filepath}': {e}")
    else:
        print("\n⚠️ No MIDI files were successfully processed.")

# --- Example Usage ---


def note_vector_to_midi_pitches(interval_vector: List[Union[int, List[int]]]) -> List[Union[int, List[int]]]:
    """
    Reverses the process, converting a sequential vector of pitch intervals (deltas) 
    back into a sequence of absolute MIDI pitches.

    The first pitch is randomly selected from Octave 4 (MIDI 60 to 71).

    Args:
        interval_vector: A list of pitch intervals (integers or lists of integers).

    Returns:
        A list of absolute MIDI pitches (integers or lists of integers).
    """

    if not interval_vector:
        return []

    # Randomly select the starting absolute pitch from Octave 4 (C4 to B4)
    # MIDI 60 (C4) to 71 (B4)
    start_pitch = random.randint(60, 71)

    absolute_pitches: List[Union[int, List[int]]] = []

    # 1. Handle the very first element using the random start pitch.
    first_element = interval_vector[0]

    def process_element(element, reference_pitch):
        if isinstance(element, int):
            # Single note: New pitch = reference + interval
            new_pitch = reference_pitch + element
            return [new_pitch], new_pitch
        else:
            # Chord: New pitches = reference + each interval
            new_pitches = [reference_pitch + interval for interval in element]
            # Use the lowest pitch of the new chord as the anchor for the NEXT delta calculation
            new_anchor = min(new_pitches)
            return new_pitches, new_anchor

    # Process the first element
    new_pitches_list, last_pitch = process_element(first_element, start_pitch)

    if len(new_pitches_list) == 1:
        absolute_pitches.append(new_pitches_list[0])
    else:
        absolute_pitches.append(new_pitches_list)

    # 2. Iterate through the rest of the elements
    for element in interval_vector[1:]:
        # Calculate the new absolute pitches relative to the last_pitch (anchor)
        new_pitches_list, new_anchor = process_element(element, last_pitch)

        # Update the anchor pitch for the next iteration
        last_pitch = new_anchor

        # Append the result to the final list
        if len(new_pitches_list) == 1:
            absolute_pitches.append(new_pitches_list[0])
        else:
            absolute_pitches.append(new_pitches_list)

    return absolute_pitches


def play_midi_pitches(absolute_pitches: List[Union[int, List[int]]], duration: float = 0.5):
    """
    Creates a music21 Stream from a sequence of absolute MIDI pitches and plays it.

    NOTE: Rhythmic information (duration, offset) is not preserved or reconstructed 
    from the interval vector, so a default duration is used.

    Args:
        absolute_pitches: A list of absolute MIDI pitches (integers or lists).
        duration: The quarter length to use for each note/chord (default is an eighth note).
    """
    score = m21.stream.Score()
    part = m21.stream.Part()

    for element in absolute_pitches:
        if isinstance(element, int):
            # Single note
            n = m21.note.Note(element)
            n.quarterLength = duration
            part.append(n)
        elif isinstance(element, list):
            # Chord
            c = m21.chord.Chord(element)
            c.quarterLength = duration
            part.append(c)

    score.insert(0, part)

    print("Attempting to play generated MIDI sequence...")
    # This command uses music21's default playback mechanism, which typically
    # opens the generated MIDI file in a system media player (like SimpleSynth on Mac or VLC/Media Player on Windows).
    score.show('midi')


if __name__ == '__main__':

    # --- Example of how to run the folder processing script ---

    # Define the directory where your MIDI files are located (this will be recursively searched)
    ROOT_DIRECTORY = "maestro-v3.0.0"

    # Define the output JSON file path
    OUTPUT_FILE = 'delta_notes.json'

    print("--- Starting MIDI Dataset Processing ---")
    print(f"Set up to read files from: {ROOT_DIRECTORY}")
    print(f"Set up to write results to: {OUTPUT_FILE}")
    print("---------------------------------------")

    # Call the main processing function
    # Note: Ensure you have MIDI files in the ROOT_DIRECTORY path before running.
    process_folder_to_json(ROOT_DIRECTORY, OUTPUT_FILE)
