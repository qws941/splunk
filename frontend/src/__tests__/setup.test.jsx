import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';

describe('vitest setup', () => {
  it('renders a React element', () => {
    render(<h1>Security Dashboard</h1>);
    expect(screen.getByText('Security Dashboard')).toBeInTheDocument();
  });
});
