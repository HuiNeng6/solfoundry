/**
 * Toast notification context and provider
 * @module contexts/ToastContext
 */
import { createContext, useContext, useReducer, useCallback, ReactNode } from 'react';
import type { Toast, ToastOptions, ToastContextValue } from '../types/toast';

// ============================================================================
// Constants
// ============================================================================

const MAX_TOASTS = 3;
const DEFAULT_DURATION = 5000; // 5 seconds

// ============================================================================
// Context
// ============================================================================

const ToastContext = createContext<ToastContextValue | null>(null);

// ============================================================================
// Reducer
// ============================================================================

type ToastAction =
  | { type: 'ADD'; toast: Toast }
  | { type: 'REMOVE'; id: string }
  | { type: 'CLEAR' };

function toastReducer(state: Toast[], action: ToastAction): Toast[] {
  switch (action.type) {
    case 'ADD':
      // Add to beginning, limit to MAX_TOASTS
      return [action.toast, ...state].slice(0, MAX_TOASTS);
    case 'REMOVE':
      return state.filter((t) => t.id !== action.id);
    case 'CLEAR':
      return [];
    default:
      return state;
  }
}

// ============================================================================
// Provider
// ============================================================================

interface ToastProviderProps {
  children: ReactNode;
  maxToasts?: number;
}

export function ToastProvider({ children, maxToasts = MAX_TOASTS }: ToastProviderProps) {
  const [toasts, dispatch] = useReducer(toastReducer, []);

  const addToast = useCallback((options: ToastOptions): string => {
    const id = crypto.randomUUID();
    const toast: Toast = {
      id,
      variant: options.variant,
      title: options.title,
      message: options.message,
      duration: options.duration ?? DEFAULT_DURATION,
    };
    dispatch({ type: 'ADD', toast });
    return id;
  }, []);

  const removeToast = useCallback((id: string) => {
    dispatch({ type: 'REMOVE', id });
  }, []);

  const clearToasts = useCallback(() => {
    dispatch({ type: 'CLEAR' });
  }, []);

  return (
    <ToastContext.Provider value={{ toasts, addToast, removeToast, clearToasts }}>
      {children}
    </ToastContext.Provider>
  );
}

// ============================================================================
// Hook
// ============================================================================

export function useToast(): ToastContextValue {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error('useToast must be used within a ToastProvider');
  }
  return context;
}

// ============================================================================
// Convenience hooks
// ============================================================================

export function useToastActions() {
  const { addToast, removeToast, clearToasts } = useToast();

  return {
    success: (title: string, message?: string) => 
      addToast({ variant: 'success', title, message }),
    error: (title: string, message?: string) => 
      addToast({ variant: 'error', title, message }),
    warning: (title: string, message?: string) => 
      addToast({ variant: 'warning', title, message }),
    info: (title: string, message?: string) => 
      addToast({ variant: 'info', title, message }),
    remove: removeToast,
    clear: clearToasts,
  };
}