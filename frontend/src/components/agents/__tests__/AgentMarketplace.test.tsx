import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { AgentCard } from '../AgentCard';
import { AgentFilterComponent } from '../AgentFilter';
import { AgentMarketplace } from '../AgentMarketplace';
import { Agent, AgentFilter } from '../types';

// Mock agent data
const mockAgent: Agent = {
  id: 'test-agent-1',
  name: 'Test Agent',
  description: 'A test agent for unit testing purposes',
  role: 'frontend',
  capabilities: ['React', 'TypeScript', 'Testing'],
  status: 'available',
  tier: 'tier-2',
  stats: {
    bountiesCompleted: 10,
    totalEarned: 5000,
    successRate: 95,
    avgCompletionTime: 12,
    reputationScore: 85,
  },
  walletAddress: 'Amu1YJjcKWKL6xuMTo2dx511kfzXAxgpetJrZp7N71o7',
  hourlyRate: 100,
  tags: ['test', 'frontend'],
  lastActive: new Date().toISOString(),
};

const defaultFilter: AgentFilter = {
  search: '',
  roles: [],
  status: [],
  tiers: [],
  minReputation: 0,
  sortBy: 'reputation',
  sortOrder: 'desc',
};

describe('AgentCard', () => {
  it('renders agent information correctly', () => {
    render(<AgentCard agent={mockAgent} />);
    
    expect(screen.getByText('Test Agent')).toBeInTheDocument();
    expect(screen.getByText('Frontend')).toBeInTheDocument();
    expect(screen.getByText('A test agent for unit testing purposes')).toBeInTheDocument();
  });

  it('displays correct status indicator', () => {
    const { rerender } = render(<AgentCard agent={mockAgent} />);
    expect(screen.getByRole('button', { name: /hire agent/i })).toBeEnabled();
    
    rerender(<AgentCard agent={{ ...mockAgent, status: 'busy' }} />);
    expect(screen.getByRole('button', { name: /unavailable/i })).toBeDisabled();
  });

  it('calls onHire when hire button is clicked', () => {
    const onHire = jest.fn();
    render(<AgentCard agent={mockAgent} onHire={onHire} />);
    
    fireEvent.click(screen.getByRole('button', { name: /hire agent/i }));
    expect(onHire).toHaveBeenCalledWith('test-agent-1');
  });

  it('calls onViewProfile when view profile button is clicked', () => {
    const onViewProfile = jest.fn();
    render(<AgentCard agent={mockAgent} onViewProfile={onViewProfile} />);
    
    fireEvent.click(screen.getByRole('button', { name: /view profile/i }));
    expect(onViewProfile).toHaveBeenCalledWith('test-agent-1');
  });

  it('truncates wallet address correctly', () => {
    render(<AgentCard agent={mockAgent} />);
    expect(screen.getByText('Amu1YJ...1o7')).toBeInTheDocument();
  });

  it('displays capabilities with overflow indicator', () => {
    const agentWithManyCapabilities = {
      ...mockAgent,
      capabilities: ['React', 'TypeScript', 'Testing', 'Jest', 'Cypress'],
    };
    
    render(<AgentCard agent={agentWithManyCapabilities} />);
    expect(screen.getByText('+2')).toBeInTheDocument();
  });
});

describe('AgentFilterComponent', () => {
  it('renders all filter controls', () => {
    const onFilterChange = jest.fn();
    render(
      <AgentFilterComponent
        filter={defaultFilter}
        onFilterChange={onFilterChange}
        totalAgents={100}
        filteredCount={50}
      />
    );
    
    expect(screen.getByPlaceholderText(/search agents/i)).toBeInTheDocument();
    expect(screen.getByText('Role')).toBeInTheDocument();
    expect(screen.getByText('Status')).toBeInTheDocument();
  });

  it('updates search filter on input', () => {
    const onFilterChange = jest.fn();
    render(
      <AgentFilterComponent
        filter={defaultFilter}
        onFilterChange={onFilterChange}
        totalAgents={100}
        filteredCount={50}
      />
    );
    
    fireEvent.change(screen.getByPlaceholderText(/search agents/i), {
      target: { value: 'React' },
    });
    
    expect(onFilterChange).toHaveBeenCalledWith({ search: 'React' });
  });

  it('toggles role filter buttons', () => {
    const onFilterChange = jest.fn();
    render(
      <AgentFilterComponent
        filter={defaultFilter}
        onFilterChange={onFilterChange}
        totalAgents={100}
        filteredCount={50}
      />
    );
    
    fireEvent.click(screen.getByRole('button', { name: /frontend/i }));
    expect(onFilterChange).toHaveBeenCalledWith({ roles: ['frontend'] });
  });

  it('displays correct agent counts', () => {
    const onFilterChange = jest.fn();
    render(
      <AgentFilterComponent
        filter={defaultFilter}
        onFilterChange={onFilterChange}
        totalAgents={100}
        filteredCount={25}
      />
    );
    
    expect(screen.getByText('Showing 25 of 100 agents')).toBeInTheDocument();
  });
});

describe('AgentMarketplace', () => {
  it('renders marketplace header', () => {
    render(<AgentMarketplace />);
    
    expect(screen.getByText('AI Agent Marketplace')).toBeInTheDocument();
    expect(screen.getByText(/discover, compare, and hire/i)).toBeInTheDocument();
  });

  it('displays quick stats in header', () => {
    render(<AgentMarketplace />);
    
    expect(screen.getByText('Available Agents')).toBeInTheDocument();
    expect(screen.getByText('Total Earned')).toBeInTheDocument();
    expect(screen.getByText('Bounties Completed')).toBeInTheDocument();
  });

  it('renders agent cards', () => {
    render(<AgentMarketplace />);
    
    expect(screen.getByText('CodeForge Alpha')).toBeInTheDocument();
    expect(screen.getByText('Solana Sentinel')).toBeInTheDocument();
    expect(screen.getByText('API Architect')).toBeInTheDocument();
  });

  it('filters agents by search query', () => {
    render(<AgentMarketplace />);
    
    const searchInput = screen.getByPlaceholderText(/search agents/i);
    fireEvent.change(searchInput, { target: { value: 'Solana' } });
    
    expect(screen.getByText('Solana Sentinel')).toBeInTheDocument();
    expect(screen.queryByText('CodeForge Alpha')).not.toBeInTheDocument();
  });

  it('shows empty state when no agents match filters', () => {
    render(<AgentMarketplace />);
    
    const searchInput = screen.getByPlaceholderText(/search agents/i);
    fireEvent.change(searchInput, { target: { value: 'NonExistentAgent' } });
    
    expect(screen.getByText('No agents found')).toBeInTheDocument();
  });

  it('calls onHireAgent when hire button is clicked', () => {
    const onHireAgent = jest.fn();
    render(<AgentMarketplace onHireAgent={onHireAgent} />);
    
    const hireButtons = screen.getAllByRole('button', { name: /hire agent/i });
    fireEvent.click(hireButtons[0]);
    
    expect(onHireAgent).toHaveBeenCalled();
  });
});