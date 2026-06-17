import React from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { 
  LayoutDashboard, 
  Users, 
  Activity, 
  BarChart3, 
  LogOut,
  Stethoscope
} from 'lucide-react';

const Sidebar = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <aside className="sidebar">
      <div className="sidebar-logo">
        <Stethoscope size={28} />
        CareSync
      </div>

      <nav className="nav-links">
        <NavLink to="/dashboard" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
          <LayoutDashboard size={20} />
          Dashboard
        </NavLink>
        <NavLink to="/patients" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
          <Users size={20} />
          Patients
        </NavLink>
        <NavLink to="/care-gaps" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
          <Activity size={20} />
          Care Gaps
        </NavLink>
        <NavLink to="/analytics" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
          <BarChart3 size={20} />
          Analytics
        </NavLink>
      </nav>

      <div className="user-profile">
        <div className="avatar">
          {user?.full_name?.charAt(0) || 'U'}
        </div>
        <div style={{ flex: 1, overflow: 'hidden' }}>
          <div style={{ fontSize: '0.875rem', fontWeight: 600, whiteSpace: 'nowrap', textOverflow: 'ellipsis', overflow: 'hidden' }}>
            {user?.full_name || 'User'}
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', textTransform: 'capitalize' }}>
            {user?.role || 'Role'}
          </div>
        </div>
        <button 
          onClick={handleLogout}
          style={{ background: 'transparent', border: 'none', color: 'var(--text-secondary)', cursor: 'pointer' }}
          title="Logout"
        >
          <LogOut size={18} />
        </button>
      </div>
    </aside>
  );
};

export default Sidebar;
