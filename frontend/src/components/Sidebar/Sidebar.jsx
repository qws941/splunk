import { useState, useEffect, useCallback } from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import {
  LayoutDashboard,
  Shield,
  Link2,
  Bell,
  Target,
  Settings,
  ChevronLeft,
  ChevronRight,
  ChevronDown,
  Search,
  Menu,
  X,
  ExternalLink,
} from 'lucide-react';
import './Sidebar.css';

const SPLUNK_BASE = import.meta.env.VITE_SPLUNK_BASE_URL || 'http://192.168.50.150:8000';

const navItems = [
  { path: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { 
    path: '/security', 
    label: 'Security', 
    icon: Shield,
    children: [
      { path: '/security/events', label: 'Events' },
      { path: '/security/policies', label: 'Policies' },
    ]
  },
  { path: '/correlation', label: 'Correlation', icon: Link2 },
  { 
    path: '/alerts', 
    label: 'Alerts', 
    icon: Bell,
    children: [
      { path: '/alerts/active', label: 'Active' },
      { path: '/alerts/history', label: 'History' },
    ]
  },
  { path: '/threats', label: 'Threats', icon: Target },
  { path: '/system', label: 'System', icon: Settings },
];

const splunkLinks = [
  { label: 'Search', path: '/app/security_alert/search' },
  { label: 'Dashboards', path: '/app/security_alert/fortigate_comprehensive_alerts' },
  { label: 'Alerts', path: '/app/security_alert/fortigate_alerts_monitoring' },
];

const Sidebar = () => {
  const navigate = useNavigate();
  const [collapsed, setCollapsed] = useState(() => {
    return localStorage.getItem('sidebar-collapsed') === 'true';
  });
  const [mobileOpen, setMobileOpen] = useState(false);
  const [expandedItems, setExpandedItems] = useState({});
  const [searchOpen, setSearchOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    localStorage.setItem('sidebar-collapsed', collapsed);
  }, [collapsed]);

  useEffect(() => {
    const handleKeyDown = (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        setSearchOpen(true);
      }
      if (e.key === 'Escape') {
        setSearchOpen(false);
        setSearchQuery('');
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  const toggleSidebar = () => setCollapsed(!collapsed);
  const toggleMobile = () => setMobileOpen(!mobileOpen);
  
  const toggleExpand = (path) => {
    setExpandedItems(prev => ({ ...prev, [path]: !prev[path] }));
  };

  const handleSearch = useCallback((e) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      const flatItems = navItems.flatMap(item => 
        item.children ? [item, ...item.children] : [item]
      );
      const match = flatItems.find(item => 
        item.label.toLowerCase().includes(searchQuery.toLowerCase())
      );
      if (match) {
        navigate(match.path);
        setSearchOpen(false);
        setSearchQuery('');
      }
    }
  }, [searchQuery, navigate]);

  const filteredItems = searchQuery
    ? navItems.flatMap(item => item.children ? [item, ...item.children] : [item])
        .filter(item => item.label.toLowerCase().includes(searchQuery.toLowerCase()))
    : [];

  const renderNavItem = ({ path, label, icon: Icon, children }) => {
    const hasChildren = children && children.length > 0;
    const isExpanded = expandedItems[path];

    if (hasChildren && !collapsed) {
      return (
        <div key={path} className="nav-group">
          <button
            className="sidebar-link nav-group-toggle"
            onClick={() => toggleExpand(path)}
          >
            <Icon className="sidebar-icon" size={20} />
            <span className="sidebar-label">{label}</span>
            <ChevronDown 
              className={`nav-chevron ${isExpanded ? 'expanded' : ''}`} 
              size={16} 
            />
          </button>
          {isExpanded && (
            <div className="nav-children">
              {children.map(child => (
                <NavLink
                  key={child.path}
                  to={child.path}
                  className={({ isActive }) =>
                    `sidebar-link child-link ${isActive ? 'active' : ''}`
                  }
                >
                  <span className="sidebar-label">{child.label}</span>
                </NavLink>
              ))}
            </div>
          )}
        </div>
      );
    }

    return (
      <NavLink
        key={path}
        to={path}
        className={({ isActive }) =>
          `sidebar-link ${isActive ? 'active' : ''}`
        }
        title={collapsed ? label : undefined}
      >
        <Icon className="sidebar-icon" size={20} />
        {!collapsed && <span className="sidebar-label">{label}</span>}
      </NavLink>
    );
  };

  return (
    <>
      <button className="mobile-menu-btn" onClick={toggleMobile}>
        {mobileOpen ? <X size={24} /> : <Menu size={24} />}
      </button>

      <div 
        className={`sidebar-overlay ${mobileOpen ? 'visible' : ''}`} 
        onClick={() => setMobileOpen(false)}
      />

      <aside className={`sidebar ${collapsed ? 'collapsed' : ''} ${mobileOpen ? 'mobile-open' : ''}`}>
        <div className="sidebar-header">
          {!collapsed && <span className="sidebar-title">Security Alert</span>}
        </div>
        
        <button 
          className="search-trigger" 
          onClick={() => setSearchOpen(true)}
          title="Search (⌘K)"
        >
          <Search size={16} />
          {!collapsed && <span>Search...</span>}
          {!collapsed && <kbd>⌘K</kbd>}
        </button>
        
        <nav className="sidebar-nav">
          {navItems.map(renderNavItem)}
        </nav>
        
        {!collapsed && (
          <div className="splunk-links">
            <span className="splunk-links-title">Splunk</span>
            {splunkLinks.map(link => (
              <a
                key={link.path}
                href={`${SPLUNK_BASE}${link.path}`}
                target="_blank"
                rel="noopener noreferrer"
                className="splunk-link"
              >
                <span>{link.label}</span>
                <ExternalLink size={14} />
              </a>
            ))}
          </div>
        )}
        
        <button className="sidebar-toggle" onClick={toggleSidebar}>
          {collapsed ? <ChevronRight size={20} /> : <ChevronLeft size={20} />}
          {!collapsed && <span>Collapse</span>}
        </button>
      </aside>

      {searchOpen && (
        <div className="command-palette-overlay" onClick={() => setSearchOpen(false)}>
          <div className="command-palette" onClick={e => e.stopPropagation()}>
            <form onSubmit={handleSearch}>
              <div className="command-input-wrapper">
                <Search size={20} />
                <input
                  type="text"
                  className="command-input"
                  placeholder="Search pages..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  autoFocus
                />
                <kbd>ESC</kbd>
              </div>
            </form>
            {filteredItems.length > 0 && (
              <ul className="command-results">
                {filteredItems.map(item => (
                  <li key={item.path}>
                    <button
                      className="command-result"
                      onClick={() => {
                        navigate(item.path);
                        setSearchOpen(false);
                        setSearchQuery('');
                      }}
                    >
                      {item.icon && <item.icon size={16} />}
                      <span>{item.label}</span>
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
      )}
    </>
  );
};

export default Sidebar;
