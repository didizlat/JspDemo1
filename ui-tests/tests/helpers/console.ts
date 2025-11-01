import { expect, Page } from '@playwright/test';

export function monitorConsoleErrors(page: Page) {
	const errors: string[] = [];
	const handler = (msg: any) => {
		if (msg?.type?.() === 'error') {
			errors.push(msg.text());
		}
	};
	page.on('console', handler);
	return {
		stop: async () => {
			page.off('console', handler);
			if (errors.length > 0) {
				// Include consolidated error output for easier debugging
				expect(errors.join('\n')).toBe('');
			}
		},
	};
}


