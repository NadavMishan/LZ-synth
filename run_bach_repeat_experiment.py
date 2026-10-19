import argparse
import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt

from LZ_Main import build_trees_from_vectors, generate_from_existing_trees
from Utils import load_bach_melody
from Visualize import build_branch_histogram_figure
from maestro_to_melody import export_midi_file


DEFAULT_REPEATS = [5, 10, 15]
DEFAULT_OUTPUT_DIR = Path("BachRepeatExperiments")
DEFAULT_SENTENCE_LENGTH = 100
OUTPUT_TEMPO_BPM = 120.0
SUSTAIN_FACTOR = 5


def serialize_tree(node):
    return {
        "symbol": node.symbol,
        "freq": node.freq,
        "is_leaf": node.is_leaf(),
        "child_count": len(node.children),
        "children": [serialize_tree(child) for child in node.children],
    }


def average(values):
    return sum(values) / len(values) if values else 0.0


def save_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=2, ensure_ascii=False)


def save_branch_histogram(trees, path, repeat):
    fig = build_branch_histogram_figure(
        trees,
        title=f"Bach Branch Length Histogram (repeat={repeat})",
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=300, bbox_inches="tight")
    plt.close(fig)


def run_repeat_experiment(midi_data, repeat, sentence_length, output_dir):
    repeat_dir = output_dir / f"repeat_{repeat:03d}"
    repeat_dir.mkdir(parents=True, exist_ok=True)

    trees = build_trees_from_vectors(
        midi_data,
        number_of_songs_per_tree=1,
        song_repeat=repeat,
        steps=1,
        max_depth=None,
        concatenate_songs=False,
    )
    if not trees:
        raise ValueError(f"Tree construction returned no trees for repeat={repeat}.")

    generation = generate_from_existing_trees(trees, sentence_length=sentence_length)
    generated_tokens = generation["sentence"]
    if not generated_tokens:
        raise ValueError(f"Generation returned an empty sequence for repeat={repeat}.")

    tree = trees[0]
    branch_lengths = tree.get_branch_lengths()
    metrics = tree.analyze_tree_metrics()

    midi_path = repeat_dir / "generated.mid"
    histogram_path = repeat_dir / "branch_length_histogram.png"
    tree_path = repeat_dir / "tree.json"
    summary_path = repeat_dir / "summary.json"

    export_midi_file(
        generated_tokens,
        midi_path,
        tempo_bpm=OUTPUT_TEMPO_BPM,
        sustain_factor=SUSTAIN_FACTOR,
    )
    save_branch_histogram(trees, histogram_path, repeat)
    save_json(tree_path, serialize_tree(tree))

    summary = {
        "repeat": repeat,
        "sentence_length": sentence_length,
        "generated_token_count": len(generated_tokens),
        "restarts": generation["restarts"],
        "sequence_lengths": generation["sequence_lengths"],
        "branch_lengths": branch_lengths,
        "average_branch_length": average(branch_lengths),
        "tree_metrics": metrics,
        "output_paths": {
            "generated_midi": str(midi_path.resolve()),
            "branch_length_histogram": str(histogram_path.resolve()),
            "tree_json": str(tree_path.resolve()),
            "summary_json": str(summary_path.resolve()),
        },
    }
    save_json(summary_path, summary)
    return summary


def parse_args():
    parser = argparse.ArgumentParser(
        description="Run the Bach repeat experiment and save generated MIDI, histograms, and trees."
    )
    parser.add_argument(
        "--repeats",
        type=int,
        nargs="+",
        default=DEFAULT_REPEATS,
        help="Repeat values to run. Defaults to 1 20 40.",
    )
    parser.add_argument(
        "--sentence-length",
        type=int,
        default=DEFAULT_SENTENCE_LENGTH,
        help="Number of generated events per repeat.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Directory where experiment artifacts will be saved.",
    )
    args = parser.parse_args()

    if args.sentence_length <= 0:
        parser.error("--sentence-length must be greater than 0.")
    if not args.repeats:
        parser.error("--repeats must include at least one value.")
    invalid_repeats = [repeat for repeat in args.repeats if repeat <= 0]
    if invalid_repeats:
        parser.error(f"--repeats values must be greater than 0: {invalid_repeats}")

    return args


def main():
    sys.setrecursionlimit(max(sys.getrecursionlimit(), 10000))
    args = parse_args()

    midi_data = load_bach_melody()
    if not midi_data or not midi_data[0]:
        raise ValueError("load_bach_melody() returned no Bach melody data.")

    summaries = []
    for repeat in args.repeats:
        print(f"Running Bach repeat experiment for repeat={repeat}...")
        summary = run_repeat_experiment(
            midi_data=midi_data,
            repeat=repeat,
            sentence_length=args.sentence_length,
            output_dir=args.output_dir,
        )
        summaries.append(summary)
        print(
            "Saved repeat={repeat}: avg_branch_length={avg:.2f}, outputs={path}".format(
                repeat=repeat,
                avg=summary["average_branch_length"],
                path=args.output_dir / f"repeat_{repeat:03d}",
            )
        )

    combined_summary_path = args.output_dir / "summary.json"
    save_json(
        combined_summary_path,
        {
            "repeats": args.repeats,
            "sentence_length": args.sentence_length,
            "runs": summaries,
        },
    )
    print(f"Experiment summary saved to: {combined_summary_path.resolve()}")


if __name__ == "__main__":
    main()
