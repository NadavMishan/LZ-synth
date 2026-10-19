import plotly.graph_objects as go
import networkx as nx
from collections import Counter
from typing import List, Tuple
import os
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.patches import Rectangle
from typing import Dict, Any
import matplotlib.cbook as cbook
import json
from pathlib import Path
import re
from collections import defaultdict
from music21 import harmony, roman, key
# Using standard library for stats
from statistics import quantiles, median, stdev


def _collect_branch_lengths(root_nodes):
    all_distances = []
    for root in root_nodes:
        all_distances.extend(root.get_branch_lengths())
    return all_distances


def build_branch_histogram_figure(root_nodes, title="Distribution of Branch Lengths"):
    fig = Figure(figsize=(8, 4.5), tight_layout=True)
    ax = fig.add_subplot(111)

    all_distances = _collect_branch_lengths(root_nodes)
    if not all_distances:
        ax.text(0.5, 0.5, "No branch data available", ha="center", va="center")
        ax.set_axis_off()
        return fig

    counts = Counter(all_distances)
    lengths = sorted(counts.keys())
    frequencies = [counts[length] for length in lengths]

    bars = ax.bar(lengths, frequencies, color="#8ecae6", edgecolor="#023047", alpha=0.85)
    for bar in bars:
        yval = bar.get_height()
        if yval > 0:
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                yval,
                f"{int(yval)}",
                va="bottom",
                ha="center",
                fontsize=8,
            )

    ax.set_title(title, fontsize=13)
    ax.set_xlabel("Branch Length (Edges from Root to Leaf)", fontsize=10)
    ax.set_ylabel("Frequency", fontsize=10)
    ax.set_xticks(lengths)
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    return fig


def build_piano_roll_figure(absolute_pitches, title="Generated Melody Chart"):
    fig = Figure(figsize=(8, 4.5), tight_layout=True)
    ax = fig.add_subplot(111)

    if not absolute_pitches:
        ax.text(0.5, 0.5, "Generate a melody to view the chart", ha="center", va="center")
        ax.set_axis_off()
        return fig

    min_pitch = None
    max_pitch = None

    for index, event in enumerate(absolute_pitches):
        pitches = event if isinstance(event, list) else [event]
        for pitch in pitches:
            min_pitch = pitch if min_pitch is None else min(min_pitch, pitch)
            max_pitch = pitch if max_pitch is None else max(max_pitch, pitch)
            rect = Rectangle(
                (index, pitch - 0.4),
                1.0,
                0.8,
                facecolor="#219ebc",
                edgecolor="#023047",
                alpha=0.8,
            )
            ax.add_patch(rect)

    ax.set_xlim(0, max(len(absolute_pitches), 1))
    ax.set_ylim((min_pitch or 60) - 2, (max_pitch or 72) + 2)
    ax.set_title(title, fontsize=13)
    ax.set_xlabel("Event Index", fontsize=10)
    ax.set_ylabel("MIDI Pitch", fontsize=10)
    ax.grid(True, linestyle="--", alpha=0.25)
    return fig


def build_tree_figure(root_node, active_path_ids=None, max_val=12, title="Tree Explorer"):
    fig = Figure(figsize=(8, 5.5), tight_layout=True)
    ax = fig.add_subplot(111)

    if root_node is None:
        ax.text(0.5, 0.5, "Build trees to view the explorer", ha="center", va="center")
        ax.set_axis_off()
        return fig

    active_path_ids = set(active_path_ids or [])
    graph = nx.DiGraph()
    pos = {}
    labels = {}

    def assign_positions(node, depth=0, x_offset=0):
        try:
            symbol_value = float(node.symbol)
            if abs(symbol_value) > max_val:
                return None, x_offset
        except (TypeError, ValueError):
            pass

        node_id = node.get_path_id()
        graph.add_node(node_id)
        labels[node_id] = "root" if node.symbol is None else str(node.symbol)

        if node.is_leaf():
            pos[node_id] = (x_offset, -depth)
            return x_offset, x_offset

        children_x = []
        current_x = x_offset
        for child in node.children:
            child_min_x, child_max_x = assign_positions(child, depth + 1, current_x)
            if child_min_x is not None:
                child_id = child.get_path_id()
                graph.add_edge(node_id, child_id)
                children_x.append(pos[child_id][0])
                current_x = child_max_x + 1

        if not children_x:
            pos[node_id] = (x_offset, -depth)
            return x_offset, x_offset

        center_x = sum(children_x) / len(children_x)
        pos[node_id] = (center_x, -depth)
        return x_offset, current_x - 1

    assign_positions(root_node)

    if graph.number_of_nodes() == 0:
        ax.text(0.5, 0.5, "Tree pruned by current display limit", ha="center", va="center")
        ax.set_axis_off()
        return fig

    default_edges = []
    highlighted_edges = []
    for edge in graph.edges():
        if edge[0] in active_path_ids and edge[1] in active_path_ids:
            highlighted_edges.append(edge)
        else:
            default_edges.append(edge)

    default_nodes = [node_id for node_id in graph.nodes() if node_id not in active_path_ids]
    highlighted_nodes = [node_id for node_id in graph.nodes() if node_id in active_path_ids]

    if default_edges:
        nx.draw_networkx_edges(graph, pos, edgelist=default_edges, ax=ax, edge_color="#94a3b8", width=1.0, alpha=0.65, arrows=False)
    if highlighted_edges:
        nx.draw_networkx_edges(graph, pos, edgelist=highlighted_edges, ax=ax, edge_color="#ef476f", width=2.6, alpha=0.95, arrows=False)

    if default_nodes:
        nx.draw_networkx_nodes(graph, pos, nodelist=default_nodes, ax=ax, node_color="#8ecae6", edgecolors="#023047", node_size=430)
    if highlighted_nodes:
        nx.draw_networkx_nodes(graph, pos, nodelist=highlighted_nodes, ax=ax, node_color="#ffd166", edgecolors="#d62828", linewidths=2.0, node_size=520)

    nx.draw_networkx_labels(graph, pos, labels=labels, ax=ax, font_size=8)
    ax.set_title(title, fontsize=13)
    ax.set_axis_off()
    return fig


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


def create_box_plot(parameter_range, box_plot_data, config_dict):
    """
    Creates a box plot from pre-calculated statistics using matplotlib's bxp,
    taking axis labels and file name from a configuration dictionary.

    Args:
        parameter_range (list): List of values for the x-axis labels.
        box_plot_data (list): List of dictionaries with box plot statistics
                              (min, Q1, median, Q3, max).
        config_dict (dict): Dictionary containing 'title', 'xlabel', 'ylabel', and 'filename'.
    """
    # 1. Transform data to matplotlib's required format for bxp
    bxp_stats = []
    for stats in box_plot_data:
        # Map user's keys to matplotlib's bxp keys
        bxp_stats.append({
            'whislo': stats['min'],
            'q1': stats['Q1'],
            'med': stats['median'],
            'q3': stats['Q3'],
            'whishi': stats['max'],
            # Required or useful keys for bxp
            'iqr': stats['Q3'] - stats['Q1'],
            'cilo': stats['Q1'],
            'cihi': stats['Q3'],
            'fliers': []
        })

    # 2. Create the plot
    fig, ax = plt.subplots(figsize=(10, 6))

    # 3. Plot the box plot using pre-calculated statistics
    ax.bxp(bxp_stats, positions=range(1, len(bxp_stats) + 1), showfliers=False)

    # 4. Set x-axis tick positions and labels
    ax.set_xticks(range(1, len(parameter_range) + 1))
    ax.set_xticklabels([str(p) for p in parameter_range])

    # 5. Add titles and labels from config_dict
    ax.set_title(config_dict.get('title', 'Box Plot (Default Title)'))
    ax.set_xlabel(config_dict.get('xlabel', 'X-Axis (Default Label)'))
    ax.set_ylabel(config_dict.get('ylabel', 'Y-Axis (Default Label)'))
    ax.grid(True, linestyle='--', alpha=0.6)

    # 6. Save the plot using filename from config_dict
    filename = config_dict.get('filename', 'box_plot_default.png')
    plt.savefig(filename)
    plt.close(fig)
    print(f"Box plot saved as '{filename}'")


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


def plot_and_save_branch_frequency(root_nodes, filename="branch_frequency.png", title="Distribution of Branch Lengths"):
    """
    Collects branch lengths from a list of root nodes, plots a 
    frequency histogram (raw counts), and saves it to the 'Graphs' directory.

    :param root_nodes: List of Node objects to analyze.
    :param filename: Name of the output file.
    :param title: Custom title heading for the plot.
    """
    # 1. Ensure the 'Graphs' directory exists
    directory = "Graphs"
    if not os.path.exists(directory):
        os.makedirs(directory)

    # 2. Collect distances from every root in the list
    all_distances = _collect_branch_lengths(root_nodes)

    if not all_distances:
        print("No branches found to plot.")
        return

    fig = build_branch_histogram_figure(root_nodes, title=title)
    save_path = os.path.join(directory, filename)
    fig.savefig(save_path, dpi=300)
    plt.close(fig)

    print(f"Graph successfully saved to: {save_path}")

# Example Usage:
# roots = [root1, root2]
# plot_and_save_branch_frequency(roots, "experiment_v2.png", "Analysis of Tree Depth Frequency")

# Example Usage:
# roots = [root1, root2]
# plot_and_save_branch_histogram(roots, "experiment_1_results.png")

# Example Usage:
# roots = [root1, root2, root3]
# plot_branch_length_histogram(roots)
# root_nodes = root_nodes[0:min(20, len(root_nodes))]


def plot_tree_graphs(root_nodes, filename="tree_structures_pruned.png", show_labels=False, max_val=12):
    root_nodes = root_nodes[0:min(20, len(root_nodes))]
    directory = "Graphs"
    if not os.path.exists(directory):
        os.makedirs(directory)

    num_trees = len(root_nodes)
    fig, axes = plt.subplots(num_trees, 1, figsize=(14, 8 * num_trees))
    if num_trees == 1:
        axes = [axes]

    for i, root in enumerate(root_nodes):
        G = nx.DiGraph()
        pos = {}
        labels = {}

        def assign_positions(node, depth=0, x_offset=0):
            # --- PRUNING LOGIC ---
            try:
                symbol_value = float(node.symbol)
                if abs(symbol_value) > max_val:
                    return None, x_offset  # Stop recursion here
            except (ValueError, TypeError):
                pass  # Keep non-numeric nodes

            node_id = id(node)
            G.add_node(node_id)
            if show_labels:
                labels[node_id] = node.symbol

            if node.is_leaf():
                pos[node_id] = (x_offset, -depth)
                return x_offset, x_offset

            children_x = []
            current_x = x_offset

            for child in node.children:
                # Recursive call
                child_min_x, child_max_x = assign_positions(
                    child, depth + 1, current_x)

                # If the child wasn't pruned, connect it
                if child_min_x is not None:
                    G.add_edge(node_id, id(child))
                    children_x.append(pos[id(child)][0])
                    current_x = child_max_x + 1

            # Handle case where all children of a non-leaf were pruned
            if not children_x:
                pos[node_id] = (x_offset, -depth)
                return x_offset, x_offset

            # Position parent in center of remaining (non-pruned) children
            center_x = sum(children_x) / len(children_x)
            pos[node_id] = (center_x, -depth)
            return x_offset, current_x - 1

        # Build the graph
        assign_positions(root)

        ax = axes[i]
        if G.number_of_nodes() > 0:
            nx.draw(G, pos, ax=ax,
                    with_labels=False,
                    node_size=400 if show_labels else 50,
                    node_color="#8ecae6",
                    edge_color="#023047",
                    width=0.8,
                    alpha=0.7,
                    arrows=False)

            if show_labels:
                nx.draw_networkx_labels(G, pos, labels=labels, ax=ax,
                                        font_size=7, font_weight="bold")
        else:
            ax.text(0.5, 0.5, "Root node exceeded limit (Tree Pruned)",
                    ha='center', va='center', color='red')

        ax.set_title(
            f"Tree {i+1} (Pruned at > |{max_val}|)", fontsize=14, pad=20)

    plt.tight_layout()
    save_path = os.path.join(directory, filename)
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Pruned graph saved to: {save_path}")


def create_interactive_tree(root_node, max_val=12):
    G = nx.DiGraph()
    pos = {}
    node_labels = {}  # The text that will appear ON the node

    def assign_positions(node, depth=0, x_offset=0):
        try:
            val = float(node.symbol)
            if abs(val) > max_val:
                return None, x_offset
        except:
            pass

        node_id = id(node)
        G.add_node(node_id)
        # Store the symbol for display
        node_labels[node_id] = str(node.symbol)

        if node.is_leaf():
            pos[node_id] = (x_offset, -depth)
            return x_offset, x_offset

        children_x = []
        curr_x = x_offset
        for child in node.children:
            c_min, c_max = assign_positions(child, depth + 1, curr_x)
            if c_min is not None:
                G.add_edge(node_id, id(child))
                children_x.append(pos[id(child)][0])
                curr_x = c_max + 1

        if not children_x:
            pos[node_id] = (x_offset, -depth)
            return x_offset, x_offset

        center_x = sum(children_x) / len(children_x)
        pos[node_id] = (center_x, -depth)
        return x_offset, curr_x - 1

    assign_positions(root_node)

    # ... (Edge trace logic remains the same as before) ...
    edge_x, edge_y = [], []
    for edge in G.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])
    edge_trace = go.Scatter(x=edge_x, y=edge_y, line=dict(
        width=1, color='#888'), hoverinfo='none', mode='lines')

    # --- NODE TRACE WITH VISIBLE LABELS ---
    node_x, node_y, display_text = [], [], []
    for node in G.nodes():
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)
        display_text.append(node_labels[node])

    node_trace = go.Scatter(
        x=node_x, y=node_y,
        mode='markers+text',       # <--- KEY CHANGE: Adds text to markers
        text=display_text,         # The actual values
        textposition="top center",  # Places text above the circle
        hoverinfo='text',
        marker=dict(size=15, color='#8ecae6', line_width=2),
        textfont=dict(size=10, color='black')
    )

    fig = go.Figure(data=[edge_trace, node_trace],
                    layout=go.Layout(
                    title=f'Tree Visualization (Pruned at {max_val})',
                    hovermode='closest',
                    xaxis=dict(showgrid=False, zeroline=False,
                               showticklabels=False),
                    yaxis=dict(showgrid=False, zeroline=False, showticklabels=False))
                    )
    fig.show()


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
