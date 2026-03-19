import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { Header } from '../Header';
import { Sidebar } from '../Sidebar';

// Mock ThemeToggle
vi.mock('../ThemeToggle', () => ({
  ThemeToggle: () => <button aria-label="Toggle theme">Theme</button>,
}));

const renderWithRouter = (component: React.ReactNode) => {
  return render(
    <BrowserRouter>
      {component}
    </BrowserRouter>
  );
};

describe('Header', () => {
  const defaultProps = {
    sidebarCollapsed: true,
    onMenuClick: vi.fn(),
    theme: 'light' as const,
    onToggleTheme: vi.fn(),
  };

  it('renders mobile hamburger menu button', () => {
    renderWithRouter(<Header {...defaultProps} />);
    const menuButton = screen.getByRole('button', { name: /open navigation menu/i });
    expect(menuButton).toBeInTheDocument();
  });

  it('hamburger button has proper touch target size on mobile', () => {
    renderWithRouter(<Header {...defaultProps} />);
    const menuButton = screen.getByRole('button', { name: /open navigation menu/i });
    // Should have touch-button class which ensures 44px minimum
    expect(menuButton).toHaveClass('touch-button');
  });

  it('renders search button on mobile', () => {
    renderWithRouter(<Header {...defaultProps} />);
    const searchButton = screen.getByRole('button', { name: /open search/i });
    expect(searchButton).toBeInTheDocument();
  });

  it('renders notification button with proper touch target', () => {
    renderWithRouter(<Header {...defaultProps} />);
    const notificationButton = screen.getByRole('button', { name: /notifications/i });
    expect(notificationButton).toBeInTheDocument();
    expect(notificationButton).toHaveClass('touch-button');
  });

  it('renders user avatar button', () => {
    renderWithRouter(<Header {...defaultProps} />);
    const avatarButton = screen.getByRole('button', { name: /user menu/i });
    expect(avatarButton).toBeInTheDocument();
  });
});

describe('Sidebar', () => {
  const defaultProps = {
    collapsed: true,
    onToggle: vi.fn(),
    mobileOpen: false,
    onMobileClose: vi.fn(),
  };

  it('renders navigation items', () => {
    renderWithRouter(<Sidebar {...defaultProps} />);
    // Check for navigation labels
    expect(screen.getByText('Dashboard')).toBeInTheDocument();
    expect(screen.getByText('Projects')).toBeInTheDocument();
    expect(screen.getByText('Automations')).toBeInTheDocument();
    expect(screen.getByText('Analytics')).toBeInTheDocument();
    expect(screen.getByText('Settings')).toBeInTheDocument();
  });

  it('mobile sidebar is hidden when mobileOpen is false', () => {
    renderWithRouter(<Sidebar {...defaultProps} mobileOpen={false} />);
    const mobileSidebar = screen.getByLabelText('Main navigation');
    // Should have -translate-x-full class when closed
    expect(mobileSidebar).toHaveClass('-translate-x-full');
  });

  it('mobile sidebar is visible when mobileOpen is true', () => {
    renderWithRouter(<Sidebar {...defaultProps} mobileOpen={true} />);
    const mobileSidebars = screen.getAllByLabelText('Main navigation');
    // Mobile sidebar should have translate-x-0 when open
    const mobileSidebar = mobileSidebars.find((el) => el.classList.contains('lg:hidden'));
    expect(mobileSidebar).toHaveClass('translate-x-0');
  });

  it('navigation links have proper touch targets', () => {
    renderWithRouter(<Sidebar {...defaultProps} mobileOpen={true} />);
    const dashboardLink = screen.getByRole('link', { name: /dashboard/i });
    // Should have sidebar-link class which includes min-h-touch (44px)
    expect(dashboardLink).toHaveClass('sidebar-link');
  });
});

describe('Responsive Design', () => {
  it('header buttons meet minimum touch target size (44px)', () => {
    renderWithRouter(
      <Header
        sidebarCollapsed={true}
        onMenuClick={vi.fn()}
        theme="light"
        onToggleTheme={vi.fn()}
      />
    );

    // All touch buttons should have the touch-button class
    const touchButtons = screen.getAllByRole('button').filter((btn) =>
      btn.classList.contains('touch-button')
    );

    // At minimum, hamburger and notification buttons should have touch-button class
    expect(touchButtons.length).toBeGreaterThan(0);
  });

  it('sidebar navigation links have minimum touch target height', () => {
    renderWithRouter(
      <Sidebar
        collapsed={true}
        onToggle={vi.fn()}
        mobileOpen={true}
        onMobileClose={vi.fn()}
      />
    );

    const links = screen.getAllByRole('link');
    links.forEach((link) => {
      expect(link).toHaveClass('sidebar-link');
    });
  });
});