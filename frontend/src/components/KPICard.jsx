import React from 'react';

const KPICard = ({ title, value, subtitle, icon: Icon, color = 'var(--primary-color)' }) => {
  return (
    <div className="card" style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between' }}>
      <div>
        <div style={{ color: 'var(--text-secondary)', fontSize: '0.875rem', fontWeight: 500, marginBottom: '0.5rem' }}>
          {title}
        </div>
        <div style={{ fontSize: '1.875rem', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '0.25rem' }}>
          {value}
        </div>
        {subtitle && (
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
            {subtitle}
          </div>
        )}
      </div>
      {Icon && (
        <div style={{ 
          backgroundColor: `${color}20`, // 20% opacity 
          color: color,
          padding: '0.75rem',
          borderRadius: 'var(--radius-md)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center'
        }}>
          <Icon size={24} />
        </div>
      )}
    </div>
  );
};

export default KPICard;
