const songExamples = [
  {title:"Songs per tree · 50", detail:"1 step · average sequence length 2.6", audio:"Songs/Songs_per_tree_50_steps_1_Ls_2.6.mp3"},
  {title:"Songs per tree · 1,200", detail:"1 step · average sequence length 3.6", audio:"Songs/Songs_per_tree_1200_steps_1_Ls_3.6.mp3"},
  {title:"Songs per tree · 1,200", detail:"5 steps · average sequence length 6.64", audio:"Songs/Songs_per_tree_1200_stpes_5_Ls_6.64.mp3"},
  {title:"Song per tree · 1,200", detail:"15 steps · average sequence length 16.5", audio:"Songs/Song_per_tree_1200_steps_15_Ls_16.5.mp3"},
  {title:"Song per tree · 25", detail:"15 steps · average sequence length 14.3", audio:"Songs/Song_per_tree_25_steps_15_Ls_14.3.mp3"},
];
const experiments = [
  {n:"001", midi:"generated.mid", audio:"generated-converted.mp3", plot:"branch_length_histogram.png", summary:"summary.json"},
  {n:"005", midi:"repeat_5.mid", audio:"repeat_5-converted.mp3", plot:"repeat_5.png", summary:"summary.json"},
  {n:"010", midi:"repeat_10.mid", audio:"repeat_10-converted.mp3", plot:"repeat_10.png", summary:"summary.json"},
  {n:"015", midi:"repeat_15.mid", audio:"repeat_15-converted.mp3", plot:"repeat_15.png", summary:"summary.json"},
  {n:"020", midi:"generated.mid", audio:"generated-converted.mp3", plot:"branch_length_histogram.png", summary:"summary.json"},
  {n:"040", midi:"generated.mid", audio:"generated-converted.mp3", plot:"branch_length_histogram.png", summary:"summary.json", branches:[
    {title:"Outlier branch", midi:"outlier_branch.mid", audio:"outlier_branch-converted.mp3"},
    {title:"Second-longest branch", midi:"second_longest_branch.mid", audio:"second_longest_branch-converted.mp3"},
  ]},
];
const songGrid = document.querySelector("#song-grid");
songExamples.forEach((song, i) => {
  const card = document.createElement("article"); card.className = "song-card"; card.dataset.kind = "audio"; card.dataset.search = `${song.title} ${song.detail}`.toLowerCase();
  card.innerHTML = `<div class="card-top"><div><span class="card-index">EXAMPLE ${String(i+1).padStart(2,"0")}</span><h3>${song.title}</h3><span class="song-meta">${song.detail}</span></div><span class="tag">Audio</span></div><audio controls preload="none" src="${song.audio}">Your browser does not support audio playback.</audio><div class="card-links"><a href="${song.audio}" download>Download audio ↗</a></div>`;
  songGrid.append(card);
});
document.querySelector("#song-count").textContent = `${songExamples.length} audio examples`;

const experimentGrid = document.querySelector("#experiment-grid");
experiments.forEach((run) => {
  const base = `BachRepeatExperiments/repeat_${run.n}/`;
  const card = document.createElement("article"); card.className = "experiment-card";
  const plot = `<img src="${base}${run.plot}" alt="Visualization for Bach repeat ${Number(run.n)}" loading="lazy" onerror="this.outerHTML='<div class=\'missing-plot\'>PLOT NOT AVAILABLE</div>'">`;
  const audio = `<audio controls preload="none" src="${base}${run.audio}">Your browser does not support audio playback.</audio>`;
  const branches = (run.branches || []).map(branch => `<div class="branch-preview"><div class="branch-preview-heading"><span class="card-index">REPEAT ${Number(run.n)} · EXTRACTED BRANCH</span><h4>${branch.title}</h4></div><audio controls preload="none" src="${base}${branch.audio}">Your browser does not support audio playback.</audio><div class="asset-links"><a href="${base}${branch.audio}" download>Download audio ↗</a><a href="${base}${branch.midi}" download>Download MIDI ↗</a></div></div>`).join("");
  card.innerHTML = `<div class="card-top"><div><span class="card-index">REPEAT RUN</span><h3>${Number(run.n)} repeats</h3></div><span class="tag">Bach · C major</span></div>${plot}${audio}<div class="asset-links"><a href="${base}${run.audio}" download>Download audio ↗</a><a href="${base}${run.midi}" download>Download MIDI ↗</a><a href="${base}${run.summary}">Run summary ↗</a></div>${branches ? `<div class="branch-previews">${branches}</div>` : ""}`;
  experimentGrid.append(card);
});

const search = document.querySelector("#search");
function filterSongs() {
  const query = search.value.trim().toLowerCase();
  document.querySelectorAll(".song-card").forEach(card => {
    card.hidden = !card.dataset.search.includes(query);
  });
}
search.addEventListener("input", filterSongs);
