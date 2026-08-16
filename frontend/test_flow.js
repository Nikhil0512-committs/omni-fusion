const puppeteer = require('puppeteer');
const fs = require('fs');

(async () => {
  // Create a dummy CSV file to upload
  fs.writeFileSync('dummy.csv', 'anchor_age,gender,Creatinine,Glucose,Potassium,Sodium,HR,SBP,DBP,RR,O2\n65,1,1.1,100,4.0,139,82,135,80,16,98\n');

  const browser = await puppeteer.launch({ headless: 'new' });
  const page = await browser.newPage();
  
  // Set a standard desktop viewport
  await page.setViewport({ width: 1280, height: 1024 });

  console.log('Navigating to http://localhost:3000...');
  await page.goto('http://localhost:3000', { waitUntil: 'networkidle2' });

  console.log('Uploading CSV...');
  const inputUploadHandle = await page.$('input[type=file]');
  await inputUploadHandle.uploadFile('dummy.csv');

  // Wait for the upload success message
  await page.waitForSelector('text/Upload Complete', { timeout: 10000 });
  console.log('Upload complete.');

  console.log('Running Inference...');
  // Find the button with text "Execute Multimodal Inference" and click it
  const buttons = await page.$$('button');
  for (const btn of buttons) {
    const text = await page.evaluate(el => el.textContent, btn);
    if (text.includes('Execute Multimodal Inference')) {
      await btn.click();
      break;
    }
  }

  // Wait for the results to render. 
  // We can wait for "Risk Score:" to appear
  console.log('Waiting for results...');
  await page.waitForSelector('text/Risk Score:', { timeout: 30000 });

  // Give charts a moment to animate
  await new Promise(resolve => setTimeout(resolve, 2000));

  console.log('Taking screenshot of Dashboard...');
  await page.screenshot({ path: '../verification_logs/phase_11_dashboard.png', fullPage: true });

  console.log('Navigating to History view...');
  await page.goto('http://localhost:3000/history', { waitUntil: 'networkidle2' });
  
  // Wait for table to load
  await page.waitForSelector('table', { timeout: 10000 });
  await new Promise(resolve => setTimeout(resolve, 1000));

  console.log('Taking screenshot of History...');
  await page.screenshot({ path: '../verification_logs/phase_11_history.png', fullPage: true });

  await browser.close();
  console.log('Done!');
})();
