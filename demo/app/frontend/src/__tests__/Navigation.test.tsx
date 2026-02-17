import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import App from '../App';

describe('Navigation', () => {
  it('contains all 5 required links', () => {
    render(
      <MemoryRouter>
        <App />
      </MemoryRouter>,
    );

    const expectedLinks = [
      'Dashboard',
      'Assets',
      'Asset Detail',
      'Compression',
      'Architecture',
    ];

    for (const linkText of expectedLinks) {
      expect(screen.getByRole('link', { name: linkText })).toBeInTheDocument();
    }
  });
});
