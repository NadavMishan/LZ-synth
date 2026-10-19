import LZ_MIDI_data
import Utils
import Visualize
# if __name__ == "__main__":
#     parameter_range = range(1, 15, 1)
#     # parameter_range = [2, 4, 8]
#     data = []
#     box_plot_data = []

#     for steps in parameter_range:
#         sequence_lengths = LZ_MIDI_data.lz_synth_main(number_of_songs_per_tree=128, sentence_length=5000,
#                                                       number_of_sentences=1, max_depth=None, steps=steps, play_song=False, get_data=False, get_sequence_lengths=True)
#         sequence_lengths.remove(min(sequence_lengths))
#         data.append(sequence_lengths)

#     for set in data:
#         box_plot_data.append(Utils.calculate_box_plot_stats(set))

#     print("Box Plot Data: ", box_plot_data)
#     config_dict = {
#         'title': 'Sequence Length Distribution vs Steps',
#         'xlabel': 'Number of Steps',
#         'ylabel': 'Sequence Length',
#         'filename': 'lz_midi_sequence_steps_box_plot_merged.png'
#     }

#     Visualize.create_box_plot(parameter_range, box_plot_data, config_dict)

if __name__ == "__main__":
    data = []
    box_plot_data = []
    steps = 10
    SPR = 1200
    # examples = [(2, 1), (50, 1), (1200, 1), (1200, 5), (1200, 15), (25, 15)]
    examples = [(1200, 1)]
    for SPR, steps in examples:

        Trees = LZ_MIDI_data.lz_synth_main(number_of_songs_per_tree=SPR, sentence_length=100,
                                           number_of_sentences=1, max_depth=None, steps=steps, play_song=True, get_data=False, get_sequence_lengths=False, get_trees=True)
        print(f"Visualizing Trees for SPR={SPR}, steps={steps}")

        Visualize.plot_and_save_branch_frequency(
            Trees, filename=f"SPR={SPR}_steps={steps}_branch_frequency.png", title=f"Branch Frequency Songs per tree={SPR} Steps={steps}")

        Visualize.plot_tree_graphs(
            Trees, filename=f"SPR={SPR}_steps={steps}_tree_structure.png", main_title=f"Tree Structure, Songs per tree={SPR} Steps={steps}")
