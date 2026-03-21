import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import { ToastProvider, useToast } from '../components/common/ToastContext';
import { ToastContainer } from '../components/common/Toast';
import type { ToastOptions } from '../types/toast';

// Test component to trigger toasts
const ToastTrigger = ({ options }: { options: ToastOptions }) => {
  const { addToast } = useToast();
  return (
    <button onClick={() => addToast(options)} data-testid="trigger-toast">
      Show Toast
    </button>
  );
};

describe('ToastProvider', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('renders children correctly', () => {
    render(
      <ToastProvider>
        <div data-testid="child">Child Content</div>
      </ToastProvider>
    );
    expect(screen.getByTestId('child')).toBeInTheDocument();
  });

  it('throws error when useToast is used outside provider', () => {
    const consoleError = vi.spyOn(console, 'error').mockImplementation(() => {});
    
    const TestComponent = () => {
      useToast();
      return null;
    };

    expect(() => render(<TestComponent />)).toThrow(
      'useToast must be used within a ToastProvider'
    );
    
    consoleError.mockRestore();
  });
});

describe('useToast hook', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('adds a toast successfully', async () => {
    const TestComponent = () => {
      const { toasts, addToast } = useToast();
      return (
        <>
          <button onClick={() => addToast({ variant: 'success', message: 'Test toast' })}>
            Add
          </button>
          <div data-testid="count">{toasts.length}</div>
        </>
      );
    };

    render(
      <ToastProvider>
        <TestComponent />
      </ToastProvider>
    );

    expect(screen.getByTestId('count').textContent).toBe('0');
    
    await act(async () => {
      fireEvent.click(screen.getByText('Add'));
    });
    
    expect(screen.getByTestId('count').textContent).toBe('1');
  });

  it('removes a toast successfully', async () => {
    const TestComponent = () => {
      const { toasts, addToast, removeToast } = useToast();
      return (
        <>
          <button 
            onClick={() => addToast({ variant: 'info', message: 'Info toast' })}
            data-testid="add"
          >
            Add
          </button>
          <button 
            onClick={() => toasts[0] && removeToast(toasts[0].id)}
            data-testid="remove"
          >
            Remove
          </button>
          <div data-testid="count">{toasts.length}</div>
        </>
      );
    };

    render(
      <ToastProvider>
        <TestComponent />
      </ToastProvider>
    );

    await act(async () => {
      fireEvent.click(screen.getByTestId('add'));
    });
    
    expect(screen.getByTestId('count').textContent).toBe('1');
    
    await act(async () => {
      fireEvent.click(screen.getByTestId('remove'));
    });
    
    expect(screen.getByTestId('count').textContent).toBe('0');
  });

  it('removes all toasts', async () => {
    const TestComponent = () => {
      const { toasts, addToast, removeAllToasts } = useToast();
      return (
        <>
          <button 
            onClick={() => {
              addToast({ variant: 'success', message: 'Toast 1' });
              addToast({ variant: 'error', message: 'Toast 2' });
            }}
            data-testid="add-many"
          >
            Add Many
          </button>
          <button onClick={removeAllToasts} data-testid="remove-all">
            Remove All
          </button>
          <div data-testid="count">{toasts.length}</div>
        </>
      );
    };

    render(
      <ToastProvider>
        <TestComponent />
      </ToastProvider>
    );

    await act(async () => {
      fireEvent.click(screen.getByTestId('add-many'));
    });
    
    expect(screen.getByTestId('count').textContent).toBe('2');
    
    await act(async () => {
      fireEvent.click(screen.getByTestId('remove-all'));
    });
    
    expect(screen.getByTestId('count').textContent).toBe('0');
  });

  it('uses default duration of 5000ms', async () => {
    const TestComponent = () => {
      const { toasts, addToast } = useToast();
      return (
        <>
          <button onClick={() => addToast({ variant: 'success', message: 'Test' })}>
            Add
          </button>
          <div data-testid="count">{toasts.length}</div>
        </>
      );
    };

    render(
      <ToastProvider>
        <TestComponent />
      </ToastProvider>
    );

    await act(async () => {
      fireEvent.click(screen.getByText('Add'));
    });
    
    expect(screen.getByTestId('count').textContent).toBe('1');
    
    // Fast forward 4999ms - toast should still exist
    await act(async () => {
      vi.advanceTimersByTime(4999);
    });
    
    expect(screen.getByTestId('count').textContent).toBe('1');
    
    // Fast forward 1 more ms - toast should be removed
    await act(async () => {
      vi.advanceTimersByTime(1);
    });
    
    // Allow exit animation to complete
    await act(async () => {
      vi.advanceTimersByTime(300);
    });
    
    expect(screen.getByTestId('count').textContent).toBe('0');
  });

  it('uses custom duration', async () => {
    const TestComponent = () => {
      const { toasts, addToast } = useToast();
      return (
        <>
          <button onClick={() => addToast({ variant: 'info', message: 'Test', duration: 2000 })}>
            Add
          </button>
          <div data-testid="count">{toasts.length}</div>
        </>
      );
    };

    render(
      <ToastProvider>
        <TestComponent />
      </ToastProvider>
    );

    await act(async () => {
      fireEvent.click(screen.getByText('Add'));
    });
    
    expect(screen.getByTestId('count').textContent).toBe('1');
    
    // Fast forward 2000ms
    await act(async () => {
      vi.advanceTimersByTime(2000);
    });
    
    // Allow exit animation
    await act(async () => {
      vi.advanceTimersByTime(300);
    });
    
    expect(screen.getByTestId('count').textContent).toBe('0');
  });
});

describe('ToastContainer', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('renders toast with correct message', async () => {
    const TestComponent = () => {
      const { toasts, addToast, removeToast } = useToast();
      return (
        <>
          <button 
            onClick={() => addToast({ variant: 'success', message: 'Operation succeeded!' })}
            data-testid="trigger"
          >
            Show
          </button>
          <ToastContainer toasts={toasts} onRemove={removeToast} />
        </>
      );
    };

    render(
      <ToastProvider>
        <TestComponent />
      </ToastProvider>
    );

    await act(async () => {
      fireEvent.click(screen.getByTestId('trigger'));
    });

    // Wait for enter animation
    await act(async () => {
      vi.advanceTimersByTime(50);
    });

    expect(screen.getByText('Operation succeeded!')).toBeInTheDocument();
  });

  it('shows correct toast variant styles', async () => {
    const variants: Array<{ variant: ToastOptions['variant']; testId: string }> = [
      { variant: 'success', testId: 'success-btn' },
      { variant: 'error', testId: 'error-btn' },
      { variant: 'warning', testId: 'warning-btn' },
      { variant: 'info', testId: 'info-btn' },
    ];

    const TestComponent = () => {
      const { toasts, addToast, removeToast } = useToast();
      return (
        <>
          {variants.map(({ variant, testId }) => (
            <button
              key={testId}
              data-testid={testId}
              onClick={() => addToast({ variant, message: `${variant} message` })}
            >
              {variant}
            </button>
          ))}
          <ToastContainer toasts={toasts} onRemove={removeToast} />
        </>
      );
    };

    render(
      <ToastProvider>
        <TestComponent />
      </ToastProvider>
    );

    for (const { variant, testId } of variants) {
      await act(async () => {
        fireEvent.click(screen.getByTestId(testId));
        vi.advanceTimersByTime(50);
      });
      
      expect(screen.getByText(`${variant} message`)).toBeInTheDocument();
    }
  });

  it('limits to max 3 visible toasts', async () => {
    const TestComponent = () => {
      const { toasts, addToast, removeToast } = useToast();
      return (
        <>
          <button
            onClick={() => {
              addToast({ variant: 'info', message: 'Toast 1' });
              addToast({ variant: 'info', message: 'Toast 2' });
              addToast({ variant: 'info', message: 'Toast 3' });
              addToast({ variant: 'info', message: 'Toast 4' });
            }}
            data-testid="add-four"
          >
            Add Four
          </button>
          <ToastContainer toasts={toasts} onRemove={removeToast} />
        </>
      );
    };

    render(
      <ToastProvider>
        <TestComponent />
      </ToastProvider>
    );

    await act(async () => {
      fireEvent.click(screen.getByTestId('add-four'));
      vi.advanceTimersByTime(50);
    });

    // Should only show last 3 toasts
    expect(screen.queryByText('Toast 1')).not.toBeInTheDocument();
    expect(screen.getByText('Toast 2')).toBeInTheDocument();
    expect(screen.getByText('Toast 3')).toBeInTheDocument();
    expect(screen.getByText('Toast 4')).toBeInTheDocument();
  });

  it('closes toast on manual close button click', async () => {
    const TestComponent = () => {
      const { toasts, addToast, removeToast } = useToast();
      return (
        <>
          <button
            onClick={() => addToast({ variant: 'success', message: 'Closable toast' })}
            data-testid="add"
          >
            Add
          </button>
          <ToastContainer toasts={toasts} onRemove={removeToast} />
        </>
      );
    };

    render(
      <ToastProvider>
        <TestComponent />
      </ToastProvider>
    );

    await act(async () => {
      fireEvent.click(screen.getByTestId('add'));
      vi.advanceTimersByTime(50);
    });

    expect(screen.getByText('Closable toast')).toBeInTheDocument();

    const closeButton = screen.getByRole('button', { name: /dismiss/i });
    
    await act(async () => {
      fireEvent.click(closeButton);
      vi.advanceTimersByTime(300); // Exit animation
    });

    expect(screen.queryByText('Closable toast')).not.toBeInTheDocument();
  });
});