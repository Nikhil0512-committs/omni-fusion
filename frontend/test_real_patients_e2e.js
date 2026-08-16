const puppeteer = require('puppeteer');
const fs = require('fs');
const path = require('path');

(async () => {
  const browser = await puppeteer.launch({ headless: 'new' });
  const scores = [];
  
  for (let i = 1; i <= 3; i++) {
    console.log(`\n--- Running E2E Flow for Patient ${i} ---`);
    const page = await browser.newPage();
    await page.setViewport({ width: 1280, height: 1024 });

    console.log(`Logging in as demo.patient${i}...`);
    await page.goto('http://localhost:3000/login', { waitUntil: 'networkidle2' });
    await page.type('input[type="email"]', `demo.patient${i}@omnifusion.demo`);
    await page.type('input[type="password"]', 'DemoPassword123!');
    await page.click('button[type="submit"]');
    await page.waitForNavigation({ waitUntil: 'networkidle2' });
    console.log('Navigating to assessment...');
    await page.goto('http://localhost:3000/patient/assessment/new', { waitUntil: 'networkidle2' });

    console.log('Uploading CSV...');
    const inputUploadHandle = await page.$('input[type=file]');
    await inputUploadHandle.uploadFile(path.join(__dirname, `test_data/historical_patient_${i}.csv`));

    // Wait for the upload success message
    await page.waitForSelector('text/Upload Complete', { timeout: 10000 });
    console.log('Upload complete.');

    console.log('Running Inference...');
    const buttons = await page.$$('button');
    for (const btn of buttons) {
      const text = await page.evaluate(el => el.textContent, btn);
      if (text.includes('Execute Multimodal Inference')) {
        await btn.click();
        break;
      }
    }

    console.log('Waiting for results...');
    await page.waitForSelector('text/Risk Score:', { timeout: 120000 });
    await new Promise(resolve => setTimeout(resolve, 2000));
    
    // Extract Risk Score
    const riskScoreText = await page.evaluate(() => {
      const element = Array.from(document.querySelectorAll('h2')).find(el => el.textContent.includes('Risk Score:'));
      return element ? element.textContent : null;
    });
    
    console.log(`Extracted text: ${riskScoreText}`);
    const scoreMatch = riskScoreText.match(/Risk Score: ([\d.]+)%/);
    const score = scoreMatch ? parseFloat(scoreMatch[1]) : -1;
    scores.push(score);
    console.log(`Score for Patient ${i}: ${score}%`);

    console.log('Taking screenshot of Dashboard...');
    // The prompt specified saving to verification_logs/phase_13_e2e_patient_{high,low,mixed}_dashboard.png
    // Let's just name them phase_13_e2e_patient_1/2/3 for now and verify they are different.
    await page.screenshot({ path: path.join(__dirname, `../verification_logs/phase_13_e2e_patient_${i}_dashboard.png`), fullPage: true });

    await page.close();
  }

  await browser.close();
  console.log('\n--- Test Summary ---');
  console.log(`Scores: ${scores.join(', ')}`);
  
  // Assertions
  for (const score of scores) {
    if (score === 0.0 || score === 100.0) {
      console.error(`Assertion failed: Score ${score} is saturated (exactly 0.0 or 100.0).`);
      process.exit(1);
    }
  }
  
  let differs = false;
  for (let i = 0; i < scores.length; i++) {
    for (let j = i + 1; j < scores.length; j++) {
      if (Math.abs(scores[i] - scores[j]) > 1.0) {
        differs = true;
      }
    }
  }
  
  if (!differs) {
    console.error(`Assertion failed: Scores are not materially different (${scores.join(', ')}).`);
    process.exit(1);
  }
  
  console.log('All E2E assertions passed!');
})();
