import React, { useState, useEffect } from 'react';
import Head from 'next/head';
import MediaHandler from '../components/MediaHandler';

export default function SimulationPage({ initialScenario }) {
  const [scenario, setScenario] = useState(initialScenario || {
    situation_description: "Loading situation...",
    video_url: null,
    audio_url: null
  });
  
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  // Function to load a scenario
  const loadScenario = async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      const response = await fetch('/api/scenario');
      if (!response.ok) {
        throw new Error(`Failed to fetch scenario: ${response.status}`);
      }
      
      const data = await response.json();
      setScenario(data);
    } catch (err) {
      console.error('Error loading scenario:', err);
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };
  
  // Load scenario on initial page load
  useEffect(() => {
    if (!initialScenario) {
      loadScenario();
    }
  }, [initialScenario]);

  return (
    <div className="simulation-container">
      <Head>
        <title>Simulation Experience</title>
        <meta name="description" content="Interactive simulation experience" />
      </Head>
      
      <main>
        <h1>Interactive Simulation</h1>
        
        {isLoading ? (
          <div className="loading">
            <p>Loading simulation content...</p>
          </div>
        ) : error ? (
          <div className="error-message">
            <p>Error: {error}</p>
            <button onClick={loadScenario}>Try Again</button>
          </div>
        ) : (
          <div className="scenario-display">
            <div className="scenario-content">
              <h2>Situation</h2>
              <p>{scenario.situation_description}</p>
              
              {scenario.user_role && (
                <div className="user-role">
                  <h3>Your Role</h3>
                  <p>{scenario.user_role}</p>
                </div>
              )}
              
              {scenario.user_prompt && (
                <div className="user-prompt">
                  <h3>Your Task</h3>
                  <p>{scenario.user_prompt}</p>
                </div>
              )}
            </div>
            
            {scenario.video_url && (
              <div className="media-section">
                <h2>Scenario Video</h2>
                <p className="media-info">The video will be accompanied by narration audio. Use the unified play button when both are ready.</p>
                <MediaHandler 
                  src={scenario.video_url} 
                  audioSrc={scenario.audio_url}
                  type="video/mp4" 
                  width="100%" 
                  height="auto"
                />
              </div>
            )}
            
            {scenario.audio_url && !scenario.video_url && (
              <div className="audio-section">
                <h2>Narration</h2>
                <audio controls style={{ width: '100%' }}>
                  <source src={scenario.audio_url} type="audio/mpeg" />
                  Your browser does not support the audio element.
                </audio>
              </div>
            )}
            
            <div className="response-section">
              <h2>Your Response</h2>
              <textarea 
                placeholder="Type your response here..."
                rows={5}
                className="response-input"
              />
              <button className="submit-button">Submit Response</button>
            </div>
          </div>
        )}
      </main>
      
      <style jsx>{`
        .simulation-container {
          max-width: 900px;
          margin: 0 auto;
          padding: 20px;
        }
        
        h1 {
          text-align: center;
          margin-bottom: 30px;
        }
        
        .scenario-display {
          display: flex;
          flex-direction: column;
          gap: 20px;
        }
        
        .media-section, .audio-section {
          border: 1px solid #eaeaea;
          border-radius: 8px;
          padding: 20px;
          background-color: #f9f9f9;
        }
        
        .media-info {
          font-size: 14px;
          color: #666;
          margin-bottom: 10px;
          font-style: italic;
        }
        
        .response-input {
          width: 100%;
          padding: 12px;
          border: 1px solid #ddd;
          border-radius: 4px;
          font-family: inherit;
          resize: vertical;
        }
        
        .submit-button {
          margin-top: 10px;
          padding: 10px 20px;
          background-color: #0070f3;
          color: white;
          border: none;
          border-radius: 4px;
          cursor: pointer;
          font-size: 16px;
        }
        
        .submit-button:hover {
          background-color: #0051cc;
        }
        
        .loading, .error-message {
          text-align: center;
          margin: 40px 0;
        }
      `}</style>
    </div>
  );
}

// SSR to load initial scenario if available
export async function getServerSideProps() {
  try {
    // This would normally fetch from your API endpoint
    // For testing, return null to trigger client-side loading
    return {
      props: {
        initialScenario: null
      }
    };
  } catch (error) {
    return {
      props: {
        initialScenario: null
      }
    };
  }
} 