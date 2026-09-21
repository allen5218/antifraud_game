const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: true, channel: 'msedge' });
  const context = await browser.newContext({
    viewport: { width: 1280, height: 800 }
  });
  await context.addInitScript(() => {
    localStorage.setItem('access_token', 'demo-token');
  });
  const page = await context.newPage();
  await page.goto('http://localhost:5173/quick/quiz');
  await page.waitForTimeout(1500);
  console.log('Current URL:', page.url());

  // First question is verdict question
  // Click scam or safe button
  const scamBtn = await page.$('button:has-text("詐騙")');
  if (scamBtn) {
    console.log('Clicking scam button...');
    await scamBtn.click();
    await page.waitForTimeout(500);
    // Click next button
    const nextBtn = await page.$('button:has-text("下一題")');
    if (nextBtn) {
      console.log('Clicking next button...');
      await nextBtn.click();
      await page.waitForTimeout(1000);
    }
  }

  // Now we should be on question 2
  console.log('Question 2 title:', await page.textContent('h2'));
  const labels = await page.$$('label');
  console.log('Found labels count:', labels.length);
  for (let i = 0; i < labels.length; i++) {
    const text = await labels[i].textContent();
    console.log(`Label ${i}: text="${text.trim()}"`);
  }

  await page.screenshot({ path: 'C:/Users/kun/.gemini/antigravity/scratch/antifraud_game/quiz_q2_debug.png' });
  console.log('Screenshot saved to quiz_q2_debug.png');

  await browser.close();
})();
