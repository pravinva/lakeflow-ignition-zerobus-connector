import { describe, it, expect } from 'vitest';
import { render } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import App from '../App';

describe('Theme', () => {
  it('applies dark theme CSS classes to root element', () => {
    const { container } = render(
      <MemoryRouter>
        <App />
      </MemoryRouter>,
    );

    const root = container.firstElementChild as HTMLElement;
    expect(root.className).toMatch(/bg-gray-9[05]0/);
    expect(root.className).toMatch(/text-gray-1[05]0/);
  });
});
