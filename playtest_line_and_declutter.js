const { chromium } = require('playwright');

(async () => {
  console.log('Starting Playwright automated playtest...');
  const browser = await chromium.launch({ headless: true, channel: 'msedge' });
  const context = await browser.newContext({
    viewport: { width: 1440, height: 900 },
  });

  await context.addInitScript(() => {
    localStorage.setItem('access_token', 'demo-token');
    localStorage.setItem('auth_user', JSON.stringify({
      id: 'demo_user_1',
      full_name: '大專防詐測試員',
      email: 'student@ntu.edu.tw',
      cash: 12500,
      xp: 650,
      level: 2,
      streak_days: 3,
    }));
  });

  const page = await context.newPage();

  // 0. Capture Decluttered Home Page
  console.log('0. Navigating to Home / ...');
  await page.goto('http://localhost:5173/');
  await page.waitForTimeout(2000);
  await page.screenshot({
    path: 'C:/Users/kun/.gemini/antigravity/brain/00d70c0b-91a7-4cf1-a6b8-3c185bf46f39/home_decluttered_clean_live.png',
  });
  console.log('Saved home_decluttered_clean_live.png');

  // 1. Check /quick/quiz Question 2 text rendering and lack of devtools
  console.log('1. Navigating to /quick/quiz...');
  await page.goto('http://localhost:5173/quick/quiz');
  await page.waitForTimeout(1500);

  // Answer question 1 to reach question 2
  const scamBtn = await page.$('button:has-text("這是詐騙"), button:has-text("詐騙")');
  if (scamBtn) {
    console.log('Answering Q1...');
    await scamBtn.click();
    await page.waitForTimeout(600);
    const nextBtn = await page.$('button:has-text("下一題")');
    if (nextBtn) {
      await nextBtn.click();
      await page.waitForTimeout(1000);
    }
  }

  // Question 2: check option texts
  const optionLabels = await page.$$('label');
  console.log('Q2 Option Labels count:', optionLabels.length);
  for (let i = 0; i < optionLabels.length; i++) {
    const txt = await optionLabels[i].textContent();
    console.log(`  Option ${i}: ${txt.trim()}`);
  }

  // Check if TanStack devtools is gone
  const devtoolsBtn = await page.$('button[aria-label="Open TanStack Router Devtools"]');
  console.log('TanStack Devtools present?', !!devtoolsBtn);

  await page.screenshot({
    path: 'C:/Users/kun/.gemini/antigravity/brain/00d70c0b-91a7-4cf1-a6b8-3c185bf46f39/quiz_q2_decluttered_live.png',
  });
  console.log('Saved quiz_q2_decluttered_live.png');

  // 2. Check /scenarios
  console.log('2. Navigating to /scenarios...');
  await page.goto('http://localhost:5173/scenarios');
  await page.waitForTimeout(1200);

  // Click on first scenario card or navigate to scenario chat
  const scenarioItem = await page.$('div[role="button"], li');
  if (scenarioItem) {
    await scenarioItem.click();
    await page.waitForTimeout(1500);
  } else {
    await page.goto('http://localhost:5173/scenarios/sc_01');
    await page.waitForTimeout(1500);
  }

  console.log('Current URL:', page.url());
  // Verify clean chat (no huge yellow cialdini boxes)
  const yellowSpoilers = await page.$$('text=席爾迪尼說服透視鏡');
  console.log('Inline Cialdini Spoilers count in chat:', yellowSpoilers.length);

  await page.screenshot({
    path: 'C:/Users/kun/.gemini/antigravity/brain/00d70c0b-91a7-4cf1-a6b8-3c185bf46f39/scenario_clean_chat_live.png',
  });
  console.log('Saved scenario_clean_chat_live.png');

  // Test judging to verify forensic analysis appears post-game (把分析給我們)
  const judgeBtn = await page.$('[data-testid="judge-button"], button:has-text("下判斷")');
  if (judgeBtn) {
    console.log('Clicking judge button...');
    await judgeBtn.click();
    await page.waitForTimeout(800);
    const reportActionBtn = await page.$('button:has-text("這是詐騙"), button:has-text("檢舉")');
    if (reportActionBtn) {
      await reportActionBtn.click();
      await page.waitForTimeout(1500);
      await page.screenshot({
        path: 'C:/Users/kun/.gemini/antigravity/brain/00d70c0b-91a7-4cf1-a6b8-3c185bf46f39/scenario_verdict_analysis_live.png',
      });
      console.log('Saved scenario_verdict_analysis_live.png');
    }
  }

  // 3. Check /line-channel (LINE 官方頻道實境對話)
  console.log('3. Navigating to /line-channel...');
  await page.goto('http://localhost:5173/line-channel');
  await page.waitForTimeout(2000);

  // Click quick reply or flex button to start invest scenario
  const investBtn = await page.waitForSelector('button:has-text("投資"):not([disabled])', { timeout: 8000 }).catch(() => null);
  if (investBtn) {
    console.log('Clicking Invest Scenario button...');
    await investBtn.click();
    await page.waitForTimeout(2500);
  }

  await page.screenshot({
    path: 'C:/Users/kun/.gemini/antigravity/brain/00d70c0b-91a7-4cf1-a6b8-3c185bf46f39/line_official_channel_live.png',
  });
  console.log('Saved line_official_channel_live.png');

  await browser.close();
  console.log('Playtest completed successfully!');
})();
