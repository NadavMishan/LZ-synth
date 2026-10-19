# LZ-Synth
   
   This repository is supplementary  to our confernce paper: TBD.
   
   ## Examples of songs with diffrent parameters:
   - [Songs per tree: 50     Steps: 1    Average sequance length: 2.6](Songs/Songs_per_tree_50_steps_1_Ls_2.6.mp3)
   - [Songs per tree: 1200   Steps: 1    Average sequance length: 3.6](Songs/Songs_per_tree_1200_steps_1_Ls_3.6.mp3)
   - [Songs per tree: 1200   Steps: 5    Average sequance length: 6.64](Songs/Songs_per_tree_1200_stpes_5_Ls_6.64.mp3)
   - [Songs per tree: 1200   Steps: 15   Average sequance length: 16.5](Songs/Song_per_tree_1200_steps_15_Ls_16.5.mp3)
   - [Songs per tree: 25     Steps: 15   Average sequance length: 14.3](Songs/Song_per_tree_25_steps_15_Ls_14.3.mp3)
  
## How to run the code
- To run the code you need to download the MAESTRO database to the code's folder: https://magenta.withgoogle.com/datasets/maestro, specificly the midi version ("maestro-v3.0.0-midi.zip").
    
- Run the pre-processing code in the file: "maestro_to_vector.py"
    
- You can now run LZ_MIDI_data.py to listen to the LZ_synt.

## Song examples website

The repository root contains a static GitHub Pages site for the song examples in `Songs/` and the Bach repeat experiments in `BachRepeatExperiments/`. The page includes audio and video players, visualizations, MIDI downloads, and experiment summaries.

The `Deploy song examples to GitHub Pages` workflow publishes the site whenever changes are pushed to `main` or `master`. In the GitHub repository, set **Settings → Pages → Build and deployment → Source** to **GitHub Actions**. After the first deployment, the site is available at `https://nadavmishan.github.io/LZ-synth/`.

To add or remove examples, update the catalog near the top of `site.js`; the media files remain in their existing folders.
