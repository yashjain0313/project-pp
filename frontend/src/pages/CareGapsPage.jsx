import React, { useState, useEffect } from 'react';
import api from '../api';
import { Activity, Clock, CheckCircle } from 'lucide-react';

const CareGapsPage = () => {
  const [gaps, setGaps] = useState([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState('open,overdue');

  useEffect(() => {
    fetchGaps();
  }, [statusFilter]);

  const fetchGaps = async () => {
    setLoading(true);
    try {
      // In a real app we'd pass comma separated status, but our API takes one.
      // So we'll fetch all and filter in frontend for simplicity of this demo.
      const res = await api.get('/care-gaps?limit=500');
      
      let filtered = res.data;
      if (statusFilter !== 'all') {
        const statuses = statusFilter.split(',');
        filtered = res.data.filter(g => statuses.includes(g.status));
      }
      
      setGaps(filtered);
    } catch (error) {
      console.error("Failed to fetch care gaps", error);
    } finally {
      setLoading(false);
    }
  };

  const handleCloseGap = async (gapId) => {
    try {
      await api.put(`/care-gaps/${gapId}/close`, { resolution_notes: 'Closed via dashboard' });
      fetchGaps(); // Refresh data
    } catch (error) {
      console.error("Failed to close gap", error);
    }
  };

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
        <h1>Care Gaps Management</h1>
        
        <select 
          className="form-input" 
          style={{ width: '200px' }}
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
        >
          <option value="open,overdue">Open & Overdue</option>
          <option value="open">Open Only</option>
          <option value="overdue">Overdue Only</option>
          <option value="closed">Closed Only</option>
          <option value="all">All Care Gaps</option>
        </select>
      </div>

      <div className="table-container">
        {loading ? (
          <div style={{ padding: '2rem', textAlign: 'center' }}>Loading care gaps...</div>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Patient</th>
                <th>Gap Title</th>
                <th>Type</th>
                <th>Priority</th>
                <th>Due Date</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {gaps.length === 0 ? (
                <tr>
                  <td colSpan="7" style={{ textAlign: 'center', padding: '2rem' }}>No care gaps found</td>
                </tr>
              ) : (
                gaps.map(gap => (
                  <tr key={gap.id}>
                    <td style={{ fontWeight: 500 }}>
                      <a href={`/patients/${gap.patient_id}`} style={{ color: 'var(--text-primary)' }}>
                        {gap.patient_name}
                      </a>
                    </td>
                    <td>{gap.title}</td>
                    <td style={{ textTransform: 'capitalize' }}>{gap.gap_type}</td>
                    <td>
                      <span className={`badge risk-${gap.priority === 'high' ? 'high' : gap.priority === 'medium' ? 'moderate' : 'low'}`}>
                        {gap.priority}
                      </span>
                    </td>
                    <td>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                        <Clock size={14} color="var(--text-muted)" />
                        {new Date(gap.due_date).toLocaleDateString()}
                      </div>
                    </td>
                    <td>
                      <span className={`badge risk-${gap.status === 'closed' ? 'low' : gap.status === 'overdue' ? 'critical' : 'moderate'}`}>
                        {gap.status}
                      </span>
                    </td>
                    <td>
                      {gap.status !== 'closed' && (
                        <button 
                          className="btn btn-outline" 
                          style={{ padding: '0.25rem 0.5rem', fontSize: '0.75rem', color: 'var(--primary-color)', borderColor: 'var(--primary-color)' }}
                          onClick={() => handleCloseGap(gap.id)}
                        >
                          <CheckCircle size={14} /> Close
                        </button>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
};

export default CareGapsPage;
