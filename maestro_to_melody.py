from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import json
import os
import random
import tempfile

import music21 as m21
import pandas as pd

try:
    from midi2audio import FluidSynth
except ImportError:
    FluidSynth = None


def is_wav_renderer_available() -> bool:
    if FluidSynth is None:
        return False

    try:
        FluidSynth()
    except Exception:
        return False

    return True


def build_metadata_index(csv_path):
    df = pd.read_csv(csv_path)

    return {
        row["midi_filename"]: (
            row["canonical_composer"],
            row["canonical_title"],
        )
        for _, row in df.iterrows()
    }


def midi_to_highest_pitch_intervals(midi_filepath: str) -> List[int]:
    """
    Reads a MIDI file and returns a sequential vector of pitch intervals.
    If multiple notes (chords) occur at the same time, it selects only
    the highest pitch to calculate the interval.
    """

    try:
        score = m21.converter.parse(midi_filepath)
    except m21.converter.ConverterException as e:
        print(f"Error parsing MIDI file '{midi_filepath}': {e}")
        return []

    all_note_data: List[Dict[str, Any]] = []

    for element in score.flat.notes:
        data: Dict[str, Any] = {"offset": element.offset}

        if isinstance(element, m21.note.Note):
            data["pitch"] = element.pitch.midi
        elif isinstance(element, m21.chord.Chord):
            data["pitch"] = max(p.midi for p in element.pitches)

        all_note_data.append(data)

    all_note_data.sort(key=lambda x: x["offset"])

    final_vector: List[int] = []
    last_pitch = 0

    for item in all_note_data:
        next_pitch = item["pitch"]
        interval = next_pitch - last_pitch
        final_vector.append(interval)
        last_pitch = next_pitch

    if final_vector:
        final_vector.pop(0)

    return final_vector


def absolute_to_relative_pitches(
    midi_filepath: str, bass_threshold: int = 50
) -> List[int]:
    """
    Returns a vector of pitch intervals with the following filters:
    1. Chords are reduced to the highest pitch.
    2. Notes below the bass threshold are removed.
    3. Intervals greater than 18 semitones are ignored (skipped).
    """
    try:
        score = m21.converter.parse(midi_filepath)
    except Exception as e:
        print(f"Error parsing MIDI file: {e}")
        return []

    pitches = []
    for element in score.flat.notes:
        if isinstance(element, m21.note.Note):
            pitch = element.pitch.midi
        elif isinstance(element, m21.chord.Chord):
            pitch = max(n.midi for n in element.pitches)
        else:
            continue

        if pitch >= bass_threshold:
            pitches.append(pitch)

    if not pitches:
        return []

    final_intervals: List[int] = []
    last_valid_pitch = pitches[0]

    for current_pitch in pitches[1:]:
        interval = current_pitch - last_valid_pitch
        if abs(interval) <= 18:
            final_intervals.append(interval)
            last_valid_pitch = current_pitch

    return final_intervals


def midi_to_absolute_pitch_tokens(
    midi_filepath: str,
) -> List[Union[int, List[int]]]:
    """
    Reads a MIDI file and returns an ordered sequence of absolute pitch tokens.
    Timing is removed from the output representation, but note order is preserved.
    Simultaneous notes are grouped into a single sorted chord token.
    """
    try:
        score = m21.converter.parse(midi_filepath)
    except Exception as e:
        print(f"Error parsing MIDI file '{midi_filepath}': {e}")
        return []

    events_by_offset: Dict[float, List[int]] = {}
    ordered_offsets: List[float] = []

    flattened_score = score.flatten() if hasattr(score, "flatten") else score.flat

    for element in flattened_score.notes:
        pitches: List[int]
        if isinstance(element, m21.note.Note):
            pitches = [element.pitch.midi]
        elif isinstance(element, m21.chord.Chord):
            pitches = [pitch.midi for pitch in element.pitches]
        else:
            continue

        offset = float(element.offset)
        if offset not in events_by_offset:
            events_by_offset[offset] = []
            ordered_offsets.append(offset)
        events_by_offset[offset].extend(pitches)

    tokens: List[Union[int, List[int]]] = []
    for offset in sorted(ordered_offsets):
        unique_pitches = sorted(set(int(pitch) for pitch in events_by_offset[offset]))
        if not unique_pitches:
            continue
        tokens.append(unique_pitches[0] if len(unique_pitches) == 1 else unique_pitches)

    return tokens


def get_midi_tempo_bpm(midi_filepath: str, default_bpm: float = 120.0) -> float:
    """
    Returns the first tempo marking found in the MIDI file, or default_bpm when
    no explicit tempo is available.
    """
    try:
        score = m21.converter.parse(midi_filepath)
    except Exception as e:
        print(f"Error parsing MIDI file '{midi_filepath}' for tempo: {e}")
        return float(default_bpm)

    tempo_marks = list(score.recurse().getElementsByClass(m21.tempo.MetronomeMark))
    for mark in tempo_marks:
        if mark.number is not None:
            return float(mark.number)

    return float(default_bpm)


def process_folder_to_json(root_dir: str, output_filepath: str, csv_path: str):
    print(f"Starting directory scan in: {root_dir}")

    metadata_index = build_metadata_index(csv_path)
    all_processed_songs = []

    for dirpath, _, filenames in os.walk(root_dir):
        for filename in filenames:
            if filename.lower().endswith((".mid", ".midi")):
                filepath = os.path.join(dirpath, filename)
                csv_key = os.path.relpath(filepath, root_dir).replace("\\", "/")
                print(f"Processing: {filepath}")

                note_vector = absolute_to_relative_pitches(filepath)
                if note_vector:
                    composer, composition = metadata_index.get(
                        csv_key, ("Unknown", "Unknown")
                    )

                    song_data = {
                        "filepath": filepath,
                        "composer": composer,
                        "composition": composition,
                        "vector": note_vector,
                    }

                    all_processed_songs.append(song_data)

    if all_processed_songs:
        with open(output_filepath, "w", encoding="utf-8") as f:
            json.dump(all_processed_songs, f, indent=4)

        print(f"\nProcessed {len(all_processed_songs)} songs.")
        print(f"Saved to: {output_filepath}")
    else:
        print("\nNo MIDI files processed.")


def relative_to_absolute_pitches(
    interval_vector: List[Union[int, List[int]]]
) -> List[Union[int, List[int]]]:
    """
    Converts a sequential vector of pitch intervals back into absolute MIDI pitches.
    """

    if not interval_vector:
        return []

    start_pitch = random.randint(60, 71)
    absolute_pitches: List[Union[int, List[int]]] = []

    def process_element(element, reference_pitch):
        if isinstance(element, int):
            new_pitch = reference_pitch + element
            return [new_pitch], new_pitch

        new_pitches = [reference_pitch + interval for interval in element]
        new_anchor = min(new_pitches)
        return new_pitches, new_anchor

    new_pitches_list, last_pitch = process_element(interval_vector[0], start_pitch)
    absolute_pitches.append(
        new_pitches_list[0] if len(new_pitches_list) == 1 else new_pitches_list
    )

    for element in interval_vector[1:]:
        new_pitches_list, new_anchor = process_element(element, last_pitch)
        last_pitch = new_anchor
        absolute_pitches.append(
            new_pitches_list[0] if len(new_pitches_list) == 1 else new_pitches_list
        )

    return absolute_pitches


def create_score_from_pitches(
    absolute_pitches: List[Union[int, List[int]]],
    duration: float = 0.5,
    sustain_factor: float = 3.0,
    humanize: bool = True,
    tempo_bpm: float = 120.0,
) -> m21.stream.Score:
    score = m21.stream.Score()
    part = m21.stream.Part()
    score.insert(0, m21.tempo.MetronomeMark(number=float(tempo_bpm)))

    current_time = 0.0
    base_velocity = 80
    variation = 15

    for element in absolute_pitches:
        if isinstance(element, int):
            obj = m21.note.Note(element)
        elif isinstance(element, list):
            obj = m21.chord.Chord(element)
        else:
            continue

        obj.quarterLength = duration * sustain_factor

        if humanize:
            random_vel = random.randint(base_velocity - variation, base_velocity + variation)
            obj.volume.velocity = max(0, min(127, random_vel))

        part.insert(current_time, obj)
        current_time += duration

    score.insert(0, part)
    return score


def export_midi_file(
    absolute_pitches: List[Union[int, List[int]]],
    output_path: Union[str, Path],
    duration: float = 0.5,
    sustain_factor: float = 3.0,
    humanize: bool = True,
    tempo_bpm: float = 120.0,
) -> str:
    if not absolute_pitches:
        raise ValueError("No pitches were provided for MIDI export.")

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    score = create_score_from_pitches(
        absolute_pitches,
        duration=duration,
        sustain_factor=sustain_factor,
        humanize=humanize,
        tempo_bpm=tempo_bpm,
    )
    score.write("midi", fp=str(output_path))
    return str(output_path.resolve())


def export_midi_to_temp(
    absolute_pitches: List[Union[int, List[int]]],
    duration: float = 0.5,
    sustain_factor: float = 3.0,
    humanize: bool = True,
    tempo_bpm: float = 120.0,
) -> str:
    temp_dir = Path(tempfile.gettempdir()) / "lz_synth"
    temp_dir.mkdir(parents=True, exist_ok=True)
    output_path = temp_dir / "latest_generation.mid"
    return export_midi_file(
        absolute_pitches,
        output_path,
        duration=duration,
        sustain_factor=sustain_factor,
        humanize=humanize,
        tempo_bpm=tempo_bpm,
    )


def render_midi_to_wav(
    midi_path: Union[str, Path],
    wav_path: Union[str, Path],
    sound_font: Optional[Union[str, Path]] = None,
) -> str:
    if FluidSynth is None:
        raise RuntimeError(
            "WAV export requires the optional 'midi2audio' package and a FluidSynth installation."
        )

    midi_path = Path(midi_path)
    wav_path = Path(wav_path)
    wav_path.parent.mkdir(parents=True, exist_ok=True)

    kwargs: Dict[str, Any] = {}
    if sound_font:
        kwargs["sound_font"] = str(sound_font)

    try:
        synth = FluidSynth(**kwargs)
        synth.midi_to_audio(str(midi_path), str(wav_path))
    except Exception as exc:
        raise RuntimeError(
            "Failed to render WAV. Ensure FluidSynth is installed and accessible."
        ) from exc

    return str(wav_path.resolve())


def export_wav_from_pitches(
    absolute_pitches: List[Union[int, List[int]]],
    wav_path: Union[str, Path],
    duration: float = 0.5,
    sustain_factor: float = 3.0,
    humanize: bool = True,
    sound_font: Optional[Union[str, Path]] = None,
    tempo_bpm: float = 120.0,
) -> str:
    midi_path = export_midi_to_temp(
        absolute_pitches,
        duration=duration,
        sustain_factor=sustain_factor,
        humanize=humanize,
        tempo_bpm=tempo_bpm,
    )
    return render_midi_to_wav(midi_path, wav_path, sound_font=sound_font)


def play_midi_pitches_humanized(
    absolute_pitches: List[Union[int, List[int]]],
    duration: float = 0.5,
    tempo_bpm: float = 120.0,
    sustain_factor: float = 3.0,
):
    midi_path = export_midi_to_temp(
        absolute_pitches,
        duration=duration,
        sustain_factor=sustain_factor,
        tempo_bpm=tempo_bpm,
    )
    score = m21.converter.parse(midi_path)
    print("Playing generated MIDI...")
    score.show("midi")


def play_midi_file(midi_path: Union[str, Path]):
    midi_path = Path(midi_path)
    score = m21.converter.parse(str(midi_path))
    print("Playing generated MIDI...")
    score.show("midi")


if __name__ == "__main__":
    root_directory = "maestro-v3.0.0"
    output_json = "delta_notes_melody.json"
    metadata_csv = "maestro-v3.0.0\\maestro-v3.0.0.csv"

    process_folder_to_json(root_directory, output_json, metadata_csv)
