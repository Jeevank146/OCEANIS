import { createRequire } from 'node:module';

const require = createRequire(import.meta.url);
const { chromium } = require('C:/Users/fairn/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const browser = await chromium.launch({ headless: true, executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe' });

const cases = [
  { name: 'Test Marine Sector Alpha', lat: 11.1, lon: 74.2, wave: 0.8, wind: 12, confidence: 86, safety: 'NORMAL OPERATIONAL PARAMETERS' },
  { name: 'Test Marine Sector Beta', lat: 18.2, lon: 70.4, wave: 2.2, wind: 31, confidence: 61, safety: 'CAUTION / HEIGHTENED VIGILANCE' },
];
const observed = [];

for (const testCase of cases) {
  const targetTimes = [];
  const context = await browser.newContext({ viewport: { width: 1366, height: 900 } });
  await context.addInitScript((location) => {
    localStorage.setItem('oceanis_active_validation_v2', JSON.stringify({
      status: 'VALID_COASTAL', is_coastal: true, is_marine: true,
      location_name: location.name, display_name: location.name, city: location.name,
      state: 'Test State', country: 'India', latitude: location.lat, longitude: location.lon,
      distance_to_coast_km: 0, nearest_port: null, marine_context: 'Test marine context',
      coordinates_formatted: `${location.lat}, ${location.lon}`,
    }));
  }, testCase);
  const page = await context.newPage();
  await page.route('**/api/v1/orchestrator/decision**', async (route) => {
    const body = route.request().postDataJSON();
    if (body.latitude !== testCase.lat || body.longitude !== testCase.lon) throw new Error('LocationContext coordinates were not forwarded');
    targetTimes.push(body.target_datetime);
    const scenario = { departure_time: 'dynamic', location_name: testCase.name, latitude: testCase.lat, longitude: testCase.lon, decision: testCase.confidence > 70 ? 'Suitable' : 'Caution', confidence_score: testCase.confidence, risk_level: testCase.confidence > 70 ? 'LOW' : 'MODERATE', key_conditions: [] };
    await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({
      query_intent: 'WHAT_IF', primary_answer: `Evidence comparison for ${testCase.name}`, decision: scenario.decision,
      summary: 'Evidence-backed test response', confidence: testCase.confidence, confidence_reasons: ['test'],
      safety_status: testCase.safety, guardrail_actions: [], key_findings: [], why_decision: {},
      evidence: [
        { source: 'Test feed', parameter: 'significant_wave_height', value: testCase.wave, unit: 'm', observation_type: 'Forecast', freshness: 'Fresh' },
        { source: 'Test feed', parameter: 'wind_speed', value: testCase.wind, unit: 'km/h', observation_type: 'Forecast', freshness: 'Fresh' },
      ], agents_consulted: [], freshness_summary: 'Fresh', warnings: [], limitations: [],
      location: { name: testCase.name, latitude: testCase.lat, longitude: testCase.lon }, requested_time: 'dynamic',
      what_if_comparison: { status: 'success', base_scenario: scenario, what_if_scenario: scenario, changed_factors: ['dynamic time'], decision_difference: 'evidence evaluated', confidence_difference: 0 },
      comparison_data: null, entities_extracted: {}, generated_at: new Date().toISOString(),
    }) });
  });
  await page.goto('http://127.0.0.1:5173/what-if', { waitUntil: 'domcontentloaded' });
  await page.getByRole('button', { name: /Run Scenario Simulation/i }).click();
  await page.locator('.whatif-result-card').waitFor();
  const text = await page.locator('#what-if-scenarios').innerText();
  for (const expected of [testCase.name, `${testCase.wave} m`, `${testCase.wind} km/h`, `${testCase.confidence}%`, testCase.safety]) {
    if (!text.includes(expected)) throw new Error(`Missing dynamic value: ${expected}`);
  }
  if (targetTimes.length !== 2 || targetTimes[0] === targetTimes[1]) throw new Error('Departure alternatives were not evaluated independently');
  observed.push({ location: testCase.name, wave: testCase.wave, wind: testCase.wind, confidence: testCase.confidence });
  await context.close();
}

await browser.close();
if (observed[0].wave === observed[1].wave || observed[0].wind === observed[1].wind) throw new Error('Evidence metrics did not change');
console.log(JSON.stringify({ passed: true, observed }, null, 2));
