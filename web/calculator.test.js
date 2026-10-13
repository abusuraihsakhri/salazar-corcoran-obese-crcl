import assert from 'node:assert/strict';
import { test } from 'node:test';
import { estimateCrCl, calculateCsv, parseCSV } from './calculator.js';

test('male reference example', () => {
  assert.ok(Math.abs(estimateCrCl({sex:'male',age_years:45,weight_kg:120,height_m:1.75,serum_creatinine_mg_dl:1.2}) - 107.1172385620915) < 1e-10);
});
test('female reference example', () => {
  assert.ok(Math.abs(estimateCrCl({sex:'female',age_years:55,weight_kg:110,height_m:1.65,serum_creatinine_mg_dl:1.4}) - 62.92774583333333) < 1e-10);
});
test('invalid inputs', () => {
  const valid = {sex:'male',age_years:45,weight_kg:120,height_m:1.75,serum_creatinine_mg_dl:1.2};
  for (const override of [{serum_creatinine_mg_dl:0}, {weight_kg:-2}, {height_m:'NaN'}, {age_years:17}, {sex:'unknown'}, {age_years:''}])
    assert.throws(() => estimateCrCl({...valid,...override}));
});
test('quoted and multiline CSV with formula injection protection', () => {
  const csv = 'case_id,sex,age_years,weight_kg,height_m,serum_creatinine_mg_dl\r\n"=1+1",male,45,120,1.75,1.2\r\n"line\nbreak",female,55,110,1.65,1.4\r\n';
  const result = calculateCsv(csv);
  assert.equal(result.count, 2);
  assert.deepEqual(result.preview, ['107.12', '62.93']);
  const parsed = parseCSV(result.csv);
  assert.equal(parsed[1][0], "'=1+1");
  assert.equal(parsed[2][0], 'line\nbreak');
});
test('malformed CSV rows', () => {
  const header = 'sex,age_years,weight_kg,height_m,serum_creatinine_mg_dl\n';
  assert.throws(() => calculateCsv(header + 'male,45,120,1.75,0\n'), /row 2/);
  assert.throws(() => calculateCsv(header + 'male,45,120,1.75\n'), /column count/);
  assert.throws(() => calculateCsv(header + '"male,45,120,1.75,1.2\n'), /unterminated/);
});
