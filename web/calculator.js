/** Salazar–Corcoran (1988); years, kg, m, mg/dL => mL/min. */
export const FIELDS = ['sex', 'age_years', 'weight_kg', 'height_m', 'serum_creatinine_mg_dl'];
export const RESULT_FIELD = 'creatinine_clearance_ml_min';

function positiveFinite(value, label) {
  if (value === null || value === undefined || String(value).trim() === '') {
    throw new Error(label + ' is required');
  }
  const number = Number(value);
  if (!Number.isFinite(number) || number <= 0) throw new Error(label + ' must be a positive finite number');
  return number;
}

export function estimateCrCl(values) {
  const sex = typeof values.sex === 'string' ? values.sex.trim().toLowerCase() : '';
  if (sex !== 'male' && sex !== 'female') throw new Error("sex must be 'male' or 'female' (equation coefficient)");
  const age = positiveFinite(values.age_years, 'age_years');
  const weight = positiveFinite(values.weight_kg, 'weight_kg');
  const height = positiveFinite(values.height_m, 'height_m');
  const scr = positiveFinite(values.serum_creatinine_mg_dl, 'serum_creatinine_mg_dl');
  if (age < 18) throw new Error('The equation is intended for adults aged 18 years or older');
  if (sex === 'male') {
    if (age >= 137) throw new Error('age_years must be less than 137 for the male equation');
    return ((137 - age) * (0.285 * weight + 12.1 * height ** 2)) / (51 * scr);
  }
  if (age >= 146) throw new Error('age_years must be less than 146 for the female equation');
  return ((146 - age) * (0.287 * weight + 9.74 * height ** 2)) / (60 * scr);
}

export function parseCSV(csvText) {
  const records = [];
  let record = [], field = '', quoted = false, closedQuote = false;
  const text = csvText.replace(/^\uFEFF/, '');
  for (let i = 0; i < text.length; i++) {
    const char = text[i];
    if (quoted) {
      if (char === '"' && text[i + 1] === '"') { field += '"'; i++; }
      else if (char === '"') { quoted = false; closedQuote = true; }
      else field += char;
    } else if (closedQuote) {
      if (char === ',') { record.push(field); field = ''; closedQuote = false; }
      else if (char === '\n' || char === '\r') {
        record.push(field); records.push(record); record = []; field = ''; closedQuote = false;
        if (char === '\r' && text[i + 1] === '\n') i++;
      } else throw new Error('Malformed CSV: unexpected content after closing quote');
    } else if (char === '"') {
      if (field !== '') throw new Error('Malformed CSV: quote in unquoted value');
      quoted = true;
    } else if (char === ',') { record.push(field); field = ''; }
    else if (char === '\n' || char === '\r') {
      record.push(field); records.push(record); record = []; field = '';
      if (char === '\r' && text[i + 1] === '\n') i++;
    } else field += char;
  }
  if (quoted) throw new Error('Malformed CSV: unterminated quoted field');
  if (closedQuote || field !== '' || record.length > 0) {
    record.push(field);
    records.push(record);
  }
  return records;
}

function csvCell(value) {
  let text = String(value ?? '');
  if (/^\s*[=+\-@]/.test(text)) text = "'" + text;
  return '"' + text.replaceAll('"', '""') + '"';
}

export function calculateCsv(csvText) {
  const records = parseCSV(csvText);
  if (records.length === 0 || (records.length === 1 && records[0].every(x => x === ''))) throw new Error('CSV is empty');
  const columns = records[0];
  if (columns.some(x => !x) || new Set(columns).size !== columns.length) throw new Error('CSV headers must be unique and non-empty');
  for (const name of FIELDS) if (!columns.includes(name)) throw new Error('Missing CSV column: ' + name);
  if (columns.includes(RESULT_FIELD)) throw new Error('Input already contains ' + RESULT_FIELD);
  const data = records.slice(1).filter(row => !(row.length === 1 && row[0] === ''));
  if (data.length > 2000) throw new Error('Maximum 2,000 data rows per file');
  const calculated = data.map((row, index) => {
    if (row.length !== columns.length) throw new Error('CSV row ' + (index + 2) + ': invalid column count');
    const entry = Object.fromEntries(columns.map((name, position) => [name, row[position]]));
    try { return [...row, estimateCrCl(entry).toFixed(2)]; }
    catch (error) { throw new Error('CSV row ' + (index + 2) + ': ' + error.message); }
  });
  const output = [[...columns, RESULT_FIELD], ...calculated].map(row => row.map(csvCell).join(',')).join('\r\n') + '\r\n';
  return { csv: output, count: calculated.length, preview: calculated.slice(0, 5).map(row => row.at(-1)) };
}
