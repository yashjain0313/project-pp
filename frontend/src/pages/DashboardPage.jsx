import React, { useState, useEffect } from 'react';
import api from '../api';
import KPICard from '../components/KPICard';
import { Users, AlertTriangle, Activity, CheckCircle } from 'lucide-react';
import { 
  PieChart, Pie, Cell, Tooltip as RechartsTooltip, ResponsiveContainer,
  BarChart, Bar, XAxis, YAxis, CartesianGrid
} from 'recharts';

const DashboardPage = () => {
  const [kpis, setKpis] = useState(null);
  const [riskData, setRiskData] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        const [kpiRes, riskRes] = await Promise.all([
          api.get('/analytics/dashboard'),
          api.get('/analytics/risk-distribution')
        ]);
        
        setKpis(kpiRes.data);
        
        // Format for pie chart
        const formattedRisk = riskRes.data.map(item => ({
          name: item.level.charAt(0).toUpperCase() + item.level.slice(1),
          value: item.count,
          color: getRiskColor(item.level)
        }));
        setRiskData(formattedRisk);
      } catch (error) {
        console.error("Failed to fetch dashboard data", error);
      } finally {
        setLoading(false);
      }
    };

    fetchDashboardData();
  }, []);

  const getRiskColor = (level) => {
    switch(level) {
      case 'low': return 'var(--risk-low)';
      case 'moderate': return 'var(--risk-moderate)';
      case 'high': return 'var(--risk-high)';
      case 'critical': return 'var(--risk-critical)';
      default: return '#ccc';
    }
  };

  if (loading) return <div>Loading dashboard...</div>;

  return (
    <div>
      <h1>Dashboard overview</h1>
      
      <div className="grid grid-cols-4 gap-6" style={{ marginBottom: '2rem' }}>
        <KPICard 
          title="Total Patients" 
          value={kpis?.total_patients || 0} 
          icon={Users} 
          color="#3b82f6" 
        />
        <KPICard 
          title="High/Critical Risk" 
          value={(kpis?.high_risk_patients || 0) + (kpis?.critical_risk_patients || 0)} 
          subtitle="Patients requiring attention"
          icon={AlertTriangle} 
          color="var(--risk-critical)" 
        />
        <KPICard 
          title="Open Care Gaps" 
          value={kpis?.total_open_gaps || 0} 
          subtitle="Missing preventive care"
          icon={Activity} 
          color="var(--risk-high)" 
        />
        <KPICard 
          title="Closure Rate" 
          value={`${kpis?.gap_closure_rate || 0}%`} 
          subtitle="Care gaps closed"
          icon={CheckCircle} 
          color="var(--risk-low)" 
        />
      </div>

      <div className="grid grid-cols-2 gap-6">
        <div className="card">
          <h2>Risk Distribution</h2>
          <div style={{ height: '300px' }}>
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={riskData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={100}
                  paddingAngle={5}
                  dataKey="value"
                >
                  {riskData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <RechartsTooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div style={{ display: 'flex', justifyContent: 'center', gap: '1rem', marginTop: '1rem' }}>
            {riskData.map(item => (
              <div key={item.name} style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.875rem' }}>
                <div style={{ width: '12px', height: '12px', borderRadius: '50%', backgroundColor: item.color }}></div>
                {item.name} ({item.value})
              </div>
            ))}
          </div>
        </div>

        <div className="card" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center', textAlign: 'center' }}>
          <div style={{ backgroundColor: 'var(--primary-light)', padding: '1rem', borderRadius: '50%', marginBottom: '1rem', color: 'var(--primary-color)' }}>
            <Activity size={48} />
          </div>
          <h2>Run Gap Analysis</h2>
          <p style={{ color: 'var(--text-secondary)', marginBottom: '1.5rem', maxWidth: '300px' }}>
            Analyze your patient panel against HEDIS and USPSTF clinical guidelines to identify new care gaps.
          </p>
          <button 
            className="btn btn-primary"
            onClick={async () => {
              try {
                await api.post('/care-gaps/analyze-all');
                alert('Analysis complete! Check the Care Gaps page.');
                window.location.reload();
              } catch (e) {
                alert('Failed to run analysis');
              }
            }}
          >
            Analyze All Patients
          </button>
        </div>
      </div>
    </div>
  );
};

export default DashboardPage;
