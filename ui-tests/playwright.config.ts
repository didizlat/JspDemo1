import { defineConfig, devices } from '@playwright/test';

const baseUrl = process.env.BASE_URL || 'http://localhost:8080';

export default defineConfig({
	testDir: 'tests',
	fullyParallel: true,
	retries: 0,
	workers: undefined,
	reporter: [
		['list'],
		['html', { open: 'never' }],
	],
	use: {
		baseURL: baseUrl,
		trace: 'on-first-retry',
		screenshot: 'only-on-failure',
		video: 'retain-on-failure',
		headless: true,
		timeout: 30_000,
	},
	projects: [
		{
			name: 'Chromium',
			use: { ...devices['Desktop Chrome'] },
		},
		{
			name: 'Firefox',
			use: { ...devices['Desktop Firefox'] },
		},
		{
			name: 'WebKit',
			use: { ...devices['Desktop Safari'] },
		},
	],
});


