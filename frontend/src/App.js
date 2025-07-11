import React, { useState, useRef, useEffect } from 'react';
import './App.css';

const App = () => {
  const [currentStep, setCurrentStep] = useState('upload');
  const [selectedFile, setSelectedFile] = useState(null);
  const [caseId, setCaseId] = useState(null);
  const [analysisResult, setAnalysisResult] = useState(null);
  const [enhancementResult, setEnhancementResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [cases, setCases] = useState([]);
  const fileInputRef = useRef(null);

  const backendUrl = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

  useEffect(() => {
    fetchCases();
  }, []);

  const fetchCases = async () => {
    try {
      const response = await fetch(`${backendUrl}/api/cases`);
      const data = await response.json();
      setCases(data.cases || []);
    } catch (error) {
      console.error('Error fetching cases:', error);
    }
  };

  const handleFileSelect = (event) => {
    const file = event.target.files[0];
    if (file) {
      setSelectedFile(file);
      setCurrentStep('preview');
    }
  };

  const handleDragOver = (event) => {
    event.preventDefault();
  };

  const handleDrop = (event) => {
    event.preventDefault();
    const file = event.dataTransfer.files[0];
    if (file && file.type.startsWith('image/')) {
      setSelectedFile(file);
      setCurrentStep('preview');
    }
  };

  const uploadImage = async () => {
    if (!selectedFile) return;

    setLoading(true);
    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
      const response = await fetch(`${backendUrl}/api/upload-image`, {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();
      
      if (response.ok) {
        setCaseId(data.case_id);
        setAnalysisResult(data);
        setCurrentStep('analysis');
        fetchCases();
      } else {
        alert('Upload failed: ' + data.detail);
      }
    } catch (error) {
      console.error('Upload error:', error);
      alert('Upload failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const enhanceFace = async (enhancementType = 'restoration') => {
    if (!caseId) return;

    setLoading(true);
    try {
      const response = await fetch(`${backendUrl}/api/enhance-face/${caseId}?enhancement_type=${enhancementType}`, {
        method: 'POST',
      });

      const data = await response.json();
      
      if (response.ok) {
        setEnhancementResult(data);
        setCurrentStep('results');
        fetchCases();
      } else {
        alert('Enhancement failed: ' + data.detail);
      }
    } catch (error) {
      console.error('Enhancement error:', error);
      alert('Enhancement failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const resetProcess = () => {
    setCurrentStep('upload');
    setSelectedFile(null);
    setCaseId(null);
    setAnalysisResult(null);
    setEnhancementResult(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const UploadStep = () => (
    <div className="upload-container">
      <div className="hero-section">
        <img 
          src="https://images.unsplash.com/photo-1626148749358-5b3b3f45b41a?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NTY2Njl8MHwxfHNlYXJjaHwxfHxmb3JlbnNpYyUyMGludmVzdGlnYXRpb258ZW58MHx8fGJsdWV8MTc1MjE5NTY0Mnww&ixlib=rb-4.1.0&q=85" 
          alt="Forensic Investigation" 
          className="hero-image"
        />
        <div className="hero-content">
          <h1>AI Face Reconstruction System</h1>
          <p>Advanced forensic tool for crime investigation and identity analysis</p>
        </div>
      </div>

      <div className="upload-section">
        <h2>Upload Evidence Image</h2>
        <p>Supports CCTV footage, mobile photos, and various image sources</p>
        
        <div 
          className="drop-zone"
          onDragOver={handleDragOver}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
        >
          <div className="drop-zone-content">
            <div className="upload-icon">📁</div>
            <p>Drag and drop your image here or click to select</p>
            <p className="file-types">Supported: JPG, PNG, JPEG, BMP</p>
          </div>
        </div>

        <input
          ref={fileInputRef}
          type="file"
          accept="image/*"
          onChange={handleFileSelect}
          style={{ display: 'none' }}
        />
      </div>

      {cases.length > 0 && (
        <div className="recent-cases">
          <h2>Recent Cases</h2>
          <div className="cases-grid">
            {cases.slice(0, 6).map((case_, index) => (
              <div key={index} className="case-card">
                <img src={case_.original_image} alt={`Case ${case_.case_id}`} />
                <div className="case-info">
                  <p>Case: {case_.case_id.substring(0, 8)}</p>
                  <p>Faces: {case_.face_count}</p>
                  <p>Status: {case_.status}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );

  const PreviewStep = () => (
    <div className="preview-container">
      <h2>Image Preview & Analysis</h2>
      
      <div className="preview-section">
        <img 
          src={URL.createObjectURL(selectedFile)} 
          alt="Selected" 
          className="preview-image"
        />
        
        <div className="image-info">
          <h3>Image Details</h3>
          <p><strong>Filename:</strong> {selectedFile.name}</p>
          <p><strong>Size:</strong> {(selectedFile.size / 1024 / 1024).toFixed(2)} MB</p>
          <p><strong>Type:</strong> {selectedFile.type}</p>
        </div>
      </div>

      <div className="action-buttons">
        <button onClick={resetProcess} className="btn-secondary">
          Cancel
        </button>
        <button onClick={uploadImage} className="btn-primary" disabled={loading}>
          {loading ? 'Analyzing...' : 'Analyze Image'}
        </button>
      </div>
    </div>
  );

  const AnalysisStep = () => (
    <div className="analysis-container">
      <h2>Face Detection Analysis</h2>
      
      <div className="analysis-results">
        <div className="result-card">
          <h3>Detection Results</h3>
          <div className="detection-stats">
            <div className="stat">
              <span className="stat-value">{analysisResult?.face_count || 0}</span>
              <span className="stat-label">Faces Detected</span>
            </div>
            <div className="stat">
              <span className={`stat-value ${analysisResult?.faces_detected ? 'success' : 'warning'}`}>
                {analysisResult?.faces_detected ? 'YES' : 'NO'}
              </span>
              <span className="stat-label">Faces Found</span>
            </div>
            <div className="stat">
              <span className="stat-value confidence">
                {analysisResult?.detection_confidence ? (analysisResult.detection_confidence * 100).toFixed(1) + '%' : 'N/A'}
              </span>
              <span className="stat-label">Detection Confidence</span>
            </div>
          </div>
        </div>

        <div className="original-image">
          <h3>Original Evidence</h3>
          <img src={URL.createObjectURL(selectedFile)} alt="Original" />
        </div>
      </div>

      <div className="enhancement-options">
        <h3>Government-Grade Enhancement Options</h3>
        <div className="enhancement-grid">
          <div className="enhancement-option">
            <button 
              onClick={() => enhanceFace('restoration')} 
              className="btn-primary"
              disabled={loading}
            >
              {loading ? 'Processing...' : 'Face Restoration'}
            </button>
            <p>High-fidelity restoration with identity preservation</p>
          </div>
          
          <div className="enhancement-option">
            <button 
              onClick={() => enhanceFace('super_resolution')} 
              className="btn-primary"
              disabled={loading}
            >
              {loading ? 'Processing...' : 'Super Resolution'}
            </button>
            <p>Ultra-high resolution enhancement</p>
          </div>
          
          <div className="enhancement-option">
            <button 
              onClick={() => enhanceFace('forensic_enhancement')} 
              className="btn-primary"
              disabled={loading}
            >
              {loading ? 'Processing...' : 'Forensic Enhancement'}
            </button>
            <p>Government-grade forensic reconstruction</p>
          </div>
          
          <div className="enhancement-option">
            <button 
              onClick={() => enhanceFace('identity_preservation')} 
              className="btn-primary"
              disabled={loading}
            >
              {loading ? 'Processing...' : 'Identity Preservation'}
            </button>
            <p>Maximum identity consistency for analysis</p>
          </div>
        </div>
      </div>

      <div className="action-buttons">
        <button onClick={resetProcess} className="btn-secondary">
          New Case
        </button>
      </div>
    </div>
  );

  const ResultsStep = () => (
    <div className="results-container">
      <h2>Enhancement Results</h2>
      
      <div className="comparison-section">
        <div className="comparison-images">
          <div className="image-container">
            <h3>Original Evidence</h3>
            <img src={URL.createObjectURL(selectedFile)} alt="Original" />
          </div>
          
          <div className="image-container">
            <h3>Enhanced Result</h3>
            <img src={enhancementResult?.enhanced_image} alt="Enhanced" />
          </div>
        </div>
        
        <div className="result-stats">
          <div className="stat-card">
            <h3>Analysis Report</h3>
            <div className="stat-row">
              <span>Confidence Score:</span>
              <span className="confidence-score">
                {(enhancementResult?.confidence_score * 100).toFixed(1)}%
              </span>
            </div>
            <div className="stat-row">
              <span>Method Used:</span>
              <span>{enhancementResult?.method_used}</span>
            </div>
            <div className="stat-row">
              <span>Case ID:</span>
              <span>{caseId}</span>
            </div>
          </div>
        </div>
      </div>

      <div className="action-buttons">
        <button onClick={resetProcess} className="btn-secondary">
          New Case
        </button>
        <button className="btn-primary">
          Export Evidence
        </button>
      </div>
    </div>
  );

  return (
    <div className="App">
      <nav className="navbar">
        <div className="nav-content">
          <h1>AI Face Reconstruction</h1>
          <div className="nav-links">
            <span className="nav-link">Forensic Analysis</span>
            <span className="nav-link">Case Management</span>
            <span className="nav-link">Evidence Export</span>
          </div>
        </div>
      </nav>

      <main className="main-content">
        {currentStep === 'upload' && <UploadStep />}
        {currentStep === 'preview' && <PreviewStep />}
        {currentStep === 'analysis' && <AnalysisStep />}
        {currentStep === 'results' && <ResultsStep />}
      </main>

      <footer className="footer">
        <p>&copy; 2025 AI Face Reconstruction System - For Law Enforcement Use</p>
      </footer>
    </div>
  );
};

export default App;