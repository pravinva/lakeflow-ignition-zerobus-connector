import { NavLink } from 'react-router-dom';
import aglLogo from '../agl/AGL_Energy_logo.png';
import databricksLogo from '../default/databricks-full.png';

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
              ? 'bg-gray-100 text-databricks-primary'
              : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
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
    <nav className="w-56 flex-shrink-0 bg-white border-r border-gray-200 p-4 shadow-sm">
      <div className="mb-6">
        <div className="flex items-center gap-2 mb-2">
          <img src={aglLogo} alt="AGL Energy" className="h-8 w-auto object-contain" />
          <h1 className="text-lg font-bold text-agl-blue">
            AGL OT Lakehouse
          </h1>
        </div>
        <p className="text-xs text-databricks-primary flex items-center gap-1.5">
          <img src={databricksLogo} alt="" className="h-5 w-auto object-contain" aria-hidden />
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
