"use strict";

const state = {
  data: null,
  selectedPath: "safe",
  timers: [],
};

const elements = {
  pathTitle: document.querySelector("#path-title"),
  pathVerdict: document.querySelector("#path-verdict"),
  timeline: document.querySelector("#timeline"),
  metrics: document.querySelector("#metrics"),
  decisionNote: document.querySelector("#decision-note"),
  verdictPanel: document.querySelector("#verdict-panel"),
  verdictAction: document.querySelector("#verdict-action"),
  verdictExplanation: document.querySelector("#verdict-explanation"),
  riskDisclaimer: document.querySelector("#risk-disclaimer"),
  animationStatus: document.querySelector("#animation-status"),
  safePathButton: document.querySelector("#path-safe"),
  riskPathButton: document.querySelector("#path-risk"),
};

function clearTimers() {
  state.timers.forEach((timer) => window.clearTimeout(timer));
  state.timers = [];
}

function escapeText(value) {
  return String(value ?? "");
}

function metricClass(tone) {
  if (tone === "safe") return "safe-value";
  if (tone === "risk") return "risk-value";
  if (tone === "unknown") return "unknown-value";
  return "";
}

function renderMetrics(path) {
  elements.metrics.replaceChildren();
  path.metrics.forEach((item) => {
    const wrapper = document.createElement("div");
    wrapper.className = "metric";

    const term = document.createElement("dt");
    term.textContent = escapeText(item.label);

    const value = document.createElement("dd");
    value.textContent = escapeText(item.value);
    const toneClass = metricClass(item.tone);
    if (toneClass) value.classList.add(toneClass);

    wrapper.append(term, value);
    elements.metrics.append(wrapper);
  });
}

function renderTimeline(path, animate = true) {
  clearTimers();
  elements.timeline.replaceChildren();
  elements.timeline.classList.toggle("is-risk", path.id === "unsafe");

  path.steps.forEach((step, index) => {
    const item = document.createElement("li");
    item.className = "timeline-step";

    const marker = document.createElement("span");
    marker.className = "timeline-marker";
    marker.textContent = String(index + 1).padStart(2, "0");
    marker.setAttribute("aria-hidden", "true");

    const content = document.createElement("div");
    content.className = "timeline-content";

    const token = document.createElement("span");
    token.className = "state-token";
    token.textContent = escapeText(step.state);

    const title = document.createElement("h4");
    title.textContent = escapeText(step.title);

    const detail = document.createElement("p");
    detail.textContent = escapeText(step.detail);

    content.append(token, title, detail);
    item.append(marker, content);
    elements.timeline.append(item);

    const reveal = () => item.classList.add("is-visible");
    if (!animate || window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      reveal();
    } else {
      state.timers.push(window.setTimeout(reveal, 140 + index * 260));
    }
  });

  const duration = animate ? 140 + path.steps.length * 260 : 0;
  state.timers.push(window.setTimeout(() => {
    elements.animationStatus.textContent = `${path.title} path complete: ${path.verdict}.`;
  }, duration));
}

function updatePathButtons(pathId) {
  [elements.safePathButton, elements.riskPathButton].forEach((button) => {
    const active = button.dataset.path === pathId;
    button.classList.toggle("is-active", active);
    button.setAttribute("aria-pressed", String(active));
  });
}

function selectPath(pathId, animate = true) {
  if (!state.data || !state.data.paths[pathId]) return;

  state.selectedPath = pathId;
  const path = state.data.paths[pathId];
  const isRisk = pathId === "unsafe";

  updatePathButtons(pathId);
  elements.pathTitle.textContent = path.title;
  elements.pathVerdict.textContent = path.verdict;
  elements.pathVerdict.className = `status-pill ${isRisk ? "status-risk" : "status-pass"}`;
  elements.decisionNote.innerHTML = `<strong>${escapeText(path.decision_heading)}</strong> ${escapeText(path.decision_note)}`;
  elements.verdictPanel.className = `verdict-panel ${isRisk ? "verdict-risk" : "verdict-safe"}`;
  elements.verdictAction.textContent = path.next_action;
  elements.verdictExplanation.textContent = path.explanation;
  elements.riskDisclaimer.hidden = !isRisk;

  renderTimeline(path, animate);
  renderMetrics(path);
}

async function loadDemo() {
  try {
    const response = await fetch("demo-data.json", { cache: "no-store" });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    state.data = await response.json();
    selectPath("safe", true);
  } catch (error) {
    elements.timeline.innerHTML = "<li class=\"timeline-step is-visible\"><div class=\"timeline-content\"><h4>Demo data unavailable</h4><p>Open the canonical evidence pack using the link above.</p></div></li>";
    elements.animationStatus.textContent = `Demo data failed to load: ${error.message}`;
  }
}

document.querySelectorAll("[data-path]").forEach((button) => {
  button.addEventListener("click", () => selectPath(button.dataset.path, true));
});

document.querySelector("#run-safe").addEventListener("click", () => {
  selectPath("safe", true);
  document.querySelector("#demo").scrollIntoView({ behavior: "smooth", block: "start" });
});

document.querySelector("#run-risk").addEventListener("click", () => {
  selectPath("unsafe", true);
  document.querySelector("#demo").scrollIntoView({ behavior: "smooth", block: "start" });
});

document.querySelector("#replay-path").addEventListener("click", () => selectPath(state.selectedPath, true));

loadDemo();
