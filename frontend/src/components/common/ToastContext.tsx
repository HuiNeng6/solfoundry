import React, { createContext, useContext, useReducer, useCallback, ReactNode } from 'react';
import type { Toast, ToastOptions, ToastContextValue } from '../../types/toast';

const ToastContext = createContext<ToastContextValue | null>(null);

type ToastAction =
  | { type: 'ADD'; toast: Toast }
  | { type: 'REMOVE'; id: string }
  | { type: 'REMOVE_ALL' };

function toastReducer(state: Toast[], action: ToastAction): Toast[] {
  switch (action.type) {
    case 'ADD':
      return [...state, action.toast];
    case 'REMOVE':
      return state.filter((t) => t.id !== action.id);
    case 'REMOVE_ALL':
      return [];
    default:
      return state;
  }
}

interface ToastProviderProps {
  children: ReactNode;
  maxToasts?: number;
}

const ToastProvider: React.FC<ToastProviderProps> = ({ children, maxToasts = 3 }) => {
  const [toasts, dispatch] = useReducer(toastReducer, []);

  const addToast = useCallback(
    (options: ToastOptions): string => {
      const id = `toast-${Date.now()}-${Math.random().toString(36).substring(2, 9)}`;
      const toast: Toast = {
        ...options,
        id,
        createdAt: Date.now(),
        duration: options.duration ?? 5000,
      };

      dispatch({ type: 'ADD', toast });

      // If we exceed maxToasts, remove the oldest
      return id;
    },
    []
  );

  const removeToast = useCallback((id: string) => {
    dispatch({ type: 'REMOVE', id });
  }, []);

  const removeAllToasts = useCallback(() => {
    dispatch({ type: 'REMOVE_ALL' });
  }, []);

  // Limit toasts to maxToasts
  const limitedToasts = toasts.slice(-maxToasts);

  return (
    <ToastContext.Provider
      value={{
        toasts: limitedToasts,
        addToast,
        removeToast,
        removeAllToasts,
      }}
    >
      {children}
    </ToastContext.Provider>
  );
};

const useToast = (): ToastContextValue => {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error('useToast must be used within a ToastProvider');
  }
  return context;
};

export { ToastContext, ToastProvider, useToast };
export default ToastProvider;