from pathlib import Path
import json
from Utils import load_midi_melody, calculate_box_plot_stats
import random
import Node
from maestro_to_vector import play_midi_pitches, note_vector_to_midi_pitches, play_midi_pitches_humanized
import sys
import Visualize


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
    print("Sentence: \n", sentence)
    return sentence, leaf_restarts, sequence_lengths


def lz_synth_main(number_of_songs_per_tree=200, sentence_length=100, number_of_sentences=1,
                  max_depth=None, steps=1, play_song=False, get_data=False, get_sequence_lengths=False, get_trees=False, song_repeat=1):

    try:
        sys.setrecursionlimit(10000)
    except Exception as e:
        print(f"Warning: Could not set recursion limit. {e}")

    print(f"\n\nBuilding with {number_of_songs_per_tree} songs per tree:")
    midi_notes_per_song = load_midi_melody()
    Trees = []
    Tree = Node.Node(0, None)
    for i in range(song_repeat):
        build_tree(midi_notes_per_song[i], Tree, max_steps=steps,
                   max_depth=max_depth)

    tot_songs = len(midi_notes_per_song)
    Trees.append(Tree)

    sentence, restarts, sequence_lengths = create_sentence(
        Trees, sentence_length)

    if play_song:
        absolute_pitches = note_vector_to_midi_pitches(sentence)
        play_midi_pitches_humanized(absolute_pitches, duration=0.5)

    return Trees


if __name__ == "__main__":
    steps = 1
    Trees = lz_synth_main(number_of_songs_per_tree=1, sentence_length=100,
                          number_of_sentences=1, max_depth=None, steps=steps,
                          play_song=False, get_data=False, get_sequence_lengths=False, song_repeat=1)

    midi_notes_per_song = load_midi_melody()
    Visualize.create_interactive_tree(Trees[0])

    Visualize.plot_tree_graphs(
        Trees, filename=f"Bach_labeled_tree_structure.png", show_labels=True)

    if False:
        Visualize.plot_tree_graphs(
            Trees, filename=f"Bach_Example_Steps={steps}_tree_structure.png", main_title="Tree Structure for Bach Example, Steps={steps}")
        Visualize.plot_and_save_branch_frequency(
            Trees, filename=f"Bach_Example_Steps={steps}_branch_frequency.png", title=f"Branch Frequency for Bach Example, Steps={steps}")

    # print(len(midi_notes_per_song[883]))
    # play_midi_pitches_humanized(note_vector_to_midi_pitches(
    #     midi_notes_per_song[883]), duration=0.5)
