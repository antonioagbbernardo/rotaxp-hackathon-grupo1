import { Avatar } from "@/components/ui/Avatar";
import logo from "@/assets/logo-xp-pulse.png";
import { ChevronDown, LogOut } from "lucide-react";
import { Button } from "@/components/ui/Button";

interface Advisor {
  name: string;
  role: string;
}

interface AppHeaderProps {
  advisor: Advisor;
  onLogout: () => void;
  loggingOut: boolean;
  onOpenProfile: () => void;
  profileOpen: boolean;
  profileAvailable: boolean;
}

export function AppHeader({ advisor, onLogout, loggingOut, onOpenProfile, profileOpen, profileAvailable }: AppHeaderProps) {
  return (
    <header className="flex h-19 shrink-0 items-center justify-between gap-3 bg-header px-4 sm:gap-6 sm:px-6">
      <div className="flex items-center gap-4">
        <img src={logo} alt="XP Pulse" className="h-8 w-auto" />
        <p className="hidden border-l border-line pl-4 text-[11px] text-ink-muted sm:block">
          Inteligência de relacionamento
        </p>
      </div>

      <div className="flex min-w-0 items-center gap-2 sm:gap-5">
        <button type="button" onClick={onOpenProfile} disabled={!profileAvailable || loggingOut}
          aria-label="Abrir perfil do assessor" aria-current={profileOpen ? 'page' : undefined}
          className="flex min-w-0 items-center gap-3 rounded-lg p-1.5 text-left transition-colors hover:bg-surface-raised focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand disabled:opacity-60">
          <Avatar name={advisor.name} size="md" className="bg-surface-raised" />
          <div className="hidden min-w-0 sm:block">
            <p className="max-w-40 truncate text-xs font-medium">{advisor.name}</p>
            <p className="max-w-40 truncate text-[10px] text-ink-muted">{advisor.role}</p>
          </div>
          <ChevronDown size={12} className="hidden shrink-0 text-ink-muted sm:block" aria-hidden="true" />
        </button>
        <Button onClick={onLogout} disabled={loggingOut} className="flex shrink-0 items-center gap-2" aria-label="Sair do XP Pulse">
          <LogOut size={14} aria-hidden="true" />
          {loggingOut ? "Saindo…" : "Sair"}
        </Button>
      </div>
    </header>
  );
}
