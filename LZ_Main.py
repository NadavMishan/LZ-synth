from pathlib import Path
import json
from Utils import load_midi_melody,load_bach_melody
import random
import Node
from maestro_to_melody import relative_to_absolute_pitches, play_midi_pitches_humanized
import sys
import Visualize
from typing import Any


def build_tree(data, Tree, max_steps=1, max_depth=None):
    # Data: list of symbols
    cur_branch = Tree
    steps = 0
    depth = 0
    for symbol in data:
        if symbol is None:
            # print("Empty symbol encountered, stopping tree build.", i, symbol)
            return
        if symbol in cur_branch.children_symbols:
            cur_branch.freq += 1
            cur_branch = cur_branch.find_child_by_symbol(symbol)
            depth += 1
            if depth == max_depth:
                cur_branch = Tree
                depth = 0
        else:
            cur_branch = cur_branch.create_child(1, symbol)
            steps += 1
            if steps == max_steps:
                cur_branch = Tree
                steps = 0


def create_sentence(Trees, sentence_length=100):
    if not Trees:
        raise ValueError("At least one tree is required to create a sentence.")

    cur_context = random.choice(Trees)
    sentence = []
    leaf_restarts = 0
    sequence_lengths = []
    for i in range(sentence_length):
        if cur_context.is_leaf():
            leaf_restarts += 1
            sequence_lengths.append(
                i-sum(sequence_lengths))
            # Reached a leaf node
            # print("Reached leaf, restarting, current run:\n", sentence)
            cur_context = random.choice(Trees)
        symbols = cur_context.children_symbols
        total_seen = sum([child.freq for child in cur_context.children])
        probabilities = [cur_context.find_child_by_symbol(
            s).freq / total_seen for s in symbols]
        next_symbol = random.choices(symbols, probabilities)[0]
        sentence.append(next_symbol)
        cur_context = cur_context.find_child_by_symbol(next_symbol)
    
    return sentence, leaf_restarts, sequence_lengths


def _coerce_bool(value: Any, field_name: str):
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        if value in (0, 1):
            return bool(value)
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"true", "1", "yes", "y", "on"}:
            return True
        if normalized in {"false", "0", "no", "n", "off"}:
            return False
    raise ValueError(f"{field_name} must be a boolean value.")


def build_trees_from_vectors(
    midi_data,
    number_of_songs_per_tree=200,
    song_repeat=1,
    max_depth=None,
    steps=1,
    concatenate_songs=False,
):
    if not midi_data:
        raise ValueError("No song vectors were provided.")

    try:
        songs_per_tree = int(number_of_songs_per_tree)
        repeats = int(song_repeat)
        step_count = int(steps)
        concatenate = _coerce_bool(concatenate_songs, "concatenate_songs")
    except (TypeError, ValueError) as exc:
        raise ValueError("Tree parameters must be integers and booleans where expected.") from exc

    if songs_per_tree <= 0:
        raise ValueError("number_of_songs_per_tree must be greater than 0.")
    if repeats <= 0:
        raise ValueError("song_repeat must be greater than 0.")
    if step_count <= 0:
        raise ValueError("steps must be greater than 0.")
    if max_depth is not None:
        try:
            max_depth = int(max_depth)
        except (TypeError, ValueError) as exc:
            raise ValueError("max_depth must be an integer or None.") from exc
        if max_depth <= 0:
            raise ValueError("max_depth must be greater than 0 when provided.")

    tot_songs = len(midi_data)
    trees = []
    chunk_size = min(songs_per_tree, tot_songs)

    for i in range(tot_songs // chunk_size):
        tree = Node.Node(0, None)
        start = i * songs_per_tree
        end = min((i + 1) * songs_per_tree, tot_songs)
        chunk = midi_data[start:end]
        for _ in range(repeats):
            if concatenate:
                combined_notes = []
                for notes in chunk:
                    combined_notes.extend(notes)
                build_tree(combined_notes, tree, max_steps=step_count, max_depth=max_depth)
            else:
                for notes in chunk:
                    build_tree(notes, tree, max_steps=step_count, max_depth=max_depth)
        trees.append(tree)

    return trees


def generate_from_existing_trees(trees, sentence_length=100):
    try:
        sentence_length = int(sentence_length)
    except (TypeError, ValueError) as exc:
        raise ValueError("sentence_length must be an integer.") from exc

    if sentence_length <= 0:
        raise ValueError("sentence_length must be greater than 0.")

    sentence, restarts, sequence_lengths = create_sentence(trees, sentence_length)
    return {
        "sentence": sentence,
        "restarts": restarts,
        "sequence_lengths": sequence_lengths,
    }


def lz_synth_main(midi_data, number_of_songs_per_tree=200, sentence_length=100, song_repeat=1,
                  max_depth=None, steps=1, concatenate_songs=False):

    try:
        sys.setrecursionlimit(10000)
    except Exception as e:
        print(f"Warning: Could not set recursion limit. {e}")

    Trees = build_trees_from_vectors(
        midi_data,
        number_of_songs_per_tree=number_of_songs_per_tree,
        song_repeat=song_repeat,
        max_depth=max_depth,
        steps=steps,
        concatenate_songs=concatenate_songs,
    )
    generation = generate_from_existing_trees(Trees, sentence_length)
    sentence = generation["sentence"]

    return Trees, sentence


if __name__ == "__main__":
    midi_data = load_bach_melody()
    # print(midi_data)
    Trees,sentence = lz_synth_main(midi_data, number_of_songs_per_tree=200, sentence_length=100, song_repeat=50,
                  max_depth=None, steps=1)
    
    print("Generated sentence (relative intervals):\n", sentence)
    
    if True:
        absolute_pitches = relative_to_absolute_pitches(sentence)
        play_midi_pitches_humanized(absolute_pitches)

   
