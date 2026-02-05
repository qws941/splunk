import { Link, useLocation } from 'react-router-dom';
import { ChevronRight, Home } from 'lucide-react';
import './Breadcrumb.css';

const routeLabels = {
  dashboard: 'Dashboard',
  security: 'Security Overview',
  correlation: 'Correlation Analysis',
  alerts: 'Alert Management',
  threats: 'Threat Intelligence',
  system: 'System Health',
};

const Breadcrumb = () => {
  const location = useLocation();
  const pathnames = location.pathname.split('/').filter((x) => x);

  if (pathnames.length === 0) return null;

  return (
    <nav className="breadcrumb" aria-label="Breadcrumb">
      <ol className="breadcrumb-list">
        <li className="breadcrumb-item">
          <Link to="/dashboard" className="breadcrumb-link">
            <Home size={16} />
            <span>Home</span>
          </Link>
        </li>
        {pathnames.map((segment, index) => {
          const isLast = index === pathnames.length - 1;
          const path = `/${pathnames.slice(0, index + 1).join('/')}`;
          const label = routeLabels[segment] || segment;

          return (
            <li key={path} className="breadcrumb-item">
              <ChevronRight size={14} className="breadcrumb-separator" />
              {isLast ? (
                <span className="breadcrumb-current">{label}</span>
              ) : (
                <Link to={path} className="breadcrumb-link">
                  {label}
                </Link>
              )}
            </li>
          );
        })}
      </ol>
    </nav>
  );
};

export default Breadcrumb;
