import React, { useState, useEffect } from 'react';
import { Brain, RefreshCw, Activity, Users, Target, ShieldAlert, UserCheck, DollarSign, Clock } from 'lucide-react';
import './App.css';

const MLDashboard = () => {
  const [loading, setLoading] = useState(false);
  const [statusMsg, setStatusMsg] = useState("");
  const [employees, setEmployees] = useState([]);
  const [selectedEmployee, setSelectedEmployee] = useState("");
  const [recommendations, setRecommendations] = useState(null);

  useEffect(() => {
    fetchEmployees();
  }, []);

  const fetchEmployees = async () => {
    try {
      const res = await fetch('http://localhost:8000/api/models/employees');
      const data = await res.json();
      setEmployees(data.employees || data.customers || []);
    } catch (err) {
      console.error("Failed to fetch employees:", err);
    }
  };

  const handleTrainModels = async (endpoint, actionName) => {
    setLoading(true);
    setStatusMsg(`Running ${actionName}...`);
    try {
      const res = await fetch(`http://localhost:8000/api/models/${endpoint}`, { method: 'POST' });
      const data = await res.json();
      setStatusMsg(data.message || "Success!");
      
      if (endpoint.includes('calculate-features') || endpoint === 'predict') {
        await fetchEmployees();
      }
    } catch (err) {
      setStatusMsg(`Error: ${err.message}`);
    }
    setLoading(false);
  };

  const handleFetchRecommendations = async (empId) => {
    if (!empId) return;
    setSelectedEmployee(empId);
    setRecommendations(null);
    try {
      const res = await fetch(`http://localhost:8000/api/models/recommendations/${empId}`);
      const data = await res.json();
      setRecommendations(data);
    } catch (err) {
      console.error("Failed to fetch HR recommendations:", err);
    }
  };

  const getPriorityColor = (priority) => {
    switch (priority) {
      case 'CRITICAL': return '#EF4444'; // Red
      case 'HIGH': return '#F59E0B';     // Orange
      case 'MEDIUM': return '#3B82F6';   // Blue
      default: return '#10B981';         // Green
    }
  };

  return (
    <div className="ml-dashboard-container">
      <header className="ml-header">
        <h2><Brain className="inline-icon" /> AI Attrition & Retention Engine</h2>
        <p>Train HR machine learning models, predict flight risk, and generate targeted employee retention strategies.</p>
      </header>

      {/* Control Panel */}
      <div className="ml-control-panel">
        <h3>1. Engine Controls</h3>
        <div className="control-buttons">
          <button 
            onClick={() => handleTrainModels('../ml/calculate-features', 'HR Feature Store Compilation')}
            disabled={loading}
            className="btn-secondary"
            style={{ borderColor: '#4F46E5', color: '#4F46E5' }}
          >
            <Activity size={18} /> Compile HR Feature Store
          </button>

          <button 
            onClick={() => handleTrainModels('train-segmentation', 'Risk Cohort K-Means Training')}
            disabled={loading}
            className="btn-primary"
          >
            <Users size={18} /> Train Risk Cohorts (K-Means)
          </button>
          
          <button 
            onClick={() => handleTrainModels('train-attrition', 'XGBoost Attrition Training')}
            disabled={loading}
            className="btn-primary"
          >
            <Target size={18} /> Train Attrition Model (XGBoost)
          </button>
          
          <button 
            onClick={() => handleTrainModels('predict', 'Attrition Inference Engine')}
            disabled={loading}
            className="btn-secondary"
          >
            <RefreshCw size={18} /> Generate Attrition Predictions
          </button>
        </div>
        
        {statusMsg && (
          <div className={`status-banner ${loading ? 'pulsing' : ''}`}>
            {statusMsg}
          </div>
        )}
      </div>

      {/* Employee Insights */}
      <div className="ml-insights-panel">
        <h3>2. Employee Intelligence & Retention Card</h3>
        
        <div className="employee-selector">
          <label>Select Employee Profile:</label>
          <select 
            value={selectedEmployee} 
            onChange={(e) => handleFetchRecommendations(e.target.value)}
          >
            <option value="">-- Choose an Employee --</option>
            {employees.map(e => (
              <option key={e} value={e}>{e.toUpperCase()}</option>
            ))}
          </select>
        </div>

        {recommendations && (
          <div className="recommendations-display">
            <div className="rec-header">
              <h4>Profile: {recommendations.employee_id.toUpperCase()}</h4>
              <span className="segment-badge">{recommendations.segment || 'Core Employee'}</span>
            </div>

            {/* Profile Overview Details */}
            <div className="profile-details-grid" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: '1rem', marginBottom: '1.5rem', background: '#F9FAFB', padding: '1rem', borderRadius: '8px' }}>
              <div><UserCheck size={16} inline /> <strong>Dept:</strong> {recommendations.department}</div>
              <div><Activity size={16} inline /> <strong>Role:</strong> {recommendations.job_role}</div>
              <div><Clock size={16} inline /> <strong>Tenure:</strong> {recommendations.tenure_years} yrs</div>
              <div><DollarSign size={16} inline /> <strong>Salary:</strong> ${recommendations.salary?.toLocaleString()}</div>
              <div><DollarSign size={16} inline /> <strong>Replacement Cost:</strong> ${recommendations.replacement_cost?.toLocaleString()}</div>
            </div>

            {/* Score Gauges */}
            <div className="score-cards">
              <div className="score-card">
                <div className="score-title"><Target size={16} /> Attrition Probability</div>
                <div className="score-value" style={{ color: recommendations.attrition_risk_percentage > 50 ? '#EF4444' : '#10B981' }}>
                  {recommendations.attrition_risk_percentage}%
                </div>
                <div className="progress-bar-bg">
                  <div 
                    className="progress-bar-fill red" 
                    style={{ width: `${Math.min(100, Math.max(0, recommendations.attrition_risk_percentage))}%` }}
                  ></div>
                </div>
              </div>
              
              <div className="score-card">
                <div className="score-title"><Activity size={16} /> Satisfaction Score</div>
                <div className="score-value">
                  {recommendations.satisfaction_score} <span>/ 100</span>
                </div>
                <div className="progress-bar-bg">
                  <div 
                    className="progress-bar-fill green" 
                    style={{ width: `${Math.min(100, Math.max(0, recommendations.satisfaction_score))}%` }}
                  ></div>
                </div>
              </div>
            </div>

            {/* Action Plan */}
            <div className="action-list">
              <h4>Recommended HR Action Plan:</h4>
              {recommendations.recommendations.map((rec, idx) => (
                <div key={idx} className="action-item" style={{ borderLeftColor: getPriorityColor(rec.priority) }}>
                  <div className="action-priority" style={{ color: getPriorityColor(rec.priority) }}>
                    <ShieldAlert size={14} /> {rec.priority} PRIORITY
                  </div>
                  <div className="action-text">{rec.action}</div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default MLDashboard;
