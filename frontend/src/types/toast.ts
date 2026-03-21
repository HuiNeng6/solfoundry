/**
 * Toast notification types
 * @module types/toast
 */

export type ToastVariant = 'success' | 'error' | 'warning' | 'info';

export interface Toast {
  id: string;
  variant: ToastVariant;
  title: string;
  message?: string;
  duration?: number; // milliseconds, 0 = no auto-dismiss
}

export interface ToastOptions {
  variant: ToastVariant;
  title: string;
  message?: string;
  duration?: number;
}

export interface ToastContextValue {
  toasts: Toast[];
  addToast: (options: ToastOptions) => string;
  removeToast: (id: string) => void;
  clearToasts: () => void;
}