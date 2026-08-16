const puppeteer = require('puppeteer');
const fs = require('fs');
const path = require('path');

(async () => {
  const browser = await puppeteer.launch({ headless: 'new' });
  
  // Edge Case 1: Missing Stream 3
  console.log(`\n--- Edge Case 1: Missing Stream 3 ---`);
  let page = await browser.newPage();
  console.log(`Logging in as demo.patient1...`);
  await page.goto('http://localhost:3000/login', { waitUntil: 'networkidle2' });
  await page.type('input[type="email"]', 'demo.patient1@omnifusion.demo');
  await page.type('input[type="password"]', 'DemoPassword123!');
  await page.click('button[type="submit"]');
  await page.waitForNavigation({ waitUntil: 'networkidle2' });
  await page.goto('http://localhost:3000/patient/assessment/new', { waitUntil: 'networkidle2' });
  
  // Click 'Execute Multimodal Inference' directly without uploading a file
  console.log('Running Inference without uploading CSV...');
  let buttons = await page.$$('button');
  for (const btn of buttons) {
    const text = await page.evaluate(el => el.textContent, btn);
    if (text.includes('Execute Multimodal Inference')) {
      await btn.click();
      break;
    }
  }
  await page.waitForSelector('text/Risk Score:', { timeout: 120000 });
  await new Promise(resolve => setTimeout(resolve, 1000));
  await page.screenshot({ path: '../verification_logs/phase_12_edge_1_missing_stream3.png' });
  await page.close();

  // Edge Case 2: Bad Upload (malformed CSV)
  console.log(`\n--- Edge Case 2: Bad Upload ---`);
  page = await browser.newPage();
  console.log(`Logging in as demo.patient1...`);
  await page.goto('http://localhost:3000/login', { waitUntil: 'networkidle2' });
  await page.type('input[type="email"]', 'demo.patient1@omnifusion.demo');
  await page.type('input[type="password"]', 'DemoPassword123!');
  await page.click('button[type="submit"]');
  await page.waitForNavigation({ waitUntil: 'networkidle2' });
  await page.goto('http://localhost:3000/patient/assessment/new', { waitUntil: 'networkidle2' });
  
  const badUploadPath = path.join(__dirname, 'bad_upload.csv');
  fs.writeFileSync(badUploadPath, '');
  const inputUploadHandle = await page.$('input[type=file]');
  await inputUploadHandle.uploadFile(badUploadPath);
  
  // Should show Upload Failed
  await page.waitForSelector('text/Upload Failed', { timeout: 10000 });
  await page.screenshot({ path: '../verification_logs/phase_12_edge_2_bad_upload.png' });
  await page.close();

  // Edge Case 3: Malformed ECG Payload
  console.log(`\n--- Edge Case 3: Malformed ECG ---`);
  page = await browser.newPage();
  await page.evaluateOnNewDocument(() => {
    const originalFetch = window.fetch;
    window.fetch = async (...args) => {
      const [resource, config] = args;
      if (typeof resource === 'string' && resource.includes('/api/v1/predict') && config?.method === 'POST') {
        const badPayload = {
          patient_id: "edge_case_3",
          ecg: [[0.0]], // Invalid shape
          vitals: {
            anchor_age: 65.0, gender: 1.0, Creatinine: 1.1, Glucose: 100.0,
            Potassium: 4.0, Sodium: 139.0, HR: 82.0, SBP: 135.0,
            DBP: 80.0, RR: 16.0, O2: 98.0
          }
        };
        config.body = JSON.stringify(badPayload);
      }
      return originalFetch(resource, config);
    };
  });
  console.log(`Logging in as demo.patient1...`);
  await page.goto('http://localhost:3000/login', { waitUntil: 'networkidle2' });
  await page.type('input[type="email"]', 'demo.patient1@omnifusion.demo');
  await page.type('input[type="password"]', 'DemoPassword123!');
  await page.click('button[type="submit"]');
  await page.waitForNavigation({ waitUntil: 'networkidle2' });
  await page.goto('http://localhost:3000/patient/assessment/new', { waitUntil: 'networkidle2' });
  
  buttons = await page.$$('button');
  for (const btn of buttons) {
    const text = await page.evaluate(el => el.textContent, btn);
    if (text.includes('Execute Multimodal Inference')) {
      await btn.click();
      break;
    }
  }
  
  // Wait for error banner
  await page.waitForSelector('.bg-red-900\\/30', { timeout: 10000 });
  await page.screenshot({ path: '../verification_logs/phase_12_edge_3_malformed_ecg.png' });
  await page.close();
  
  // Edge Case 4: Supabase Failure
  console.log(`\n--- Edge Case 4: Supabase Failure ---`);
  page = await browser.newPage();
  await page.evaluateOnNewDocument(() => {
    const originalFetch = window.fetch;
    window.fetch = async (...args) => {
      const [resource, config] = args;
      if (typeof resource === 'string' && resource.includes('/api/v1/predict') && config?.method === 'POST') {
        return new Response(JSON.stringify({ detail: "Database connection failed" }), {
          status: 500,
          headers: { 'Content-Type': 'application/json' }
        });
      }
      return originalFetch(resource, config);
    };
  });
  console.log(`Logging in as demo.patient1...`);
  await page.goto('http://localhost:3000/login', { waitUntil: 'networkidle2' });
  await page.type('input[type="email"]', 'demo.patient1@omnifusion.demo');
  await page.type('input[type="password"]', 'DemoPassword123!');
  await page.click('button[type="submit"]');
  await page.waitForNavigation({ waitUntil: 'networkidle2' });
  await page.goto('http://localhost:3000/patient/assessment/new', { waitUntil: 'networkidle2' });
  buttons = await page.$$('button');
  for (const btn of buttons) {
    const text = await page.evaluate(el => el.textContent, btn);
    if (text.includes('Execute Multimodal Inference')) {
      await btn.click();
      break;
    }
  }
  await page.waitForSelector('.bg-red-900\\/30', { timeout: 10000 });
  await page.screenshot({ path: '../verification_logs/phase_12_edge_4_supabase_failure.png' });
  await page.close();

  await browser.close();
  console.log('Edge cases test complete!');
})();
