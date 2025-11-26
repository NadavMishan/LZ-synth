from typing import List, Tuple
import os
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


def create_box_plot_from_stats(stats_dict: Dict[str, Dict[str, float]]):
    """
    Generates and displays a box plot (box graph) from a dictionary containing
    pre-calculated quartile and min/max statistics.

    The input dictionary must follow this structure:
    {
        'metric_name_1': {'min': X, 'Q1': Y, 'median': Z, 'Q3': A, 'max': B},
        ...
    }

    Args:
        stats_dict: A dictionary of metric names mapped to their summary statistics.
    """
    print("Preparing data for box plot...")

    # 1. Convert the input dictionary into a list of statistical dictionaries
    #    that matplotlib's boxplot function can understand.
    boxplot_data = []
    labels = []

    for metric_name, stats in stats_dict.items():
        # Ensure the required keys are present, although type checking should
        # cover this if using a static type checker.
        if all(key in stats for key in ['min', 'Q1', 'median', 'Q3', 'max']):

            # The structure for pre-calculated stats needs to match what
            # matplotlib.cbook.boxplot_stats expects.
            box_stats = {
                # 'label' is used for the tick label on the axis
                'label': metric_name,
                # Quartiles
                'q1': stats['Q1'],
                'med': stats['median'],
                'q3': stats['Q3'],
                # Whiskers (set to min/max since no explicit outlier list is provided)
                'whislo': stats['min'],
                'whishi': stats['max'],
                # If there were explicit outliers, they would go here as a list:
                'fliers': [],
            }
            boxplot_data.append(box_stats)
            labels.append(metric_name)
        else:
            print(
                f"Skipping metric '{metric_name}': missing required min/Q1/median/Q3/max keys.")

    if not boxplot_data:
        print("No valid data found to generate the plot.")
        return

    # 2. Create the plot
    plt.style.use('seaborn-v0_8-whitegrid')  # Set a clean style
    fig, ax = plt.subplots(figsize=(12, 6))

    # We use the list of dicts directly with the stats=True flag
    ax.bxp(boxplot_data, showfliers=False, vert=False, patch_artist=True,
           boxprops=dict(facecolor='lightblue', linewidth=1.5),
           medianprops=dict(color='darkred', linewidth=2.5),
           whiskerprops=dict(linestyle='--', linewidth=1.0, color='gray'),
           capprops=dict(color='gray', linewidth=1.0)
           )

    # 3. Add titles and labels for clarity
    ax.set_title('Box Plot Visualization of Summary Statistics',
                 fontsize=16, pad=15)
    ax.set_xlabel('Value Range (Units vary by metric)', fontsize=12)
    ax.set_ylabel('Metrics', fontsize=12)

    # 4. Improve layout and display
    plt.tight_layout()
    plt.show()


def generate_graph_from_pairs(data_pairs: List[Tuple[float, float]], filename: str = 'points_graph.png', title="Scatter Plot of (x, y) Pairs", x_title="", y_title="") -> None:
    """
    Generates a scatter plot from a list of (x, y) data pairs and saves it to a file.

    Args:
        data_pairs: A list of tuples, where each tuple is an (x, y) coordinate.
        filename: The name of the file to save the graph image to.
    """
    if not data_pairs:
        print("Error: The list of data pairs is empty.")
        return

    # Separate the x and y values from the list of tuples
    try:
        x_values = [pair[0] for pair in data_pairs]
        y_values = [pair[1] for pair in data_pairs]
    except (TypeError, IndexError):
        print("Error: The input list must contain tuples of two numbers (x, y).")
        return

    # Create the plot
    plt.figure(figsize=(10, 6))  # Set the figure size
    plt.scatter(x_values, y_values, color='skyblue', marker='o',
                s=100, edgecolors='darkblue', alpha=0.8)

    # Add labels and title
    plt.title(title, fontsize=16, fontweight='bold')
    plt.xlabel(xlabel=x_title, fontsize=12)
    plt.ylabel(ylabel=y_title, fontsize=12)

    # Add a grid for better readability
    plt.grid(True, linestyle='--', alpha=0.6)

    # Add annotations for each point (optional, but helpful)
    for i, (x, y) in enumerate(data_pairs):
        plt.annotate(f'({x}, {y})', (x, y), textcoords="offset points", xytext=(
            0, 10), ha='center', fontsize=9)

    # Save the figure
    try:
        plt.savefig(filename, bbox_inches='tight')
        print(
            f"\nSuccessfully generated graph and saved to: {os.path.abspath(filename)}")
    except Exception as e:
        print(f"\nAn error occurred while saving the file: {e}")

    # Display the plot (comment this out if running in an environment without a display server)
    # plt.show()


if __name__ == '__main__':

    sample_data = [
        (1, 0.999),
        (2, 0.526),
        (3, 0.386),
        (4, 0.349),
        (5, 0.344),
        (6, 0.339),
        (7, 0.336),
        (8, 0.331),
        (9, 0.322),
        (10, 0.337),
        (11, 0.344),
        (12, 0.341),
        (13, 0.318),
        (14, 0.338),
        (15, 0.309),
        (16, 0.309),
        (17, 0.34),
        (18, 0.308),
        (19, 0.333)
    ]

    print("Starting graph generation...")
    generate_graph_from_pairs(sample_data, '2.png', title="Root/Symbol as a Function of Maximum Tree Depth",
                              x_title="Maximum Tree Depth", y_title="Root/Symbol")

    # Example of running the function with different data
    # more_data = [(10, 100), (20, 80), (30, 60), (40, 40)]
    # generate_graph_from_pairs(more_data, 'linear_data_graph.png')
