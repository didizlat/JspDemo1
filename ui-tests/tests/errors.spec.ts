import { test, expect } from '@playwright/test';
import { monitorConsoleErrors } from './helpers/console';

const ERROR_PAGE_PATH = process.env.ERROR_PAGE_PATH; // e.g. /login or /signup

test.describe('Error validation on forms', () => {
	test.beforeAll(() => {
		if (!ERROR_PAGE_PATH) test.skip(true, 'Set ERROR_PAGE_PATH to run error validation tests');
	});

	test('shows validation errors on empty submit', async ({ page, baseURL }) => {
		if (!ERROR_PAGE_PATH) test.skip();
		const { stop } = monitorConsoleErrors(page);

		await page.goto(ERROR_PAGE_PATH.startsWith('http') ? ERROR_PAGE_PATH : `${baseURL ?? ''}${ERROR_PAGE_PATH}`);
		await page.waitForLoadState('domcontentloaded');

		const submit = page.locator('button[type="submit"], input[type="submit"], button:has-text("Submit"), button:has-text("Sign in"), button:has-text("Register")').first();
		if (!(await submit.count())) {
			test.skip('No submit control found');
		}

		await submit.click();
		await page.waitForTimeout(300);

		// Look for common validation indicators
		const candidates = [
			'[aria-invalid="true"]',
			'.error, .errors, .validation-error, .invalid-feedback',
			'role=alert',
		];
		let found = false;
		for (const sel of candidates) {
			const loc = sel.startsWith('role=') ? page.getByRole('alert') : page.locator(sel);
			if (await loc.count()) {
				found = true;
				break;
			}
		}

		if (!found) {
			// Heuristic: look for text content indicating validation
			const errorText = page.locator('text=/required|invalid|please|error/i');
			await expect(errorText).toBeVisible();
		}

		await stop();
	});
});


