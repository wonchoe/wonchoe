"use strict";
const arena = document.querySelector("#playground");
const canvas = document.querySelector("#trails");
const context = canvas.getContext("2d");
const pointer = document.querySelector("#pointer");
const trailControl = document.querySelector("#trail");
const status = document.querySelector("#status");
const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
const palettes = {
  comet: {color: "#8ad5fb", secondary: "#a78bfa", mood: "a little cosmic", shape: "M4 3L31 23L18 25L12 38Z"},
  candy: {color: "#f69bd4", secondary: "#ffa7a0", mood: "sweet by design", shape: "M4 3L31 23L18 25L12 38Z"},
  pixel: {color: "#93e8bf", secondary: "#7acdfa", mood: "a bit nostalgic", shape: "M4 3H10V9H16V15H22V21H28V27H16V39H10V27H4Z"},
  orbit: {color: "#baa7ff", secondary: "#f2a3d4", mood: "out of this world", shape: "M18 2L22 13L34 17L22 21L18 34L14 21L2 17L14 13Z"}
};
let theme = palettes.comet;
let particles = [];
let last = null;
let position = {x: 0, y: 0};
let frame = null;
let previousTime = 0;
let width = 0, height = 0;

function selectTheme(name) {
  theme = palettes[name];
  document.querySelectorAll(".theme").forEach(function(button) {
    button.setAttribute("aria-pressed", String(button.dataset.theme === name));
  });
  document.documentElement.style.setProperty("--accent", theme.color);
  document.querySelector("#mood").textContent = theme.mood;
  pointer.innerHTML = '<svg viewBox="0 0 38 46" xmlns="http://www.w3.org/2000/svg"><path d="' +
    theme.shape + '" fill="' + theme.color + '" stroke="#f4f7ff" stroke-width="2.5" stroke-linejoin="round"/>' +
    '<path d="M14 15L22 23" stroke="' + theme.secondary + '" stroke-width="3" stroke-linecap="round"/></svg>';
  status.textContent = name[0].toUpperCase() + name.slice(1) + " cursor selected.";
}

function resize() {
  const rect = arena.getBoundingClientRect();
  width = rect.width; height = rect.height;
  const scale = Math.min(window.devicePixelRatio || 1, 2);
  canvas.width = Math.round(width * scale);
  canvas.height = Math.round(height * scale);
  context.setTransform(scale, 0, 0, scale, 0, 0);
  if (!arena.classList.contains("is-active")) position = {x: width / 2, y: height / 2};
}

function paint(time) {
  const delta = previousTime ? Math.min(3, (time - previousTime) / 16.667) : 1;
  previousTime = time;
  context.clearRect(0, 0, width, height);
  particles = particles.filter(function(particle) {
    particle.life -= delta * .022;
    particle.x += particle.vx * delta;
    particle.y += particle.vy * delta;
    if (particle.life <= 0) return false;
    context.globalAlpha = particle.life;
    context.fillStyle = particle.color;
    context.beginPath();
    context.arc(particle.x, particle.y, Math.max(.1, particle.size * particle.life), 0, Math.PI * 2);
    context.fill();
    return true;
  });
  context.globalAlpha = 1;
  if (particles.length) frame = requestAnimationFrame(paint);
  else { frame = null; previousTime = 0; }
}

function sparkle(x, y, burst) {
  if (reducedMotion.matches || !trailControl.checked) return;
  const count = burst ? 28 : 2;
  for (let i = 0; i < count; i++) {
    const angle = Math.random() * Math.PI * 2;
    const speed = burst ? 1 + Math.random() * 3 : .2;
    particles.push({x: x, y: y, vx: Math.cos(angle) * speed, vy: Math.sin(angle) * speed,
      life: 1, size: burst ? 2 + Math.random() * 4 : 2 + Math.random() * 2,
      color: i % 2 ? theme.color : theme.secondary});
  }
  if (particles.length > 240) particles.splice(0, particles.length - 240);
  if (frame === null) frame = requestAnimationFrame(paint);
}

function move(x, y) {
  position = {x: Math.max(0, Math.min(width - 10, x)), y: Math.max(0, Math.min(height - 10, y))};
  pointer.style.transform = "translate(" + position.x + "px," + position.y + "px)";
  arena.classList.add("is-active");
  document.querySelector("#hint").textContent = "Click for a little extra color";
  document.querySelector("#coordinates").textContent = Math.round(position.x) + " / " + Math.round(position.y);
  if (!reducedMotion.matches) {
    const dx = (position.x / width - .5), dy = (position.y / height - .5);
    arena.style.setProperty("--eye-x", dx * 13 + "px");
    arena.style.setProperty("--eye-y", dy * 13 + "px");
    arena.style.setProperty("--rx", -dy * 6 + "deg");
    arena.style.setProperty("--ry", dx * 6 + "deg");
  }
  if (!last || Math.hypot(position.x - last.x, position.y - last.y) > 4) {
    sparkle(position.x + 4, position.y + 4, false);
    last = {...position};
  }
}

function clear() {
  particles = [];
  if (frame !== null) cancelAnimationFrame(frame);
  frame = null; previousTime = 0;
  context.clearRect(0, 0, width, height);
}

document.querySelectorAll(".theme").forEach(function(button) {
  button.addEventListener("click", function() { selectTheme(button.dataset.theme); });
});
arena.addEventListener("pointermove", function(event) {
  const rect = arena.getBoundingClientRect();
  move(event.clientX - rect.left, event.clientY - rect.top);
});
arena.addEventListener("pointerdown", function(event) {
  arena.focus({preventScroll: true});
  const rect = arena.getBoundingClientRect();
  move(event.clientX - rect.left, event.clientY - rect.top);
  sparkle(position.x, position.y, true);
});
arena.addEventListener("pointerleave", function() {
  arena.classList.remove("is-active"); last = null;
  ["--rx", "--ry", "--eye-x", "--eye-y"].forEach(function(key) { arena.style.removeProperty(key); });
});
arena.addEventListener("keydown", function(event) {
  const steps = {ArrowLeft: [-18, 0], ArrowRight: [18, 0], ArrowUp: [0, -18], ArrowDown: [0, 18]};
  if (steps[event.key]) {
    event.preventDefault();
    move(position.x + steps[event.key][0], position.y + steps[event.key][1]);
  } else if (event.code === "Space" || event.key === "Enter") {
    event.preventDefault();
    move(position.x, position.y);
    sparkle(position.x, position.y, true);
  } else if (event.key === "Escape") {
    clear(); arena.classList.remove("is-active");
  }
});
arena.addEventListener("blur", function() { arena.classList.remove("is-active"); });
document.querySelector("#clear").addEventListener("click", function() {
  clear(); status.textContent = "Canvas cleared.";
});
trailControl.addEventListener("change", function() {
  if (!trailControl.checked) clear();
});
function motionPreference() {
  trailControl.checked = !reducedMotion.matches;
  trailControl.disabled = reducedMotion.matches;
  trailControl.parentElement.title = reducedMotion.matches ? "Trails respect your reduced-motion preference" : "";
  if (reducedMotion.matches) clear();
}
reducedMotion.addEventListener("change", motionPreference);
document.addEventListener("visibilitychange", function() { if (document.hidden) clear(); });
new ResizeObserver(resize).observe(arena);
resize();
motionPreference();
selectTheme("comet");
