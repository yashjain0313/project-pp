import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../api';
import { Search } from 'lucide-react';

const PatientsPage = () => {
  const [patients, setPatients] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [riskFilter, setRiskFilter] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    fetchPatients();
  }, [search, riskFilter]);

  const fetchPatients = async () => {
    setLoading(true);
    try {
      let url = '/patients?limit=50';
      if (search) url += `&search=${search}`;
      if (riskFilter) url += `&risk_level=${riskFilter}`;
      
      const res = await api.get(url);
      setPatients(res.data);
    } catch (error) {
      console.error("Failed to fetch patients", error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
        <h1>Patients</h1>
        
        <div style={{ display: 'flex', gap: '1rem' }}>
          <div style={{ position: 'relative' }}>
            <div style={{ position: 'absolute', top: '50%', left: '0.75rem', transform: 'translateY(-50%)', color: 'var(--text-muted)' }}>
              <Search size={16} />
            </div>
            <input 
              type="text" 
              className="form-input" 
              placeholder="Search patients..." 
              style={{ paddingLeft: '2.25rem', width: '250px' }}
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>
          
          <select 
            className="form-input" 
            style={{ width: '150px' }}
            value={riskFilter}
            onChange={(e) => setRiskFilter(e.target.value)}
          >
            <option value="">All Risks</option>
            <option value="critical">Critical</option>
            <option value="high">High</option>
            <option value="moderate">Moderate</option>
            <option value="low">Low</option>
          </select>
        </div>
      </div>

      <div className="table-container">
        {loading ? (
          <div style={{ padding: '2rem', textAlign: 'center' }}>Loading patients...</div>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Patient Name</th>
                <th>DOB / Age</th>
                <th>Gender</th>
                <th>Risk Level</th>
                <th>Open Gaps</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {patients.length === 0 ? (
                <tr>
                  <td colSpan="6" style={{ textAlign: 'center', padding: '2rem' }}>No patients found</td>
                </tr>
              ) : (
                patients.map(patient => (
                  <tr key={patient.id} style={{ cursor: 'pointer' }} onClick={() => navigate(`/patients/${patient.id}`)}>
                    <td style={{ fontWeight: 500 }}>{patient.first_name} {patient.last_name}</td>
                    <td>{new Date(patient.date_of_birth).toLocaleDateString()} ({patient.age}y)</td>
                    <td style={{ textTransform: 'capitalize' }}>{patient.gender}</td>
                    <td>
                      <span className={`badge risk-${patient.risk_level}`}>
                        {patient.risk_level}
                      </span>
                    </td>
                    <td>
                      {patient.open_gaps_count > 0 ? (
                        <span style={{ color: 'var(--risk-critical)', fontWeight: 600 }}>{patient.open_gaps_count}</span>
                      ) : (
                        <span style={{ color: 'var(--text-muted)' }}>0</span>
                      )}
                    </td>
                    <td>
                      <button 
                        className="btn btn-outline" 
                        style={{ padding: '0.25rem 0.5rem', fontSize: '0.75rem' }}
                        onClick={(e) => {
                          e.stopPropagation();
                          navigate(`/patients/${patient.id}`);
                        }}
                      >
                        View
                      </button>
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

export default PatientsPage;
