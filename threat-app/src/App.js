import React, { useState } from 'react';
import './App.css';

function App() {
  const [vulnScore, setVulnScore] = useState(0);
  const [assessment, setAssessment] = useState('');

  const calculateVuln = (likelihood, exposure, consequence) => {
    // Sanitize inputs
    if (likelihood < 1 || exposure < 1 || consequence < 1) return 0;
    const score = likelihood * exposure * consequence;
    const levels = {
      1: 'Low',
      50: 'Medium',
      100: 'High',
      200: 'Critical'
    };
    const level = Object.keys(levels).reduce((a, b) => score > levels[b] ? b : a, 'Low');
    setVulnScore(score);
    setAssessment(`Vulnerability Score: ${score} (${level}) - Prioritize if >100.`);
  };

  return (
    <div className=\"App\">
      <header className=\"App-header\">
        <h1>Threat App - Vuln Assessment</h1>
        <div>
          <label>Likelihood (1-10): <input type=\"number\" min=\"1\" max=\"10\" onChange={(e) => calculateVuln(e.target.value, exposure, consequence)} /></label>
          <label>Exposure (1-10): <input type=\"number\" min=\"1\" max=\"10\" /></label>
          <label>Consequence (1-10): <input type=\"number\" min=\"1\" max=\"10\" /></label>
        </div>
        <p>{assessment}</p>
      </header>
    </div>
  );
}

export default App;