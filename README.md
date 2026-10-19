# Copying Versus Randomization in Lempel-Ziv Music Synthesis

Supplementary site for the ICSEE paper by Nadav Mishan and Ram Zamir. It presents Bach repeat experiments and generated song examples, with audio and video previews, visualizations, and downloadable MIDI files.

**Open the site:** [nadavmishan.github.io/LZ-synth](https://nadavmishan.github.io/LZ-synth/)

**Preprint:** [arXiv:2609.11353](https://arxiv.org/abs/2609.11353) · Presented at ICSEE; IEEE Xplore publication forthcoming.

## Preview locally

From the repository folder, run:

```powershell
py -m http.server 8000
```

Then open [http://localhost:8000](http://localhost:8000). Stop the server with **Ctrl+C**.

## Publish updates

The GitHub Actions workflow in `.github/workflows/pages.yml` deploys the site when changes are pushed to `main` or `master`. Set the repository’s **Settings → Pages → Build and deployment → Source** to **GitHub Actions**.

The page is built from `index.html`, `styles.css`, and `site.js`. Update the catalog in `site.js` when adding or removing examples; keep their media in `Songs/` or `BachRepeatExperiments/`.
