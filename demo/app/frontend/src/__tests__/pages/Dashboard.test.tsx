import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import Dashboard from '../../pages/Dashboard';

// Mock recharts to avoid rendering issues in jsdom
vi.mock('recharts', () => ({
  ResponsiveContainer: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="responsive-container">{children}</div>
  ),
  AreaChart: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="area-chart">{children}</div>
  ),
  Area: () => <div />,
  XAxis: () => <div />,
  YAxis: () => <div />,
  CartesianGrid: () => <div />,
  Tooltip: () => <div />,
  Legend: () => <div />,
}));

// Mock the API to return empty data
vi.mock('../../services/api', () => ({
  api: {
    getThroughput: vi.fn().mockRejectedValue(new Error('no server')),
    getLatency: vi.fn().mockRejectedValue(new Error('no server')),
    getEventsLatest: vi.fn().mockRejectedValue(new Error('no server')),
    getDiagnostic: vi.fn().mockRejectedValue(new Error('no server')),
  },
}));

describe('Dashboard page', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders throughput chart, latency panel, and event stream sections', () => {
    render(
      <MemoryRouter>
        <Dashboard />
      </MemoryRouter>,
    );

    // Page title
    expect(screen.getByText('Dashboard')).toBeInTheDocument();

    // Big number cards
    expect(screen.getByText('Active tags')).toBeInTheDocument();
    expect(screen.getByText('SDT compression ratio')).toBeInTheDocument();

    // Throughput chart section
    expect(
      screen.getByText('Throughput (events/sec)'),
    ).toBeInTheDocument();

    // Event stream section
    expect(screen.getByText('Live event stream')).toBeInTheDocument();
  });
});
