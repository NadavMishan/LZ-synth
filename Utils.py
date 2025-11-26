import matplotlib.pyplot as plt
from typing import Dict, Any
import matplotlib.cbook as cbook
import json
from pathlib import Path
import re
from collections import defaultdict
from music21 import harmony, roman, key
# Using standard library for stats
from statistics import quantiles, median, stdev


def chords_to_roman(chord_list, song_key):
    """
    Convert chord symbols to Roman numerals in the given key.
    """
    if song_key:
        if ":" in song_key:
            song_key = song_key.split(":")[0].strip()
    k = key.Key(song_key)
    roman_list = []

    for ch in chord_list:
        if not ch or ch == "N":
            roman_list.append("N")
            continue

        try:
            cs = harmony.ChordSymbol(ch)
            rn = roman.romanNumeralFromChord(cs, k)
            roman_list.append(str(rn.figure))
        except Exception:
            roman_list.append("N")

    return roman_list


# Mapping regex patterns for canonical names
mapping = {
    'verse': r'\bverse\b|\bverse[_(/\']',
    'intro': r'\bintro\b|intro[_(/\']',
    'outro': r'\boutro\b|outro[_(/\']',
    'refrain': r'\brefrain\b|refrain[_(/\']',
    'bridge': r'\bbridge\b|bridge[_(/\']',
    'solo': r'solo',
    'silence': r'\bsilence\b'
}


def normalize_label(label):
    label_lower = label.lower()
    for base in mapping.keys():
        if base in label_lower:
            return base
    return label_lower  # keep as is if no match


# if __name__ == "__main__":
#     folder = Path("BeatlesMerged")
#     symbols = []
#     for file_path in folder.glob("*.json"):
#         with open(file_path, "r", encoding="utf-8") as f:
#             data = json.load(f)

#         # Segment compression
#         segment_data = [normalize_label(i["label"]) for i in data]
#         segment_data.append("EOF")

#         # Chord compression per segment

#         for section in data:
#             norm_label = normalize_label(section["label"])

#             try:
#                 chord_data = chords_to_roman(
#                     section["chords"]["original"], section["key"])
#             except Exception as e:
#                 print(f"Error processing file {file_path.name}: {e}")
#                 chord_data = ["N"]
#                 print(section["chords"]["original"])
#                 break
#             chord_data.append("EOF")
#             # print("Chords to compress", chord_data)
#             for chord in chord_data:
#                 if chord not in symbols:
#                     symbols.append(chord)

#     print(f"symbols: {symbols}")
    # chords_compress_dict[norm_label], chord_code = lzw_compress(
    #     chord_data, chords_compress_dict[norm_label])
    # chords_decompress_dict[norm_label], chord_decode = lzw_decompress(
    #     chord_code, chords_decompress_dict[norm_label])


def get_songs(file_path="BeatlesMerged", output_path="all_songs_chords.json"):
    """
    Reads all .json song files in the given folder, extracts all Roman chords
    (ignoring sections), and saves the resulting list to a JSON file.

    Returns:
        chords_per_song (list): A list where each element is a list of Roman chords for one song.
    """
    folder = Path(file_path)
    chords_per_song = []

    for p in folder.glob("*.json"):
        with open(p, "r", encoding="utf-8") as f:
            data = json.load(f)

        song_chords = []

        for section in data:
            # Convert section's original chords to Roman numerals
            chord_data = chords_to_roman(
                section["chords"]["original"], section["key"])
            song_chords.extend(chord_data)

        chords_per_song.append(song_chords)

    # Save the full list of chord sequences to JSON
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(chords_per_song, f, indent=2, ensure_ascii=False)

    print(f"✅ Saved {len(chords_per_song)} songs to {output_path}")
    return chords_per_song


def load_songs(json_path="all_songs_chords.json"):
    """
    Loads the saved chords-per-song list from a JSON file.

    Returns:
        list: A list of lists (each inner list is a song’s Roman chord sequence).
    """
    with open(json_path, "r", encoding="utf-8") as f:
        chords_per_song = json.load(f)
    return chords_per_song


def load_midi(file_path="delta_notes.json"):
    with open(file_path, "r", encoding="utf-8") as f:
        midi_songs = json.load(f)
    midi_songs = [song["vector"] for song in midi_songs]
    return midi_songs


def calculate_box_plot_stats(values):
    """
    Calculates the 5 essential box plot statistics: Min, Q1, Median, Q3, Max.
    """
    if not values:
        return {'min': 0, 'Q1': 0, 'median': 0, 'Q3': 0, 'max': 0}

    # Sort the values for accurate quantile calculation
    sorted_values = sorted(values)

    minimum = sorted_values[0]
    maximum = sorted_values[-1]

    # Calculate Q1, Median (Q2), Q3 using the exclusive method for a list of size < 100
    try:
        # Pct = [25, 50, 75]
        quartiles = quantiles(sorted_values, n=4, method='exclusive')
        Q1 = quartiles[0]
        Q2 = quartiles[1]  # Median
        Q3 = quartiles[2]
    except:
        # Fallback if list is too small for 'exclusive' or other error
        Q1 = sorted_values[len(sorted_values) // 4]
        Q2 = median(sorted_values)
        Q3 = sorted_values[len(sorted_values) * 3 // 4]

    return {
        'min': minimum,
        'Q1': Q1,
        'median': Q2,
        'Q3': Q3,
        'max': maximum
    }


if __name__ == "__main__":
    print(load_midi())
