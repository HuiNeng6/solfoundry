import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Route, Routes, useLocation } from 'react-router-dom';
import { BountyTags } from './BountyTags';

function RouterLoc() {
  const { pathname, search } = useLocation();
  return <span data-testid="router-loc">{`${pathname}${search}`}</span>;
}

describe('BountyTags', () => {
  it('renders tier, normalized category label, and skills (static)', () => {
    render(
      <BountyTags
        tier="T2"
        category="smart_contract"
        skills={['TypeScript', 'Rust']}
        interactive={false}
        showTier
      />,
    );
    expect(screen.getByText('T2')).toBeInTheDocument();
    expect(screen.getByText('Smart Contract')).toBeInTheDocument();
    expect(screen.getByText('TypeScript')).toBeInTheDocument();
    expect(screen.getByText('Rust')).toBeInTheDocument();
  });

  it('truncates skills with overflow hint', () => {
    render(
      <BountyTags
        tier="T1"
        skills={['A', 'B', 'C', 'D']}
        interactive={false}
        showTier={false}
        maxSkills={2}
      />,
    );
    expect(screen.getByText('A')).toBeInTheDocument();
    expect(screen.getByText('B')).toBeInTheDocument();
    expect(screen.getByText('+2 more')).toBeInTheDocument();
  });

  it('updates route search when interactive skill is clicked', async () => {
    const user = userEvent.setup();
    render(
      <MemoryRouter initialEntries={['/bounties']}>
        <Routes>
          <Route
            path="/bounties"
            element={
              <>
                <BountyTags tier="T1" skills={['Python']} interactive showTier={false} />
                <RouterLoc />
              </>
            }
          />
        </Routes>
      </MemoryRouter>,
    );

    await user.click(screen.getByRole('button', { name: /Filter bounties by skill: Python/i }));
    expect(screen.getByTestId('router-loc')).toHaveTextContent(/skills=Python/);
  });

  it('toggles tier off when it matches the current URL filter', async () => {
    const user = userEvent.setup();
    render(
      <MemoryRouter initialEntries={['/bounties?tier=T2']}>
        <Routes>
          <Route
            path="/bounties"
            element={
              <>
                <BountyTags tier="T2" skills={[]} interactive showTier />
                <RouterLoc />
              </>
            }
          />
        </Routes>
      </MemoryRouter>,
    );

    await user.click(screen.getByRole('button', { name: /Filter bounties by tier T2/i }));
    expect(screen.getByTestId('router-loc')).toHaveTextContent('/bounties');
  });

  it('updates route search when interactive category is clicked', async () => {
    const user = userEvent.setup();
    render(
      <MemoryRouter initialEntries={['/bounties']}>
        <Routes>
          <Route
            path="/bounties"
            element={
              <>
                <BountyTags tier="T1" category="frontend" skills={[]} interactive showTier={false} />
                <RouterLoc />
              </>
            }
          />
        </Routes>
      </MemoryRouter>,
    );

    await user.click(screen.getByRole('button', { name: /Filter bounties by category: Frontend/i }));
    expect(screen.getByTestId('router-loc')).toHaveTextContent(/category=frontend/);
  });

  it('toggles category off when it matches the current URL filter', async () => {
    const user = userEvent.setup();
    render(
      <MemoryRouter initialEntries={['/bounties?category=backend']}>
        <Routes>
          <Route
            path="/bounties"
            element={
              <>
                <BountyTags tier="T1" category="backend" skills={[]} interactive showTier={false} />
                <RouterLoc />
              </>
            }
          />
        </Routes>
      </MemoryRouter>,
    );

    await user.click(screen.getByRole('button', { name: /Filter bounties by category: Backend/i }));
    expect(screen.getByTestId('router-loc')).toHaveTextContent('/bounties');
  });

  it('hides tier when showTier is false', () => {
    render(
      <BountyTags
        tier="T3"
        skills={[]}
        interactive={false}
        showTier={false}
      />,
    );
    expect(screen.queryByText('T3')).not.toBeInTheDocument();
  });

  it('renders all tier badges with correct colors', () => {
    const { rerender } = render(
      <BountyTags tier="T1" skills={[]} interactive={false} showTier />,
    );
    expect(screen.getByText('T1')).toBeInTheDocument();

    rerender(<BountyTags tier="T2" skills={[]} interactive={false} showTier />);
    expect(screen.getByText('T2')).toBeInTheDocument();

    rerender(<BountyTags tier="T3" skills={[]} interactive={false} showTier />);
    expect(screen.getByText('T3')).toBeInTheDocument();
  });

  it('renders all category labels correctly', () => {
    const categories = [
      { value: 'smart-contract', label: 'Smart Contract' },
      { value: 'frontend', label: 'Frontend' },
      { value: 'backend', label: 'Backend' },
      { value: 'design', label: 'Design' },
      { value: 'content', label: 'Content' },
      { value: 'security', label: 'Security' },
      { value: 'devops', label: 'DevOps' },
      { value: 'documentation', label: 'Documentation' },
    ] as const;

    categories.forEach(({ value, label }) => {
      const { unmount } = render(
        <BountyTags tier="T1" category={value} skills={[]} interactive={false} showTier={false} />,
      );
      expect(screen.getByText(label)).toBeInTheDocument();
      unmount();
    });
  });

  it('supports keyboard interaction for interactive tags', async () => {
    const user = userEvent.setup();
    render(
      <MemoryRouter initialEntries={['/bounties']}>
        <Routes>
          <Route
            path="/bounties"
            element={
              <>
                <BountyTags tier="T1" skills={['React']} interactive showTier={false} />
                <RouterLoc />
              </>
            }
          />
        </Routes>
      </MemoryRouter>,
    );

    const button = screen.getByRole('button', { name: /Filter bounties by skill: React/i });
    button.focus();
    await user.keyboard('{Enter}');
    expect(screen.getByTestId('router-loc')).toHaveTextContent(/skills=React/);
  });

  it('applies custom className', () => {
    render(
      <BountyTags
        tier="T1"
        skills={[]}
        interactive={false}
        className="custom-class"
      />,
    );
    const container = screen.getByTestId('bounty-tags');
    expect(container).toHaveClass('custom-class');
  });

  it('applies custom data-testid', () => {
    render(
      <BountyTags
        tier="T1"
        skills={[]}
        interactive={false}
        data-testid="custom"
      />,
    );
    expect(screen.getByTestId('custom-bounty-tags')).toBeInTheDocument();
  });
});
