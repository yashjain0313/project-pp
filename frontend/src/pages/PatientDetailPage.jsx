import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import api from '../api';
import { ArrowLeft, Activity, User, Heart, ShieldAlert, CheckCircle, Clock } from 'lucide-react';

const PatientDetailPage = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [patient, setPatient] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('gaps');

  useEffect(() => {
    fetchPatient();
  }, [id]);

  const fetchPatient = async () => {
    try {
      const res = await api.get(`/patients/${id}`);
      setPatient(res.data);
    } catch (error) {
      console.error("Failed to fetch patient", error);
    } finally {
      setLoading(false);
    }
  };

  const handleCloseGap = async (gapId) => {
    try {
      await api.put(`/care-gaps/${gapId}/close`, { resolution_notes: 'Closed via dashboard' });
      fetchPatient(); // Refresh data
    } catch (error) {
      console.error("Failed to close gap", error);
    }
  };

  const handleAnalyze = async () => {
    try {
      await api.post(`/care-gaps/analyze/${id}`);
      fetchPatient(); // Refresh data
    } catch (error) {
      console.error("Failed to analyze", error);
    }
  };

  if (loading) return <div>Loading patient details...</div>;
  if (!patient) return <div>Patient not found</div>;

  return (
    <div>
      <button 
        className="btn btn-outline" 
        style={{ marginBottom: '1.5rem', border: 'none', padding: 0 }}
        onClick={() => navigate('/patients')}
      >
        <ArrowLeft size={16} /> Back to Patients
      </button>

      {/* Header Profile Card */}
      <div className="card" style={{ marginBottom: '2rem', display: 'flex', gap: '2rem', alignItems: 'center' }}>
        <div style={{ width: '80px', height: '80px', borderRadius: '50%', backgroundColor: 'var(--primary-light)', color: 'var(--primary-color)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '2rem', fontWeight: 'bold' }}>
          {patient.first_name.charAt(0)}{patient.last_name.charAt(0)}
        </div>
        <div style={{ flex: 1 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <div>
              <h1 style={{ marginBottom: '0.25rem' }}>{patient.first_name} {patient.last_name}</h1>
              <div style={{ color: 'var(--text-secondary)', display: 'flex', gap: '1rem', fontSize: '0.875rem' }}>
                <span>DOB: {new Date(patient.date_of_birth).toLocaleDateString()} ({patient.age}y)</span>
                <span>•</span>
                <span style={{ textTransform: 'capitalize' }}>Gender: {patient.gender}</span>
                <span>•</span>
                <span>PCP: {patient.provider_name}</span>
              </div>
            </div>
            <div style={{ textAlign: 'right' }}>
              <div style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', marginBottom: '0.25rem' }}>Risk Score</div>
              <div style={{ fontSize: '1.5rem', fontWeight: 'bold', color: `var(--risk-${patient.risk_level})` }}>
                {patient.risk_score} / 100
              </div>
              <span className={`badge risk-${patient.risk_level}`} style={{ marginTop: '0.25rem' }}>
                {patient.risk_level} Risk
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div style={{ display: 'flex', gap: '1rem', borderBottom: '1px solid var(--border-color)', marginBottom: '1.5rem' }}>
        <button 
          className={`btn ${activeTab === 'gaps' ? 'btn-outline' : ''}`}
          style={{ border: 'none', borderRadius: '0', borderBottom: activeTab === 'gaps' ? '2px solid var(--primary-color)' : '2px solid transparent', color: activeTab === 'gaps' ? 'var(--primary-color)' : 'var(--text-secondary)' }}
          onClick={() => setActiveTab('gaps')}
        >
          Care Gaps ({patient.care_gaps.filter(g => g.status !== 'closed').length})
        </button>
        <button 
          className={`btn ${activeTab === 'conditions' ? 'btn-outline' : ''}`}
          style={{ border: 'none', borderRadius: '0', borderBottom: activeTab === 'conditions' ? '2px solid var(--primary-color)' : '2px solid transparent', color: activeTab === 'conditions' ? 'var(--primary-color)' : 'var(--text-secondary)' }}
          onClick={() => setActiveTab('conditions')}
        >
          Conditions ({patient.conditions.length})
        </button>
        <button 
          className={`btn ${activeTab === 'meds' ? 'btn-outline' : ''}`}
          style={{ border: 'none', borderRadius: '0', borderBottom: activeTab === 'meds' ? '2px solid var(--primary-color)' : '2px solid transparent', color: activeTab === 'meds' ? 'var(--primary-color)' : 'var(--text-secondary)' }}
          onClick={() => setActiveTab('meds')}
        >
          Medications ({patient.medications.length})
        </button>
        <button 
          className={`btn ${activeTab === 'encounters' ? 'btn-outline' : ''}`}
          style={{ border: 'none', borderRadius: '0', borderBottom: activeTab === 'encounters' ? '2px solid var(--primary-color)' : '2px solid transparent', color: activeTab === 'encounters' ? 'var(--primary-color)' : 'var(--text-secondary)' }}
          onClick={() => setActiveTab('encounters')}
        >
          History
        </button>
      </div>

      {/* Tab Content */}
      <div className="tab-content">
        {activeTab === 'gaps' && (
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
              <h2>Identified Care Gaps</h2>
              <button className="btn btn-primary" onClick={handleAnalyze}>
                <Activity size={16} /> Run Analysis
              </button>
            </div>
            
            {patient.care_gaps.length === 0 ? (
              <div className="card" style={{ textAlign: 'center', padding: '3rem' }}>
                <CheckCircle size={48} color="var(--risk-low)" style={{ marginBottom: '1rem' }} />
                <h3>No Care Gaps</h3>
                <p style={{ color: 'var(--text-secondary)' }}>This patient is up to date with all preventive care guidelines.</p>
              </div>
            ) : (
              <div className="grid gap-4">
                {patient.care_gaps.map(gap => (
                  <div key={gap.id} className="card" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', opacity: gap.status === 'closed' ? 0.6 : 1 }}>
                    <div>
                      <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center', marginBottom: '0.25rem' }}>
                        {gap.status === 'overdue' && <span className="badge risk-critical">Overdue</span>}
                        {gap.status === 'closed' && <span className="badge risk-low">Closed</span>}
                        {gap.priority === 'high' && gap.status !== 'closed' && <span className="badge risk-high">High Priority</span>}
                        <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                          {gap.gap_type}
                        </span>
                      </div>
                      <h3 style={{ fontSize: '1.125rem', marginBottom: '0.25rem' }}>{gap.title}</h3>
                      <p style={{ color: 'var(--text-secondary)', fontSize: '0.875rem' }}>{gap.description}</p>
                      
                      <div style={{ display: 'flex', gap: '1rem', marginTop: '0.5rem', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                        <span style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                          <Clock size={14} /> 
                          {gap.status === 'closed' ? `Closed: ${new Date(gap.closed_date).toLocaleDateString()}` : `Due: ${new Date(gap.due_date).toLocaleDateString()}`}
                        </span>
                      </div>
                    </div>
                    
                    {gap.status !== 'closed' && (
                      <button 
                        className="btn btn-outline" 
                        style={{ color: 'var(--primary-color)', borderColor: 'var(--primary-color)' }}
                        onClick={() => handleCloseGap(gap.id)}
                      >
                        <CheckCircle size={16} /> Mark Closed
                      </button>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {activeTab === 'conditions' && (
          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th>Condition</th>
                  <th>ICD-10 Code</th>
                  <th>Status</th>
                  <th>Diagnosed</th>
                  <th>Type</th>
                </tr>
              </thead>
              <tbody>
                {patient.conditions.map(c => (
                  <tr key={c.id}>
                    <td style={{ fontWeight: 500 }}>{c.name}</td>
                    <td>{c.icd_code}</td>
                    <td><span className={`badge ${c.status === 'active' ? 'risk-low' : 'risk-moderate'}`}>{c.status}</span></td>
                    <td>{new Date(c.diagnosed_date).toLocaleDateString()}</td>
                    <td>{c.is_chronic ? 'Chronic' : 'Acute'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {activeTab === 'meds' && (
          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th>Medication</th>
                  <th>Dosage</th>
                  <th>Frequency</th>
                  <th>Status</th>
                  <th>Start Date</th>
                </tr>
              </thead>
              <tbody>
                {patient.medications.map(m => (
                  <tr key={m.id}>
                    <td style={{ fontWeight: 500 }}>{m.name}</td>
                    <td>{m.dosage}</td>
                    <td>{m.frequency}</td>
                    <td><span className={`badge ${m.is_active ? 'risk-low' : 'risk-moderate'}`}>{m.is_active ? 'Active' : 'Discontinued'}</span></td>
                    <td>{new Date(m.start_date).toLocaleDateString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {activeTab === 'encounters' && (
          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Type</th>
                  <th>Provider</th>
                  <th>Notes</th>
                </tr>
              </thead>
              <tbody>
                {patient.encounters.map(e => (
                  <tr key={e.id}>
                    <td>{new Date(e.encounter_date).toLocaleDateString()}</td>
                    <td style={{ fontWeight: 500 }}>{e.encounter_type}</td>
                    <td>{e.provider_name}</td>
                    <td style={{ maxWidth: '300px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                      {e.notes}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};

export default PatientDetailPage;
