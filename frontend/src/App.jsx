import { useState } from 'react';
import Dashboard from './Dashboard';
import MLDashboard from './MLDashboard';
import './App.css';

const schemas = {
  employees: ["employee_id", "name", "email", "department", "job_role", "hire_date", "location", "manager_id"],
  compensation: ["comp_id", "employee_id", "salary", "bonus", "stock_options", "effective_date"],
  performance: ["review_id", "employee_id", "review_date", "rating", "promotion_given", "manager_feedback_score"],
  workload: ["workload_id", "employee_id", "log_date", "weekly_hours", "overtime_hours", "sick_leaves_taken", "remote_days"],
  hr_tickets: ["ticket_id", "employee_id", "issue_date", "resolution_date", "category", "severity", "status", "satisfaction_score"],
  training: ["event_id", "employee_id", "training_name", "event_date", "completed", "score"]
};

function App() {
  const [activeTab, setActiveTab] = useState('upload'); // 'upload', 'dashboard', or 'ml'
  
  const [datasetType, setDatasetType] = useState('employees');
  const [file, setFile] = useState(null);
  const [csvHeaders, setCsvHeaders] = useState([]);
  const [mapping, setMapping] = useState({});
  const [uploadStatus, setUploadStatus] = useState(null);

  // Handle File Selection & Parse Headers
  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    setFile(selectedFile);
    setUploadStatus(null);
    setMapping({});

    if (selectedFile) {
      const reader = new FileReader();
      reader.onload = (event) => {
        const text = event.target.result;
        const firstLine = text.split('\n')[0];
        const headers = firstLine.split(',').map(h => h.trim().replace(/['"]/g, '').toLowerCase());
        setCsvHeaders(headers);
        
        // Auto-map exact matches for better UX
        const initialMapping = {};
        const requiredCols = schemas[datasetType];
        headers.forEach(header => {
          if (requiredCols.includes(header)) {
            initialMapping[header] = header;
          }
        });
        setMapping(initialMapping);
      };
      reader.readAsText(selectedFile.slice(0, 5000));
    } else {
      setCsvHeaders([]);
    }
  };

  const handleDatasetTypeChange = (e) => {
    setDatasetType(e.target.value);
    setMapping({});
  };

  const handleMappingChange = (requiredCol, csvCol) => {
    setMapping(prev => {
      const newMapping = { ...prev };
      
      if (!csvCol) {
        Object.keys(newMapping).forEach(key => {
          if (newMapping[key] === requiredCol) delete newMapping[key];
        });
        return newMapping;
      }
      
      newMapping[csvCol] = requiredCol;
      return newMapping;
    });
  };

  const handleUpload = async () => {
    if (!file) return;

    setUploadStatus("Uploading...");

    const formData = new FormData();
    formData.append("file", file);
    formData.append("column_mapping", JSON.stringify(mapping));

    try {
      const response = await fetch(`http://localhost:8000/api/upload/${datasetType}`, {
        method: "POST",
        body: formData,
      });
      
      const data = await response.json();
      
      if (response.ok) {
        if (data.rows_inserted === 0 && data.errors && data.errors.length > 0) {
          setUploadStatus(`Failed. 0 rows inserted. Database Error: ${data.errors[0].issue}`);
        } else {
          setUploadStatus(`Success! Inserted ${data.rows_inserted} rows. Health Score: ${data.dataset_health_score}`);
        }
      } else {
        setUploadStatus(`Error: ${JSON.stringify(data.detail)}`);
      }
    } catch (error) {
      setUploadStatus(`Error connecting to server: ${error.message}`);
    }
  };

  const requiredColumns = schemas[datasetType];

  return (
    <div className="app-layout">
      <aside className="sidebar">
        <div className="sidebar-logo">
          <h2>AttritionX</h2>
        </div>
        <nav className="sidebar-nav">
          <button 
            className={`nav-btn ${activeTab === 'upload' ? 'active' : ''}`}
            onClick={() => setActiveTab('upload')}
          >
            Data Importer
          </button>
          <button 
            className={`nav-btn ${activeTab === 'dashboard' ? 'active' : ''}`}
            onClick={() => setActiveTab('dashboard')}
          >
            HR EDA Dashboard
          </button>
          <button 
            className={`nav-btn ${activeTab === 'ml' ? 'active' : ''}`}
            onClick={() => setActiveTab('ml')}
          >
            AI Attrition Engine
          </button>
        </nav>
      </aside>

      <main className="main-content">
        {activeTab === 'dashboard' ? (
          <Dashboard />
        ) : activeTab === 'ml' ? (
          <MLDashboard />
        ) : (
          <div className="container">
            <header className="header">
              <h1>HR Data Importer</h1>
              <p>Map your HR CSV datasets directly into the Attrition Platform</p>
            </header>

            <div className="upload-card">
              <div className="form-group">
                <label>1. Select HR Dataset Type</label>
                <select value={datasetType} onChange={handleDatasetTypeChange}>
                  {Object.keys(schemas).map(type => (
                    <option key={type} value={type}>{type.toUpperCase()}</option>
                  ))}
                </select>
              </div>

              <div className="form-group">
                <label>2. Upload HR CSV File</label>
                <input type="file" accept=".csv" onChange={handleFileChange} />
              </div>

              {csvHeaders.length > 0 && (
                <div className="mapping-section">
                  <h3>3. Map Your Columns</h3>
                  <p className="subtitle">Match required database schema attributes to your CSV headers.</p>
                  
                  <div className="mapper-grid">
                    <div className="mapper-header">Required DB Column</div>
                    <div className="mapper-header">Your CSV Column</div>
                    
                    {requiredColumns.map(reqCol => {
                      const mappedCsvHeader = Object.keys(mapping).find(key => mapping[key] === reqCol) || "";
                      
                      return (
                        <div key={reqCol} className="mapper-row">
                          <div className="req-col-name">{reqCol} <span className="asterisk">*</span></div>
                          <select 
                            value={mappedCsvHeader}
                            onChange={(e) => handleMappingChange(reqCol, e.target.value)}
                          >
                            <option value="">-- Ignore / Use Default --</option>
                            {csvHeaders.map(header => (
                              <option key={header} value={header}>{header}</option>
                            ))}
                          </select>
                        </div>
                      );
                    })}
                  </div>

                  <button 
                    className="upload-button" 
                    onClick={handleUpload}
                    disabled={uploadStatus === "Uploading..."}
                  >
                    {uploadStatus === "Uploading..." ? "Processing..." : "Run Upload & Cleaning Pipeline"}
                  </button>
                  
                  {uploadStatus && (
                    <div className={`status-message ${uploadStatus.includes("Error") || uploadStatus.includes("Failed") ? "error" : "success"}`}>
                      {uploadStatus}
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

export default App;
