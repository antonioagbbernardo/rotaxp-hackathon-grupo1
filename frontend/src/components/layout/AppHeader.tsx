import { Avatar } from "@/components/ui/Avatar";
import logo from "@/assets/logo-xp-pulse.png";

interface Advisor {
  name: string;
  role: string;
}

interface AppHeaderProps {
  advisor: Advisor;
}

export function AppHeader({ advisor }: AppHeaderProps) {
  return (
    <header className="flex h-19 shrink-0 items-center justify-between gap-6 bg-header px-6">
      <div className="flex items-center gap-4">
        <img src={logo} alt="XP Pulse" className="h-8 w-auto" />
        <p className="hidden border-l border-line pl-4 text-[11px] text-ink-muted sm:block">
          Inteligência de relacionamento
        </p>
      </div>

      <div className="flex items-center gap-5">
        <div className="flex items-center gap-3">
          <Avatar name={advisor.name} size="md" className="bg-surface-raised" />
          <div className="hidden sm:block">
            <p className="text-xs font-medium">{advisor.name}</p>
            <p className="text-[10px] text-ink-muted">{advisor.role}</p>
          </div>
        </div>
      </div>
    </header>
  );
}
