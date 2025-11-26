from pathlib import Path
import json
from Utils import load_midi, calculate_box_plot_stats
import random
import Node
from maestro_to_vector import play_midi_pitches, note_vector_to_midi_pitches
import sys
import Visualize


def build_tree(data, Tree, max_steps=1, max_depth=None):
    # Data: list of symbols
    cur_branch = Tree
    steps = 0
    depth = 0
    for symbol in data:
        if not symbol:
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
    for _ in range(sentence_length):
        if cur_context.is_leaf():
            leaf_restarts += 1
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
    return sentence, leaf_restarts


if __name__ == "__main__":

    try:
        sys.setrecursionlimit(10000)
    except Exception as e:
        print(f"Warning: Could not set recursion limit. {e}")

    # Build Parameters
    number_of_songs_per_tree = 200
    max_depth = None
    steps = 1
    # Generate Parameters
    sentence_length = 100
    number_of_sentences = 1
    graph_data = []
    # for number_of_songs_per_tree in [2, 4, 8, 16, 32, 64, 128, 256, 512, 1200]:
    print(f"\n\nBuilding with {number_of_songs_per_tree} songs per tree:")
    midi_notes_per_song = load_midi()
    Trees = []

    tot_songs = len(midi_notes_per_song)

    for i in range(tot_songs//number_of_songs_per_tree):
        Tree = Node.Node(0, None)
        for notes in midi_notes_per_song[i*number_of_songs_per_tree:min((i+1)*number_of_songs_per_tree, tot_songs)]:
            build_tree(notes, Tree, max_steps=steps,
                       max_depth=max_depth)
        Trees.append(Tree)
    song_restarts = []
    sentences = []

    for i in range(number_of_sentences):
        sentence, restarts = create_sentence(Trees, sentence_length)
        song_restarts.append(restarts)
        sentences.append(sentence)

    absolute_pitches = note_vector_to_midi_pitches(sentences[0])
    play_midi_pitches(absolute_pitches, duration=0.5)

    # if True:
    #         # metrics = []
    #         # for tree in Trees:
    #         #     metric = tree.analyze_tree_metrics()
    #         #     metric["Total freq"] = sum(child.freq for child in tree.children)
    #         #     metrics.append(metric)

    #         # box_metrics = {}
    #         # for metric in metrics[0].keys():
    #         #     box_metrics[metric] = calculate_box_plot_stats(
    #         #         [m[metric] for m in metrics])
    #         # box_metrics["Leaf Restarts"] = calculate_box_plot_stats(song_restarts)

    #         general_metrics = {
    #             "Number of Trees": len(Trees),
    #             "Songs per Tree": number_of_songs_per_tree,
    #             "Total Songs": tot_songs,
    #             "Restart per Symbol": sum(song_restarts) / (number_of_sentences * sentence_length)

    #         }
    #         graph_data.append((
    #             number_of_songs_per_tree,
    #             general_metrics["Restart per Symbol"]
    #         ))
    #         # print("General Metrics:")
    #         # print(general_metrics)
    #         # print("Box Plot Stats:")
    #         # print(box_metrics)
    #         # if False:
    #         #     create_box_plot_from_stats(
    #         #         box_metrics)
    #     # Average Tree Depth Vs Number of leaf restarts
    #     # changing build depth when reaching leaf.
    # print("graph Data: ", graph_data)
    # Visualize.generate_graph_from_pairs(
    #     graph_data, "steps_vs_reset_symbol_2_songs.png")
