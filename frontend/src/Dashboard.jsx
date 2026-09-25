import React, { useState, useEffect } from 'react';
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ComposedChart, Line 
} from 'recharts';
import { Users, AlertTriangle, DollarSign, Smile } from 'lucide-react';
import './App.css';

const Dashboard = () => {
  const [kpis, setKpis] = useState(null);
  const [deptAttrition, setDeptAttrition] = useState([]);
  const [overtimeSat, setOvertimeSat] = useState([]);
  const [compTrends, setCompTrends] = useState([]);
  const [hrTickets, setHrTickets] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        const [kpiRes, deptRes, otRes, compRes, ticketRes] = await Promise.all([
          fetch('http://localhost:8000/api/eda/kpis'),
          fetch('http://localhost:8000/api/eda/department-attrition'),
          fetch('http://localhost:8000/api/eda/overtime-vs-satisfaction'),
          fetch('http://localhost:8000/api/eda/compensation-trends'),
          fetch('http://localhost:8000/api/eda/hr-ticket-analysis')
        ]);

        setKpis(await kpiRes.json());
        setDeptAttrition(await deptRes.json());
        setOvertimeSat(await otRes.json());
        setCompTrends(await compRes.json());
        setHrTickets(await ticketRes.json());
      } catch (error) {
        console.error("Failed to fetch HR dashboard data:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchDashboardData();
  }, []);

  if (loading) return <div className="loading">Loading HR Executive Dashboard...</div>;

  return (
    <div className="dashboard-container">
      <h2 className="dashboard-title">HR Executive Overview & Attrition EDA</h2>
      
      {/* KPI Cards */}
      <div className="kpi-grid">
        <div className="kpi-card">
          <div className="kpi-icon-wrapper blue"><Users size={24} /></div>
          <div className="kpi-details">
            <p className="kpi-label">Total Headcount</p>
            <h3 className="kpi-value">{kpis?.total_headcount || 0}</h3>
          </div>
        </div>
        <div className="kpi-card">
          <div className="kpi-icon-wrapper orange"><AlertTriangle size={24} /></div>
          <div className="kpi-details">
            <p className="kpi-label">Org Attrition Risk Rate</p>
            <h3 className="kpi-value">{kpis?.org_attrition_rate || 0}%</h3>
          </div>
        </div>
        <div className="kpi-card">
          <div className="kpi-icon-wrapper green"><DollarSign size={24} /></div>
          <div className="kpi-details">
            <p className="kpi-label">Average Org Salary</p>
            <h3 className="kpi-value">${kpis?.average_salary?.toLocaleString() || 0}</h3>
          </div>
        </div>
        <div className="kpi-card">
          <div className="kpi-icon-wrapper purple"><Smile size={24} /></div>
          <div className="kpi-details">
            <p className="kpi-label">Org Satisfaction Score</p>
            <h3 className="kpi-value">{kpis?.avg_satisfaction_score || 0} <span>/ 100</span></h3>
          </div>
        </div>
      </div>

      {/* Charts Grid */}
      <div className="charts-grid">
        
        {/* Chart 1: Department-wise Flight Risk */}
        <div className="chart-card">
          <h3>Department-wise Flight Risk Rate (%)</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={deptAttrition}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E5E7EB" />
              <XAxis dataKey="department" stroke="#6B7280" fontSize={12} tickLine={false} />
              <YAxis stroke="#6B7280" fontSize={12} tickLine={false} axisLine={false} tickFormatter={(val) => `${val}%`} />
              <Tooltip formatter={(value) => [`${value}%`, "Flight Risk Rate"]} />
              <Bar dataKey="flight_risk_pct" fill="#EF4444" radius={[4, 4, 0, 0]} barSize={40} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Chart 2: Overtime Hours vs. Satisfaction Score */}
        <div className="chart-card">
          <h3>Overtime Hours vs. Employee Satisfaction Score</h3>
          <ResponsiveContainer width="100%" height={300}>
            <ComposedChart data={overtimeSat}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E5E7EB" />
              <XAxis dataKey="department" stroke="#6B7280" fontSize={12} tickLine={false} />
              <YAxis yAxisId="left" stroke="#6B7280" fontSize={12} tickLine={false} axisLine={false} />
              <YAxis yAxisId="right" orientation="right" domain={[0, 100]} stroke="#6B7280" fontSize={12} tickLine={false} axisLine={false} />
              <Tooltip />
              <Legend />
              <Bar yAxisId="left" dataKey="avg_overtime" fill="#F59E0B" name="Avg Weekly Overtime (hrs)" radius={[4, 4, 0, 0]} barSize={35} />
              <Line yAxisId="right" type="monotone" dataKey="avg_satisfaction" stroke="#10B981" strokeWidth={3} name="Avg Satisfaction Score" />
            </ComposedChart>
          </ResponsiveContainer>
        </div>

        {/* Chart 3: Salary Growth / Avg Salary by Department */}
        <div className="chart-card">
          <h3>Average Compensation by Department</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={compTrends}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E5E7EB" />
              <XAxis dataKey="department" stroke="#6B7280" fontSize={12} tickLine={false} />
              <YAxis stroke="#6B7280" fontSize={12} tickLine={false} axisLine={false} tickFormatter={(val) => `$${val}`} />
              <Tooltip formatter={(value) => [`$${value.toLocaleString()}`, "Avg Salary"]} />
              <Bar dataKey="avg_salary" fill="#6366F1" radius={[4, 4, 0, 0]} barSize={40} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Chart 4: HR Complaint Volume & CSAT by Severity */}
        <div className="chart-card">
          <h3>HR Complaint Volume & Satisfaction by Severity</h3>
          <ResponsiveContainer width="100%" height={300}>
            <ComposedChart data={hrTickets}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E5E7EB" />
              <XAxis dataKey="severity" stroke="#6B7280" fontSize={12} tickLine={false} />
              <YAxis yAxisId="left" stroke="#6B7280" fontSize={12} tickLine={false} axisLine={false} />
              <YAxis yAxisId="right" orientation="right" domain={[0, 5]} stroke="#6B7280" fontSize={12} tickLine={false} axisLine={false} />
              <Tooltip />
              <Legend />
              <Bar yAxisId="left" dataKey="volume" fill="#8B5CF6" name="Ticket Volume" radius={[4, 4, 0, 0]} barSize={40} />
              <Line yAxisId="right" type="monotone" dataKey="avg_csat" stroke="#EC4899" strokeWidth={3} name="Avg Ticket CSAT (1-5)" />
            </ComposedChart>
          </ResponsiveContainer>
        </div>

      </div>
    </div>
  );
};

export default Dashboard;
