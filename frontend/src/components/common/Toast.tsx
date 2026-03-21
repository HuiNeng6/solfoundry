/**
 * Toast notification component
 * @module components/common/Toast
 */
import { useEffect, useState, useCallback } from 'react';
import type { Toast as ToastType, ToastVariant } from '../../types/toast';

// ============================================================================
// Icons
// ============================================================================

function SuccessIcon() {
  return (
    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
  );
}

function ErrorIcon() {
  return (
    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" />
    </svg>
  );
}

function WarningIcon() {
  return (
    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" />
    </svg>
  );
}

function InfoIcon() {
  return (
    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="M11.25 11.25l.041-.02a.75.75 0 011.063.852l-.708 2.836a.75.75 0 001.063.853l.041-.021M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-9-3.75h.008v.008H12V8.25z" />
    </svg>
  );
}

function CloseIcon() {
  return (
    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
    </svg>
  );
}

// ============================================================================
// Variant Config
// ============================================================================

const VARIANT_CONFIG: Record<ToastVariant, {
  icon: React.ReactNode;
  bgClass: string;
  iconColor: string;
}> = {
  success: {
    icon: <SuccessIcon />,
    bgClass: 'bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800',
    iconColor: 'text-green-600 dark:text-green-400',
  },
  error: {
    icon: <ErrorIcon />,
    bgClass: 'bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800',
    iconColor: 'text-red-600 dark:text-red-400',
  },
  warning: {
    icon: <WarningIcon />,
    bgClass: 'bg-yellow-50 dark:bg-yellow-900/20 border-yellow-200 dark:border-yellow-800',
    iconColor: 'text-yellow-600 dark:text-yellow-400',
  },
  info: {
    icon: <InfoIcon />,
    bgClass: 'bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800',
    iconColor: 'text-blue-600 dark:text-blue-400',
  },
};

// ============================================================================
// Toast Component
// ============================================================================

interface ToastProps {
  toast: ToastType;
  onRemove: (id: string) => void;
}

export function Toast({ toast, onRemove }: ToastProps) {
  const [isExiting, setIsExiting] = useState(false);
  const config = VARIANT_CONFIG[toast.variant];

  const handleClose = useCallback(() => {
    setIsExiting(true);
    setTimeout(() => onRemove(toast.id), 200);
  }, [onRemove, toast.id]);

  // Auto-dismiss
  useEffect(() => {
    if (toast.duration && toast.duration > 0) {
      const timer = setTimeout(handleClose, toast.duration);
      return () => clearTimeout(timer);
    }
  }, [toast.duration, handleClose]);

  return (
    <div
      role="alert"
      className={`
        flex items-start gap-3 p-4 rounded-lg border shadow-lg
        transition-all duration-200 transform
        ${isExiting ? 'opacity-0 translate-x-4' : 'opacity-100 translate-x-0'}
        ${config.bgClass}
      `}
    >
      {/* Icon */}
      <div className={`shrink-0 ${config.iconColor}`}>
        {config.icon}
      </div>

      {/* Content */}
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-gray-900 dark:text-white">
          {toast.title}
        </p>
        {toast.message && (
          <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">
            {toast.message}
          </p>
        )}
      </div>

      {/* Close button */}
      <button
        onClick={handleClose}
        className="shrink-0 p-1 rounded text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
        aria-label="Dismiss notification"
      >
        <CloseIcon />
      </button>
    </div>
  );
}

// ============================================================================
// ToastContainer Component
// ============================================================================

interface ToastContainerProps {
  toasts: ToastType[];
  onRemove: (id: string) => void;
}

export function ToastContainer({ toasts, onRemove }: ToastContainerProps) {
  if (toasts.length === 0) return null;

  return (
    <div
      aria-live="polite"
      aria-label="Notifications"
      className="fixed top-4 right-4 z-50 flex flex-col gap-2 w-full max-w-sm"
    >
      {toasts.map((toast) => (
        <Toast key={toast.id} toast={toast} onRemove={onRemove} />
      ))}
    </div>
  );
}