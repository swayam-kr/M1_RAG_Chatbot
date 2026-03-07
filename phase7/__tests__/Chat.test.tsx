import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import Home from '../app/page';

// Mock global fetch
global.fetch = jest.fn() as jest.Mock;

// jsdom doesn't implement scrollIntoView
window.HTMLElement.prototype.scrollIntoView = jest.fn();

describe('Groww MF Assistant Chat Interface', () => {
    beforeEach(() => {
        (global.fetch as jest.Mock).mockClear();
        // Default mock for status check on mount
        (global.fetch as jest.Mock).mockResolvedValue({
            ok: true,
            json: async () => ({ status: 'online', last_refreshed: '07 Mar 2026, 02:00 AM' })
        });
    });

    it('renders the AMC empty state dashboard initially', () => {
        render(<Home />);
        expect(screen.getAllByText('Groww PureFact')[0]).toBeInTheDocument();
        expect(screen.getByText('Ask facts about Groww Mutual Fund AMC')).toBeInTheDocument();
    });

    it('handles typing and submission properly', async () => {
        // First call: status check. Second: actual chat.
        (global.fetch as jest.Mock)
            .mockResolvedValueOnce({ ok: true, json: async () => ({ status: 'online', last_refreshed: '' }) })
            .mockResolvedValueOnce({
                ok: true,
                json: async () => ({
                    status: 'allowed',
                    answer: 'Anupam Tiwari manages the Fund.',
                    sources: ['https://groww.in/mutual-funds/groww-large-cap-fund-direct-growth']
                })
            });

        render(<Home />);

        const input = screen.getByTestId('chat-input');
        const submitBtn = screen.getByTestId('chat-submit');

        fireEvent.change(input, { target: { value: 'Who manages the fund?' } });
        expect(input).toHaveValue('Who manages the fund?');

        fireEvent.click(submitBtn);

        expect(input).toHaveValue('');
        expect(screen.getByText('Who manages the fund?')).toBeInTheDocument();

        expect(submitBtn).toBeDisabled();

        await waitFor(() => {
            expect(screen.getByText('Anupam Tiwari manages the Fund.')).toBeInTheDocument();
        });
    });

    it('enforces the intent guardrail visually', async () => {
        const refusalMessage = "I'm a factual FAQ assistant — I can't give financial advice, compare funds, or factor in personal investment goals. Please ask a specific factual question about a Groww Mutual Fund (e.g. expense ratio, NAV, exit load, fund manager).";

        (global.fetch as jest.Mock)
            .mockResolvedValueOnce({ ok: true, json: async () => ({ status: 'online', last_refreshed: '' }) })
            .mockResolvedValueOnce({
                ok: true,
                json: async () => ({
                    status: 'blocked',
                    message: 'PII or Prohibited Intent Detected',
                    answer: refusalMessage
                })
            });

        render(<Home />);
        const input = screen.getByTestId('chat-input');
        const submitBtn = screen.getByTestId('chat-submit');

        fireEvent.change(input, { target: { value: 'Should I invest my life savings?' } });
        fireEvent.click(submitBtn);

        await waitFor(() => {
            expect(screen.getByText(refusalMessage)).toBeInTheDocument();
        });
    });
});
