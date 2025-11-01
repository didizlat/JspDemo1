import { test } from '@playwright/test';
import { monitorConsoleErrors } from './helpers/console';

const WORKFLOW_START_PATH = process.env.WORKFLOW_START_PATH; // e.g. /checkout or /dashboard

test.describe('Workflow - basic click-through', () => {
	test.beforeAll(() => {
		if (!WORKFLOW_START_PATH) test.skip(true, 'Set WORKFLOW_START_PATH to run workflow tests');
	});

	test('navigate and click primary actions', async ({ page, baseURL }) => {
		if (!WORKFLOW_START_PATH) test.skip();
		const { stop } = monitorConsoleErrors(page);

		await page.goto(WORKFLOW_START_PATH.startsWith('http') ? WORKFLOW_START_PATH : `${baseURL ?? ''}${WORKFLOW_START_PATH}`);

		// Click first visible primary button/link if present
		const primary = page.locator('button:visible, a.button:visible, a[role="button"]:visible').first();
		if (await primary.count()) {
			await primary.click();
			await page.waitForLoadState('networkidle').catch(() => {});
		}

		// Click next step if present
		const next = page.getByRole('button', { name: /next|continue|proceed|confirm/i }).first();
		if (await next.count()) {
			await next.click();
			await page.waitForLoadState('networkidle').catch(() => {});
		}

		await stop();
	});
});


