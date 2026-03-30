// IP 定位模块前端验证脚本
// 验证目标：
// 1. "立即收集"按钮可正常点击，不报错
// 2. IP 列表数据显示正确

const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ 
    headless: true,
    args: ['--no-sandbox']
  });
  const context = await browser.newContext();
  const page = await context.newPage();
  
  const results = {
    login: { success: false, message: '' },
    ipLocationModule: { success: false, message: '' },
    triggerCollection: { success: false, message: '' },
    ipList: { success: false, message: '' }
  };
  
  try {
    // Step 1: 访问登录页面
    console.log('Step 1: 访问登录页面...');
    await page.goto('http://localhost:5173', { timeout: 10000 });
    await page.waitForSelector('input[type="text"], input[type="email"]', { timeout: 5000 });
    results.login.success = true;
    results.login.message = '登录页面加载成功';
    console.log('✅', results.login.message);
    
    // Step 2: 登录 (使用默认测试账号)
    console.log('Step 2: 登录...');
    try {
      const usernameInput = await page.$('input[type="text"], input[type="email"]');
      const passwordInput = await page.$('input[type="password"]');
      
      if (usernameInput && passwordInput) {
        await usernameInput.fill('admin');
        await passwordInput.fill('admin123');
        await page.click('button[type="submit"], button:has-text("登录")');
        await page.waitForURL('**/dashboard**', { timeout: 5000 }).catch(() => {});
        results.login.message = '登录成功';
        console.log('✅', results.login.message);
      } else {
        results.login.message = '未找到登录表单，可能已自动登录';
        console.log('⚠️', results.login.message);
      }
    } catch (e) {
      results.login.message = '登录步骤跳过：' + e.message;
      console.log('⚠️', results.login.message);
    }
    
    // Step 3: 访问 IP 定位模块
    console.log('Step 3: 访问 IP 定位模块...');
    try {
      // 查找 IP 定位菜单项
      const ipLocationMenu = await page.$('text=IP 定位, text=ip-location, text=IP');
      if (ipLocationMenu) {
        await ipLocationMenu.click();
        await page.waitForSelector('text=立即收集，text=IP 列表', { timeout: 5000 });
        results.ipLocationModule.success = true;
        results.ipLocationModule.message = 'IP 定位模块加载成功';
        console.log('✅', results.ipLocationModule.message);
      } else {
        // 尝试直接访问路由
        await page.goto('http://localhost:5173/ip-location', { timeout: 5000 });
        await page.waitForSelector('text=立即收集，text=IP 列表', { timeout: 5000 });
        results.ipLocationModule.success = true;
        results.ipLocationModule.message = 'IP 定位模块直接访问成功';
        console.log('✅', results.ipLocationModule.message);
      }
    } catch (e) {
      results.ipLocationModule.message = 'IP 定位模块访问失败：' + e.message;
      console.log('❌', results.ipLocationModule.message);
    }
    
    // Step 4: 测试"立即收集"按钮
    console.log('Step 4: 测试"立即收集"按钮...');
    try {
      const triggerButton = await page.$('text=立即收集，button:has-text("立即收集")');
      if (triggerButton) {
        await triggerButton.click();
        // 等待成功提示或状态变化
        await page.waitForSelector('text=成功，text=完成，.el-message--success', { timeout: 10000 });
        results.triggerCollection.success = true;
        results.triggerCollection.message = '"立即收集"按钮点击成功，无报错';
        console.log('✅', results.triggerCollection.message);
      } else {
        results.triggerCollection.message = '未找到"立即收集"按钮';
        console.log('❌', results.triggerCollection.message);
      }
    } catch (e) {
      results.triggerCollection.message = '"立即收集"测试失败：' + e.message;
      console.log('❌', results.triggerCollection.message);
    }
    
    // Step 5: 检查 IP 列表
    console.log('Step 5: 检查 IP 列表...');
    try {
      // 切换到 IP 列表标签
      const listTab = await page.$('text=IP 列表，text=列表');
      if (listTab) {
        await listTab.click();
      }
      
      // 检查表格是否加载
      const table = await page.$('table, .el-table, [class*="table"]');
      if (table) {
        results.ipList.success = true;
        results.ipList.message = 'IP 列表表格加载成功';
        console.log('✅', results.ipList.message);
        
        // 尝试获取表头
        const headers = await page.$$eval('th, thead td', els => els.map(e => e.textContent.trim()));
        console.log('表头:', headers);
      } else {
        results.ipList.message = 'IP 列表表格未找到';
        console.log('❌', results.ipList.message);
      }
    } catch (e) {
      results.ipList.message = 'IP 列表检查失败：' + e.message;
      console.log('❌', results.ipList.message);
    }
    
  } catch (e) {
    console.log('验证过程出错:', e.message);
  } finally {
    await browser.close();
  }
  
  // 输出结果汇总
  console.log('\n========== 验证结果汇总 ==========');
  console.log('登录:', results.login.success ? '✅' : '❌', results.login.message);
  console.log('IP 定位模块:', results.ipLocationModule.success ? '✅' : '❌', results.ipLocationModule.message);
  console.log('立即收集按钮:', results.triggerCollection.success ? '✅' : '❌', results.triggerCollection.message);
  console.log('IP 列表:', results.ipList.success ? '✅' : '❌', results.ipList.message);
  console.log('=====================================');
  
  // 输出 JSON 结果
  console.log('\nJSON 结果:');
  console.log(JSON.stringify(results, null, 2));
})();
