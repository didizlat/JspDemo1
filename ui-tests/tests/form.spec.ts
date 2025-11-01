import { test, expect } from '@playwright/test';
import { monitorConsoleErrors } from './helpers/console';

const FORM_PATH = process.env.FORM_PATH; // e.g. /login or /account/register

test.describe('Forms - fill and submit with test data', () => {
	test.beforeAll(() => {
		if (!FORM_PATH) test.skip(true, 'Set FORM_PATH env var to run form tests');
	});

	test('fill available fields and submit', async ({ page, baseURL }) => {
		if (!FORM_PATH) test.skip();
		const { stop } = monitorConsoleErrors(page);

		await page.goto(FORM_PATH.startsWith('http') ? FORM_PATH : `${baseURL ?? ''}${FORM_PATH}`);

		// Try to fill common fields if present
		const pairs: Array<{ locator: string; value: string }> = [
			{ locator: 'input[name="username"], input#username, input[name*="user" i]', value: 'testuser' },
			{ locator: 'input[type="email"], input[name="email"], input#email', value: 'testuser@example.com' },
			{ locator: 'input[type="password"], input[name="password"], input#password', value: 'P@ssw0rd123' },
			{ locator: 'input[type="tel"], input[name*="phone" i]', value: '+1 555 0100' },
			{ locator: 'textarea, [contenteditable="true"]', value: 'Test message for automated form submission.' },
		];

		for (const { locator, value } of pairs) {
			const field = page.locator(locator).first();
			if (await field.count()) {
				await field.fill(value);
			}
		}

		// Attempt submit
		const submit = page.locator('button[type="submit"], input[type="submit"], button:has-text("Submit"), button:has-text("Sign in"), button:has-text("Register")').first();
		if (await submit.count()) {
			await Promise.all([
				page.waitForLoadState('load').catch(() => {}),
				submit.click(),
			]);
		}

		await stop();
	});
});


