import Logo from '../components/Logo';
import Mascot from '../components/Mascot';
import { Card } from '../components/ui';

export default function AuthLayout({ title, intro, children }) {
  return (
    <main className="h-full overflow-y-auto pt-[env(safe-area-inset-top,0px)] safe-bottom">
      <div className="mx-auto w-full max-w-md px-4 py-6 sm:py-10">
        <header className="mb-5"><Logo /></header>
        <Card>
          <div className="flex items-center justify-between gap-3 mb-5">
            <div className="min-w-0">
              <h1 className="text-[28px] wrap-anywhere">{title}</h1>
              {intro && <p className="mt-2 text-sm text-text-soft">{intro}</p>}
            </div>
            <Mascot size={60} className="shrink-0" />
          </div>
          {children}
        </Card>
      </div>
    </main>
  );
}
