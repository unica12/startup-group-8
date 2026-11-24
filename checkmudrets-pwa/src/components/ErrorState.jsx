import { AlertCircle } from 'lucide-react';
import { Button } from './ui';

export default function ErrorState({ message, onRetry }) {
  return (
    <div className="rounded-input bg-danger-bg px-4 py-3 text-danger">
      <p role="alert" className="flex items-start gap-2 text-sm font-bold wrap-anywhere">
        <AlertCircle size={18} className="mt-0.5 shrink-0" aria-hidden="true" />
        {message}
      </p>
      {onRetry && (
        <Button size="sm" variant="secondary" onClick={onRetry} className="mt-3">
          Повторить
        </Button>
      )}
    </div>
  );
}
