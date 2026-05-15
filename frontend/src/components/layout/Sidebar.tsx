import { NavLink } from 'react-router-dom';

const links = [
  { to: '/', label: 'Applications', icon: '📋' },
  { to: '/new', label: 'New Application', icon: '➕' },
  { to: '/profile', label: 'My Profile', icon: '👤' },
];

export default function Sidebar() {
  return (
    <aside className="w-56 min-h-screen bg-white border-r border-slate-200 flex flex-col">
      <div className="px-4 py-5 border-b border-slate-200">
        <h1 className="text-lg font-bold text-emerald-700">Auto-Apply</h1>
        <p className="text-xs text-slate-500 mt-0.5">Job application assistant</p>
      </div>
      <nav className="flex-1 px-2 py-4 space-y-1">
        {links.map(({ to, label, icon }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/'}
            className={({ isActive }) =>
              `flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                isActive
                  ? 'bg-emerald-50 text-emerald-700'
                  : 'text-slate-600 hover:bg-slate-100'
              }`
            }
          >
            <span>{icon}</span>
            {label}
          </NavLink>
        ))}
      </nav>
    </aside>
  );
}
