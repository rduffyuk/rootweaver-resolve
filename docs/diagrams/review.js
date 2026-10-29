const preference = matchMedia('(prefers-reduced-motion: reduce)');
const images = [...document.querySelectorAll('[data-view]')];
const toggle = document.querySelector('#motion');
const replay = document.querySelector('#replay');
const status = document.querySelector('#state');
let still = preference.matches;
let revision = 0;
function render() {
  for (const image of images) image.src = `${image.dataset.view}${still ? '.static' : ''}.svg?view=${revision++}`;
  toggle.textContent = still ? 'Play animation' : 'Use still diagrams';
  toggle.setAttribute('aria-pressed', String(still));
  toggle.disabled = replay.disabled = preference.matches;
  status.textContent = preference.matches ? 'Reduced motion: static views.' : still ? 'Static views. Direction and labels remain visible.' : 'Direction only. Animation stops after 4.8 seconds.';
}
toggle.addEventListener('click', () => { still = !still; render(); });
replay.addEventListener('click', () => { still = false; render(); });
preference.addEventListener('change', () => { still = preference.matches; render(); });
render();
