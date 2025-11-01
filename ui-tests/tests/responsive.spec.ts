import { test } from '@playwright/test';
import { monitorConsoleErrors } from './helpers/console';

const PATH = process.env.RESPONSIVE_PATH || '/';

const viewports = [
	{ name: 'Desktop-1280x800', width: 1280, height: 800 },
	{ name: 'Tablet-768x1024', width: 768, height: 1024 },
	{ name: 'Mobile-390x844', width: 390, height: 844 },
];

test.describe('Responsive layouts', () => {
	for (const vp of viewports) {
		test(vp.name, async ({ page, baseURL }) => {
			const { stop } = monitorConsoleErrors(page);
			await page.setViewportSize({ width: vp.width, height: vp.height });
			await page.goto(PATH.startsWith('http') ? PATH : `${baseURL ?? ''}${PATH}`);
			await page.waitForLoadState('domcontentloaded');
			await page.screenshot({ path: `screenshots/${vp.name}.png`, fullPage: true });
			await stop();
		});
	}
});


