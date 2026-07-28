import { NavLink, Outlet } from "react-router-dom";
import { clsx } from "clsx";
import {
  Activity,
  BarChart3,
  Settings,
  Terminal,
  Github,
  Zap,
} from "lucide-react";

const navItems = [
  { to: "/", icon: Activity, label: "Dashboard", end: true },
  { to: "/analytics", icon: BarChart3, label: "Analytics" },
  { to: "/settings", icon: Settings, label: "Settings" },
];

export function Layout() {
  return (
    <div className="min-h-screen bg-surface-950 flex">
      {/* Sidebar */}
      <aside className="w-64 border-r border-surface-800 bg-surface-900/50 flex flex-col">
        {/* Logo */}
        <div className="p-5 border-b border-surface-800">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-primary-500 to-accent-500 flex items-center justify-center">
              <Zap className="w-5 h-5 text-white" />
            </div>
            <div>
              <h1 className="text-sm font-bold gradient-text">AutoDevOps</h1>
              <p className="text-[10px] text-surface-500">Self-Healing Agent</p>
            </div>
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex-1 p-3 space-y-1">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className={({ isActive }) =>
                clsx(
                  "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-200",
                  isActive
                    ? "bg-primary-500/10 text-primary-400 border border-primary-500/20"
                    : "text-surface-400 hover:text-surface-200 hover:bg-surface-800/50 border border-transparent"
                )
              }
            >
              <item.icon className="w-4 h-4" />
              {item.label}
            </NavLink>
          ))}
        </nav>

        {/* Footer */}
        <div className="p-4 border-t border-surface-800">
          <a
            href="https://github.com/Sarancoding/Autonomous-DevOps"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-2 text-xs text-surface-500 hover:text-surface-300 transition-colors"
          >
            <Github className="w-3.5 h-3.5" />
            Sarancoding/Autonomous-DevOps
          </a>
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 flex flex-col min-h-screen">
        {/* Top bar */}
        <header className="h-14 border-b border-surface-800 bg-surface-900/30 flex items-center justify-between px-6">
          <div className="flex items-center gap-3">
            <Terminal className="w-4 h-4 text-primary-400" />
            <span className="text-sm text-surface-400">
              Autonomous DevOps Agent
            </span>
          </div>
          <div className="flex items-center gap-2">
            <span className="inline-block w-2 h-2 rounded-full bg-success animate-pulse" />
            <span className="text-xs text-surface-500">Agent Online</span>
          </div>
        </header>

        {/* Page content */}
        <div className="flex-1 p-6 overflow-auto">
          <Outlet />
        </div>
      </main>
    </div>
  );
}
