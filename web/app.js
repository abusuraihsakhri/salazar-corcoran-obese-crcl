import { estimateCrCl, calculateCsv } from './calculator.js';
const form = document.getElementById('single-form');
const output = document.getElementById('single-result');
const error = document.getElementById('single-error');
const csvInput = document.getElementById('csv-input');
const batchMessage = document.getElementById('batch-message');
const download = document.getElementById('download');
let url = null;

form.addEventListener('submit', (event) => {
  event.preventDefault();
  output.hidden = true;
  error.textContent = '';
  try {
    const value = estimateCrCl(Object.fromEntries(new FormData(form)));
    document.getElementById('crcl').textContent = value.toFixed(2);
    output.hidden = false;
  } catch (exc) { error.textContent = exc.message; }
});

csvInput.addEventListener('change', async () => {
  download.hidden = true;
  batchMessage.textContent = '';
  if (url) URL.revokeObjectURL(url);
  url = null;
  const file = csvInput.files?.[0];
  if (!file) return;
  try {
    if (file.size > 2 * 1024 * 1024) throw new Error('Maximum CSV size is 2 MiB');
    const result = calculateCsv(await file.text());
    url = URL.createObjectURL(new Blob([result.csv], { type: 'text/csv;charset=utf-8' }));
    download.href = url;
    download.download = 'salazar-corcoran-results.csv';
    batchMessage.textContent = result.count + ' records validated and calculated; ready to download.';
    download.hidden = false;
  } catch (exc) { batchMessage.textContent = 'CSV error: ' + exc.message; }
});

window.addEventListener('pagehide', () => { if (url) URL.revokeObjectURL(url); });
