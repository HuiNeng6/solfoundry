/**
 * Toast notification types
 */

export type ToastVariant = 'success' | 'error' | 'warning' | 'info';

export interface ToastOptions {
  variant: ToastVariant;
  message: string;
  duration?: number; // milliseconds, default 5000
}

export interface Toast extends ToastOptions {
  id: string;
  createdAt: number;
}

export interface ToastContextValue {
  toasts: Toast[];
  addToast: (options: ToastOptions) => string;
  removeToast: (id: string) => void;
  removeAllToasts: () => void;
}