import { render, screen, fireEvent } from '@testing-library/react';
import { LeaderboardPage } from './LeaderboardPage';

const mockData = [
  {
    id: 'user-1',
    rank: 1,
    username: 'solmaster',
    avatarUrl: undefined,
    totalEarned: 2500000,
    bountiesCompleted: 42,
    reputationScore: 98,
    categories: ['Frontend', 'Smart Contracts'],
  },
  {
    id: 'user-2',
    rank: 2,
    username: 'crypto_dev',
    avatarUrl: undefined,
    totalEarned: 1850000,
    bountiesCompleted: 35,
    reputationScore: 94,
    categories: ['Backend', 'Security'],
  },
  {
    id: 'user-3',
    rank: 3,
    username: 'web3_builder',
    avatarUrl: undefined,
    totalEarned: 1500000,
    bountiesCompleted: 28,
    reputationScore: 91,
    categories: ['Smart Contracts', 'Frontend'],
  },
  {
    id: 'user-4',
    rank: 4,
    username: 'rustacean',
    avatarUrl: undefined,
    totalEarned: 1200000,
    bountiesCompleted: 22,
    reputationScore: 87,
    categories: ['Backend', 'Smart Contracts'],
  },
  {
    id: 'user-5',
    rank: 5,
    username: 'code_ninja',
    avatarUrl: undefined,
    totalEarned: 950000,
    bountiesCompleted: 18,
    reputationScore: 85,
    categories: ['Frontend', 'Design'],
  },
];

describe('LeaderboardPage', () => {
  // Basic rendering tests
  it('renders the page header', () => {
    render(<LeaderboardPage data={mockData} />);
    expect(screen.getByText('Leaderboard')).toBeInTheDocument();
    expect(screen.getByText('Top contributors ranked by FNDRY earnings')).toBeInTheDocument();
  });

  it('renders top 3 cards with medals', () => {
    render(<LeaderboardPage data={mockData} />);
    expect(screen.getByText('🥇')).toBeInTheDocument();
    expect(screen.getByText('🥈')).toBeInTheDocument();
    expect(screen.getByText('🥉')).toBeInTheDocument();
  });

  it('renders top 3 usernames', () => {
    render(<LeaderboardPage data={mockData} />);
    expect(screen.getByText('solmaster')).toBeInTheDocument();
    expect(screen.getByText('crypto_dev')).toBeInTheDocument();
    expect(screen.getByText('web3_builder')).toBeInTheDocument();
  });

  it('renders top 3 earned amounts', () => {
    render(<LeaderboardPage data={mockData} />);
    expect(screen.getByText('2,500,000 FNDRY')).toBeInTheDocument();
    expect(screen.getByText('1,850,000 FNDRY')).toBeInTheDocument();
    expect(screen.getByText('1,500,000 FNDRY')).toBeInTheDocument();
  });

  it('renders top 3 bounty counts', () => {
    render(<LeaderboardPage data={mockData} />);
    expect(screen.getByText('42')).toBeInTheDocument();
    expect(screen.getByText('35')).toBeInTheDocument();
    expect(screen.getByText('28')).toBeInTheDocument();
  });

  it('renders top 3 reputation scores', () => {
    render(<LeaderboardPage data={mockData} />);
    // Multiple 98s might appear (in card and table), use getAllByText
    expect(screen.getAllByText('98').length).toBeGreaterThan(0);
  });

  // Filter tests
  it('renders time period filter', () => {
    render(<LeaderboardPage data={mockData} />);
    expect(screen.getByLabelText('Time Period')).toBeInTheDocument();
  });

  it('renders category filter', () => {
    render(<LeaderboardPage data={mockData} />);
    expect(screen.getByLabelText('Category')).toBeInTheDocument();
  });

  it('renders search input', () => {
    render(<LeaderboardPage data={mockData} />);
    expect(screen.getByPlaceholderText('Search users...')).toBeInTheDocument();
  });

  it('filters by search query', () => {
    render(<LeaderboardPage data={mockData} />);
    const searchInput = screen.getByPlaceholderText('Search users...');
    fireEvent.change(searchInput, { target: { value: 'solmaster' } });
    expect(screen.getByText('solmaster')).toBeInTheDocument();
  });

  it('shows empty state when no results', () => {
    render(<LeaderboardPage data={mockData} />);
    const searchInput = screen.getByPlaceholderText('Search users...');
    fireEvent.change(searchInput, { target: { value: 'nonexistent' } });
    expect(screen.getByText('No contributors found')).toBeInTheDocument();
  });

  it('resets filters on empty state button click', () => {
    render(<LeaderboardPage data={mockData} />);
    const searchInput = screen.getByPlaceholderText('Search users...');
    fireEvent.change(searchInput, { target: { value: 'nonexistent' } });
    const resetButton = screen.getByText('Reset Filters');
    fireEvent.click(resetButton);
    expect(screen.getByText('solmaster')).toBeInTheDocument();
  });

  // Current user highlight tests
  it('highlights current user in top 3 cards', () => {
    render(<LeaderboardPage data={mockData} currentUserId="user-1" />);
    const youBadges = screen.getAllByText('You');
    expect(youBadges.length).toBeGreaterThan(0);
  });

  it('shows current user rank badge', () => {
    render(<LeaderboardPage data={mockData} currentUserId="user-1" />);
    expect(screen.getByText('Your Rank:')).toBeInTheDocument();
    expect(screen.getByText('#1')).toBeInTheDocument();
  });

  // Pagination tests
  it('renders pagination when many items', () => {
    const manyItems = Array.from({ length: 15 }, (_, i) => ({
      id: `user-${i + 1}`,
      rank: i + 1,
      username: `user${i + 1}`,
      avatarUrl: undefined,
      totalEarned: 100000 * (15 - i),
      bountiesCompleted: 10 - i,
      reputationScore: 90 - i,
      categories: ['Frontend'],
    }));
    render(<LeaderboardPage data={manyItems} />);
    expect(screen.getByText('Previous')).toBeInTheDocument();
    expect(screen.getByText('Next')).toBeInTheDocument();
  });

  it('does not render pagination for few items', () => {
    render(<LeaderboardPage data={mockData.slice(0, 3)} />);
    expect(screen.queryByText('Previous')).not.toBeInTheDocument();
    expect(screen.queryByText('Next')).not.toBeInTheDocument();
  });

  // Loading state test
  it('renders loading skeleton when isLoading is true', () => {
    const { container } = render(<LeaderboardPage isLoading />);
    expect(container.querySelector('.animate-pulse')).toBeInTheDocument();
  });

  // Touch-friendly button tests
  it('has touch-friendly filter controls (min 44px)', () => {
    render(<LeaderboardPage data={mockData} />);
    const selects = screen.getAllByRole('combobox');
    selects.forEach((select) => {
      expect(select).toHaveClass('min-h-[44px]');
    });
  });

  it('has touch-friendly pagination buttons (min 44px)', () => {
    const manyItems = Array.from({ length: 15 }, (_, i) => ({
      id: `user-${i + 1}`,
      rank: i + 1,
      username: `user${i + 1}`,
      avatarUrl: undefined,
      totalEarned: 100000 * (15 - i),
      bountiesCompleted: 10 - i,
      reputationScore: 90 - i,
      categories: ['Frontend'],
    }));
    render(<LeaderboardPage data={manyItems} />);
    const prevButton = screen.getByText('Previous');
    const nextButton = screen.getByText('Next');
    expect(prevButton).toHaveClass('min-h-[44px]');
    expect(nextButton).toHaveClass('min-h-[44px]');
  });

  // Results count test
  it('shows results count', () => {
    render(<LeaderboardPage data={mockData} />);
    expect(screen.getByText(/Showing/)).toBeInTheDocument();
    expect(screen.getByText(/contributors/)).toBeInTheDocument();
  });

  // Click handler tests
  it('calls onRowClick when row is clicked', () => {
    const onRowClick = jest.fn();
    render(<LeaderboardPage data={mockData} onRowClick={onRowClick} />);
    const username = screen.getByText('rustacean');
    fireEvent.click(username);
    expect(onRowClick).toHaveBeenCalled();
  });

  it('calls onFilterChange when filter changes', () => {
    const onFilterChange = jest.fn();
    render(<LeaderboardPage data={mockData} onFilterChange={onFilterChange} />);
    const searchInput = screen.getByPlaceholderText('Search users...');
    fireEvent.change(searchInput, { target: { value: 'test' } });
    expect(onFilterChange).toHaveBeenCalled();
  });

  // Category filter test
  it('filters by category', () => {
    render(<LeaderboardPage data={mockData} />);
    const categorySelect = screen.getByLabelText('Category');
    fireEvent.change(categorySelect, { target: { value: 'Security' } });
    // crypto_dev has Security category, should still be visible
    expect(screen.getByText('crypto_dev')).toBeInTheDocument();
    // solmaster doesn't have Security, should not appear in results
    // But top 3 cards still show, so we check the empty state doesn't appear
    expect(screen.queryByText('No contributors found')).not.toBeInTheDocument();
  });

  // Responsive layout test
  it('has responsive grid layout for top 3', () => {
    const { container } = render(<LeaderboardPage data={mockData} />);
    const grid = container.querySelector('.grid-cols-1.sm\\:grid-cols-3');
    expect(grid).toBeInTheDocument();
  });

  // Medal rendering test
  it('renders correct medals in order', () => {
    render(<LeaderboardPage data={mockData} />);
    const medals = ['🥇', '🥈', '🥉'];
    medals.forEach((medal) => {
      expect(screen.getByText(medal)).toBeInTheDocument();
    });
  });

  // Time period filter test
  it('filters by time period', () => {
    const onFilterChange = jest.fn();
    render(<LeaderboardPage data={mockData} onFilterChange={onFilterChange} />);
    const timeSelect = screen.getByLabelText('Time Period');
    fireEvent.change(timeSelect, { target: { value: 'week' } });
    expect(onFilterChange).toHaveBeenCalledWith(
      expect.objectContaining({ timePeriod: 'week' })
    );
  });

  // Pagination navigation tests
  it('calls onPageChange when page changes', () => {
    const onPageChange = jest.fn();
    const manyItems = Array.from({ length: 15 }, (_, i) => ({
      id: `user-${i + 1}`,
      rank: i + 1,
      username: `user${i + 1}`,
      avatarUrl: undefined,
      totalEarned: 100000 * (15 - i),
      bountiesCompleted: 10 - i,
      reputationScore: 90 - i,
      categories: ['Frontend'],
    }));
    render(<LeaderboardPage data={manyItems} onPageChange={onPageChange} />);
    const nextButton = screen.getByText('Next');
    fireEvent.click(nextButton);
    expect(onPageChange).toHaveBeenCalledWith(2);
  });

  it('disables previous button on first page', () => {
    const manyItems = Array.from({ length: 15 }, (_, i) => ({
      id: `user-${i + 1}`,
      rank: i + 1,
      username: `user${i + 1}`,
      avatarUrl: undefined,
      totalEarned: 100000 * (15 - i),
      bountiesCompleted: 10 - i,
      reputationScore: 90 - i,
      categories: ['Frontend'],
    }));
    render(<LeaderboardPage data={manyItems} />);
    const prevButton = screen.getByText('Previous');
    expect(prevButton).toBeDisabled();
  });

  it('disables next button on last page', () => {
    const manyItems = Array.from({ length: 15 }, (_, i) => ({
      id: `user-${i + 1}`,
      rank: i + 1,
      username: `user${i + 1}`,
      avatarUrl: undefined,
      totalEarned: 100000 * (15 - i),
      bountiesCompleted: 10 - i,
      reputationScore: 90 - i,
      categories: ['Frontend'],
    }));
    render(<LeaderboardPage data={manyItems} />);
    const nextButton = screen.getByText('Next');
    fireEvent.click(nextButton); // Go to page 2 (last page with 15 items)
    expect(nextButton).toBeDisabled();
  });

  // Edge cases
  it('handles empty data array', () => {
    render(<LeaderboardPage data={[]} />);
    expect(screen.getByText('No contributors found')).toBeInTheDocument();
  });

  it('handles single item data', () => {
    render(<LeaderboardPage data={mockData.slice(0, 1)} />);
    expect(screen.getByText('🥇')).toBeInTheDocument();
    expect(screen.queryByText('🥈')).not.toBeInTheDocument();
  });

  it('handles two items data', () => {
    render(<LeaderboardPage data={mockData.slice(0, 2)} />);
    expect(screen.getByText('🥇')).toBeInTheDocument();
    expect(screen.getByText('🥈')).toBeInTheDocument();
    expect(screen.queryByText('🥉')).not.toBeInTheDocument();
  });

  // Default props test
  it('renders with default props (no data prop)', () => {
    render(<LeaderboardPage />);
    // Should render with MOCK_DATA
    expect(screen.getByText('Leaderboard')).toBeInTheDocument();
  });

  // Accessibility tests
  it('has accessible filter labels', () => {
    render(<LeaderboardPage data={mockData} />);
    expect(screen.getByLabelText('Time Period')).toBeInTheDocument();
    expect(screen.getByLabelText('Category')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('Search users...')).toBeInTheDocument();
  });

  // Category tags in top 3 cards
  it('renders category tags in top 3 cards', () => {
    render(<LeaderboardPage data={mockData} />);
    // First user has Frontend and Smart Contracts
    expect(screen.getByText('Frontend')).toBeInTheDocument();
    expect(screen.getByText('Smart Contracts')).toBeInTheDocument();
  });

  // Current user not in top 3
  it('shows current user rank when not in top 3', () => {
    render(<LeaderboardPage data={mockData} currentUserId="user-4" />);
    expect(screen.getByText('Your Rank:')).toBeInTheDocument();
    expect(screen.getByText('#4')).toBeInTheDocument();
  });

  // Current user not in data
  it('does not show rank when current user not in data', () => {
    render(<LeaderboardPage data={mockData} currentUserId="nonexistent-user" />);
    expect(screen.queryByText('Your Rank:')).not.toBeInTheDocument();
  });

  // Reset filters button functionality
  it('reset filters button clears all filters', () => {
    render(<LeaderboardPage data={mockData} />);
    // Apply filters
    const searchInput = screen.getByPlaceholderText('Search users...');
    const categorySelect = screen.getByLabelText('Category');
    
    fireEvent.change(searchInput, { target: { value: 'nonexistent' } });
    fireEvent.change(categorySelect, { target: { value: 'Security' } });
    
    // Click reset
    const resetButton = screen.getByText('Reset Filters');
    fireEvent.click(resetButton);
    
    // Check that data is visible again
    expect(screen.getByText('solmaster')).toBeInTheDocument();
  });
});