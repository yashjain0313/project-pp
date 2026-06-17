import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Stethoscope } from 'lucide-react';

const LoginPage = () => {
  const [email, setEmail] = useState('provider@caresync.com');
  const [password, setPassword] = useState('demo123');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      await login(email, password);
      navigate('/dashboard');
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to login');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', backgroundColor: 'var(--bg-color)' }}>
      <div className="card" style={{ width: '100%', maxWidth: '400px', padding: '2.5rem' }}>
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', marginBottom: '2rem' }}>
          <div style={{ backgroundColor: 'var(--primary-light)', color: 'var(--primary-color)', padding: '1rem', borderRadius: '50%', marginBottom: '1rem' }}>
            <Stethoscope size={32} />
          </div>
          <h1 style={{ fontSize: '1.5rem', marginBottom: '0.5rem', textAlign: 'center' }}>Welcome to CareSync</h1>
          <p style={{ color: 'var(--text-secondary)', textAlign: 'center', fontSize: '0.875rem' }}>
            Patient Care Gap Analysis & Risk Stratification
          </p>
        </div>

        {error && (
          <div style={{ backgroundColor: 'var(--risk-critical-bg)', color: 'var(--risk-critical)', padding: '0.75rem', borderRadius: 'var(--radius-md)', marginBottom: '1.5rem', fontSize: '0.875rem', textAlign: 'center' }}>
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label className="form-label">Email</label>
            <input 
              type="email" 
              className="form-input" 
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>
          <div className="form-group">
            <label className="form-label">Password</label>
            <input 
              type="password" 
              className="form-input" 
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>
          <button 
            type="submit" 
            className="btn btn-primary" 
            style={{ width: '100%', marginTop: '1rem', padding: '0.75rem' }}
            disabled={loading}
          >
            {loading ? 'Signing in...' : 'Sign In'}
          </button>
        </form>

        <div style={{ marginTop: '2rem', paddingTop: '1.5rem', borderTop: '1px solid var(--border-color)', fontSize: '0.75rem', color: 'var(--text-secondary)', textAlign: 'center' }}>
          <p>Demo Accounts:</p>
          <div style={{ display: 'flex', justifyContent: 'center', gap: '1rem', marginTop: '0.5rem' }}>
            <button 
              onClick={() => { setEmail('provider@caresync.com'); setPassword('demo123'); }}
              style={{ background: 'none', border: 'none', color: 'var(--primary-color)', cursor: 'pointer', fontSize: '0.75rem' }}
            >
              Provider
            </button>
            <button 
              onClick={() => { setEmail('admin@caresync.com'); setPassword('demo123'); }}
              style={{ background: 'none', border: 'none', color: 'var(--primary-color)', cursor: 'pointer', fontSize: '0.75rem' }}
            >
              Admin
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;
