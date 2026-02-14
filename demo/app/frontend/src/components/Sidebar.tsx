import { NavLink } from 'react-router-dom';

const mainLinks = [
  { to: '/', label: 'Talk Track' },
  { to: '/dashboard', label: 'Dashboard' },
  { to: '/analytics', label: 'Fleet health & revenue risk' },
  { to: '/assets', label: 'Assets' },
  { to: '/assets/detail', label: 'Asset Detail' },
  { to: '/compression', label: 'Compression' },
  { to: '/performance', label: 'Performance' },
  { to: '/architecture', label: 'Architecture' },
  { to: '/data-generation', label: 'Data Generation' },
];

const assetFrameworkLinks = [
  { to: '/asset-framework/hierarchy', label: 'Asset Hierarchy' },
  { to: '/asset-framework/templates', label: 'Templates' },
];

function NavItem({ to, label }: { to: string; label: string }) {
  return (
    <li>
      <NavLink
        to={to}
        end={to === '/'}
        className={({ isActive }) =>
          `block px-3 py-2 rounded text-sm ${
            isActive
              ? 'bg-gray-800 text-databricks-primary'
              : 'text-gray-400 hover:text-gray-100 hover:bg-gray-800/50'
          }`
        }
      >
        {label}
      </NavLink>
    </li>
  );
}

export default function Sidebar() {
  return (
    <nav className="w-56 flex-shrink-0 bg-databricks-teal border-r border-gray-700 p-4">
      <div className="mb-6">
        <div className="flex items-center gap-2 mb-2">
          <img src="/logos/AGL_Energy_logo.svg" alt="AGL Energy" className="h-8 w-auto object-contain" />
          <h1 className="text-lg font-bold text-agl-blue">
            AGL OT Lakehouse
          </h1>
        </div>
        <p className="text-xs text-databricks-primary flex items-center gap-1.5">
          <img src="/logos/databricks-full.svg" alt="" className="h-5 w-auto object-contain" aria-hidden />
          Powered by Databricks
        </p>
      </div>
      <ul className="space-y-1">
        {mainLinks.map(({ to, label }) => (
          <NavItem key={to} to={to} label={label} />
        ))}
      </ul>
      <div className="mt-6">
        <p className="text-xs uppercase tracking-wider text-gray-500 px-3 mb-2">
          Asset Framework
        </p>
        <ul className="space-y-1">
          {assetFrameworkLinks.map(({ to, label }) => (
            <NavItem key={to} to={to} label={label} />
          ))}
        </ul>
      </div>
    </nav>
  );
}
