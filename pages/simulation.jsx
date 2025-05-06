
import React, { useState, useEffect } from 'react';
import Head from 'next/head';
import MediaHandler from '../components/MediaHandler';

export default function SimulationPage() {
  const [simulation, setSimulation] = useState({
    currentScenario: null,
    isLoading: false,
    error: null
  });

  const generateScenario = async () => {
    setSimulation(prev => ({ ...prev, isLoading: true, error: null }));
    try {
      const response = await fetch('/api/scenario');
      if (!response.ok) {
        throw new Error('Failed to fetch scenario');
      }
      const data = await response.json();
      setSimulation(prev => ({
        ...prev,
        currentScenario: data,
        isLoading: false
      }));
    } catch (err) {
      setSimulation(prev => ({
        ...prev,
        error: err.message,
        isLoading: false
      }));
    }
  };

  return (
    <div className="container">
      <Head>
        <title>Simulation Experience</title>
        <meta name="description" content="Interactive simulation experience" />
      </Head>

      <main className="main">
        <div className="scenario-section">
          <h1>Absurd Crisis Simulation</h1>
          
          <button 
            className="generate-btn"
            onClick={generateScenario}
            disabled={simulation.isLoading}
          >
            {simulation.isLoading ? 'Generating...' : 'Generate Scenario'}
          </button>

          {simulation.error && (
            <div className="error">Error: {simulation.error}</div>
          )}

          {simulation.currentScenario && (
            <div className="scenario-content">
              <h2>Current Scenario</h2>
              <p>{simulation.currentScenario.situation_description}</p>
              
              {simulation.currentScenario.user_role && (
                <div className="role-section">
                  <h3>Your Role</h3>
                  <p>{simulation.currentScenario.user_role}</p>
                </div>
              )}
              
              {simulation.currentScenario.user_prompt && (
                <div className="prompt-section">
                  <h3>Your Task</h3>
                  <p>{simulation.currentScenario.user_prompt}</p>
                </div>
              )}

              <div className="response-section">
                <h3>Your Response</h3>
                <textarea 
                  placeholder="How do you respond to this situation?"
                  rows={5}
                />
                <button className="submit-btn">Submit Response</button>
              </div>
            </div>
          )}
        </div>
      </main>

      <style jsx>{`
        .container {
          min-height: 100vh;
          background: #1a1a1a;
          color: #ffffff;
        }

        .main {
          padding: 2rem;
          max-width: 800px;
          margin: 0 auto;
        }

        h1 {
          text-align: center;
          margin-bottom: 2rem;
          color: #ffffff;
        }

        .generate-btn {
          display: block;
          margin: 2rem auto;
          padding: 1rem 2rem;
          font-size: 1.2rem;
          background: #4CAF50;
          color: white;
          border: none;
          border-radius: 4px;
          cursor: pointer;
          transition: background 0.2s;
        }

        .generate-btn:hover {
          background: #45a049;
        }

        .generate-btn:disabled {
          background: #666;
          cursor: not-allowed;
        }

        .scenario-content {
          background: #2a2a2a;
          padding: 2rem;
          border-radius: 8px;
          margin-top: 2rem;
        }

        .role-section, .prompt-section {
          margin: 1.5rem 0;
          padding: 1rem;
          background: #333;
          border-radius: 4px;
        }

        h2, h3 {
          color: #4CAF50;
          margin-bottom: 1rem;
        }

        .response-section {
          margin-top: 2rem;
        }

        textarea {
          width: 100%;
          padding: 1rem;
          margin: 1rem 0;
          background: #333;
          border: 1px solid #444;
          color: white;
          border-radius: 4px;
          font-family: inherit;
        }

        .submit-btn {
          padding: 0.8rem 1.5rem;
          background: #2196F3;
          color: white;
          border: none;
          border-radius: 4px;
          cursor: pointer;
        }

        .submit-btn:hover {
          background: #1976D2;
        }

        .error {
          color: #ff6b6b;
          text-align: center;
          margin: 1rem 0;
        }
      `}</style>
    </div>
  );
}
