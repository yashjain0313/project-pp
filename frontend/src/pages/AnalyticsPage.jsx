import React, { useState, useEffect } from 'react';
import api from '../api';
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  LineChart, Line
} from 'recharts';

const AnalyticsPage = () => {
  const [trends, setTrends] = useState([]);
  const [conditions, setConditions] = useState([]);
  const [providers, setProviders] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchAnalytics = async () => {
      try {
        const [trendRes, condRes, provRes] = await Promise.all([
          api.get('/analytics/care-gap-trends'),
          api.get('/analytics/top-conditions'),
          api.get('/analytics/provider-performance')
        ]);
        
        // Reverse trends so chronological order
        setTrends(trendRes.data.reverse());
        setConditions(condRes.data);
        setProviders(provRes.data);
      } catch (error) {
        console.error("Failed to fetch analytics", error);
      } finally {
        setLoading(false);
      }
    };

    fetchAnalytics();
  }, []);

  if (loading) return <div>Loading analytics...</div>;

  return (
    <div>
      <h1 style={{ marginBottom: '2rem' }}>Population Health Analytics</h1>

      <div className="grid grid-cols-2 gap-6" style={{ marginBottom: '2rem' }}>
        <div className="card">
          <h2>Care Gap Trends (6 Months)</h2>
          <div style={{ height: '300px' }}>
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={trends} margin={{ top: 20, right: 30, left: 0, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} />
                <XAxis dataKey="month" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Line type="monotone" dataKey="opened" stroke="var(--risk-high)" name="Gaps Opened" strokeWidth={2} />
                <Line type="monotone" dataKey="closed" stroke="var(--risk-low)" name="Gaps Closed" strokeWidth={2} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="card">
          <h2>Top Chronic Conditions</h2>
          <div style={{ height: '300px' }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={conditions} layout="vertical" margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" horizontal={false} />
                <XAxis type="number" />
                <YAxis dataKey="name" type="category" width={150} tick={{ fontSize: 12 }} />
                <Tooltip />
                <Bar dataKey="count" fill="var(--primary-color)" radius={[0, 4, 4, 0]} name="Patient Count" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      <div className="card">
        <h2>Provider Performance (Gap Closure Rate)</h2>
        <div className="table-container" style={{ marginTop: '1rem', border: 'none' }}>
          <table>
            <thead>
              <tr>
                <th>Provider Name</th>
                <th>Patient Panel</th>
                <th>Open Gaps</th>
                <th>Closed Gaps</th>
                <th>Closure Rate</th>
                <th>Performance</th>
              </tr>
            </thead>
            <tbody>
              {providers.map(p => (
                <tr key={p.provider_name}>
                  <td style={{ fontWeight: 500 }}>{p.provider_name}</td>
                  <td>{p.patient_count}</td>
                  <td>{p.open_gaps}</td>
                  <td>{p.closed_gaps}</td>
                  <td>{p.closure_rate}%</td>
                  <td>
                    <div style={{ width: '100%', backgroundColor: 'var(--bg-color)', height: '8px', borderRadius: '4px', overflow: 'hidden' }}>
                      <div 
                        style={{ 
                          height: '100%', 
                          width: `${p.closure_rate}%`, 
                          backgroundColor: p.closure_rate >= 70 ? 'var(--risk-low)' : p.closure_rate >= 40 ? 'var(--risk-moderate)' : 'var(--risk-high)'
                        }}
                      ></div>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default AnalyticsPage;
