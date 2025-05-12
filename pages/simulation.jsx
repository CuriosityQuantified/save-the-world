import React, { useState, useEffect, useRef } from "react";
import Head from "next/head";
import MediaHandler from "../components/MediaHandler";

export default function SimulationPage({ initialScenario }) {
  const [scenarioText, setScenarioText] = useState(
    initialScenario?.situation_description || "Loading situation...",
  );

  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [turn, setTurn] = useState(0);
  const [MAX_TURNS, setMAX_TURNS] = useState(5);
  const [userInput, setUserInput] = useState("");
  
  // State for media URLs received from the backend
  const [currentVideoUrls, setCurrentVideoUrls] = useState([]);
  const [currentAudioUrl, setCurrentAudioUrl] = useState(null);

  // New generation progress states
  const [scenarioGenerated, setScenarioGenerated] = useState(false);
  const [videosGenerated, setVideosGenerated] = useState(false);
  const [audioGenerated, setAudioGenerated] = useState(false);

  const [history, setHistory] = useState([]);
  const inputRef = useRef(null);
  const chatEndRef = useRef(null);
  const wsRef = useRef(null); // Ref to hold the WebSocket connection
  const [simulationId, setSimulationId] = useState(null); // To manage simulation ID for WebSocket

  // New state for toggling debug info
  const [showDebugInfo, setShowDebugInfo] = useState(false);

  // WebSocket setup and handling effect
  useEffect(() => {
    if (!simulationId) return;

    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const wsUrl = `${protocol}//${window.location.host}/api/ws/simulations/${simulationId}`;
    wsRef.current = new WebSocket(wsUrl);

    wsRef.current.onopen = () => {
      console.log("WebSocket connection established for React component");
    };

    wsRef.current.onmessage = (event) => {
      const message = JSON.parse(event.data);
      console.log("WebSocket message received in React component:", message);

      if (message.type === "simulation_state" || message.type === "simulation_updated") {
        setScenarioText(message.simulation.scenario?.situation_description || message.simulation.scenario || "Scenario update failed.");
        setCurrentVideoUrls(message.simulation.video_urls || []);
        setCurrentAudioUrl(message.simulation.audio_url || null);
        setTurn(message.simulation.current_turn_number || 1);
        setHistory(prevHistory => {
          // Construct history carefully if needed, or rely on API response for full history
          const assistantMessageContent = message.simulation.scenario?.situation_description || message.simulation.scenario || "No scenario generated.";
          if (!prevHistory.find(msg => msg.role === 'assistant' && msg.content === assistantMessageContent)) {
              return [...prevHistory, { role: "assistant", content: assistantMessageContent}];
          }
          return prevHistory;
        });

        // Hide loading after a delay to allow seeing final checkmarks
        setTimeout(() => setIsLoading(false), 1000);

      } else if (message.type === "progress_update") {
        console.log(`React: Progress update received for step: ${message.step}`);
        if (message.step === "scenario_generated") {
          setScenarioGenerated(true);
        } else if (message.step === "videos_generated") {
          setVideosGenerated(true);
        } else if (message.step === "audio_generated") {
          setAudioGenerated(true);
        }
      }
    };

    wsRef.current.onerror = (error) => {
      console.error("WebSocket error in React component:", error);
      setError("WebSocket connection error. Please refresh.");
      setIsLoading(false);
    };

    wsRef.current.onclose = () => {
      console.log("WebSocket connection closed in React component");
      // Optional: logic to attempt reconnection if desired
    };

    // Cleanup function to close WebSocket connection when component unmounts or simulationId changes
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [simulationId]); // Re-run effect if simulationId changes

  // Function to handle user response submission
  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!userInput.trim() || isLoading || turn >= MAX_TURNS) return;

    setIsLoading(true);
    setScenarioGenerated(false);
    setVideosGenerated(false);
    setAudioGenerated(false);
    
    const currentInput = userInput;
    // Update history immediately for user feedback
    setHistory((prev) => [...prev, { role: "user", content: currentInput }]);
    setUserInput("");

    try {
      const response = await fetch("/api/simulation/turn", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          turn: turn, 
          history: [...history, { role: "user", content: currentInput }], // Send updated history
        }),
      });

      if (!response.ok) {
        const errorData = await response.text();
        throw new Error(`HTTP error! status: ${response.status}, ${errorData}`);
      }
      // Backend will now send simulation_state/progress_updates via WebSocket.
      // The setIsLoading(false) will be handled by the WebSocket onmessage handler.
      // const data = await response.json(); // No longer need to process data here directly for UI updates

    } catch (error) {
      console.error("Error fetching next turn:", error);
      setError(`Error advancing simulation: ${error.message}`);
      setIsLoading(false); // Ensure loading is false on error
    }
  };

  useEffect(() => {
    if (inputRef.current) {
      inputRef.current.focus();
    }
    if (chatEndRef.current) {
      chatEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [history, isLoading]);

  const initializeSimulation = async () => {
    setIsLoading(true);
    setError(null);
    setScenarioGenerated(false);
    setVideosGenerated(false);
    setAudioGenerated(false);
    
    try {
      console.log("Initializing simulation (Turn 0 -> 1) - React V3");
      const response = await fetch("/api/simulation/turn", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ turn: 0, history: [] }),
      });

      if (!response.ok) {
        const errorData = await response.text();
        throw new Error(`HTTP error! status: ${response.status}, ${errorData}`);
      }

      const data = await response.json();
      console.log("Received data for initial turn (React):", data);
      
      // Set the simulation ID to trigger WebSocket connection
      if (data.simulation_id) {
          setSimulationId(data.simulation_id);
      } else {
          // Fallback if simulation_id is not directly in the response, 
          // but expected in scenario object from a different structure
          setSimulationId(data.scenario?.simulation_id); 
      }
      
      // The rest of the UI updates (scenario, media, turn, history, isLoading)
      // will be handled by the WebSocket onmessage handler upon receiving "simulation_state".

    } catch (error) {
      console.error("Error initializing simulation (React):", error);
      setError(`Error starting simulation: ${error.message}`);
      setIsLoading(false); // Ensure loading is false on error
    }
  };

  useEffect(() => {
    // Only run if initialScenario wasn't provided or is minimal
    // This condition might need adjustment based on how initialScenario is actually used or if it's deprecated
    if (!initialScenario || !initialScenario.situation_description) { 
        initializeSimulation();
    }
  }, []); // Removed initialScenario from dependencies to prevent re-initialization if prop changes unexpectedly

  // Animated checkmark component with fade-in effect
  const ProgressItem = ({ label, isComplete }) => (
    <div style={{
      display: "flex",
      alignItems: "center",
      marginBottom: "8px",
      color: isComplete ? "#00ff00" : "#999",
      transition: "color 0.5s ease",
      animation: isComplete ? "fadeIn 0.5s ease-in-out" : "none",
    }}>
      <span style={{
        display: "inline-flex",
        justifyContent: "center",
        alignItems: "center",
        width: "24px",
        height: "24px",
        borderRadius: "12px",
        backgroundColor: isComplete ? "#005500" : "#333",
        marginRight: "10px",
        transition: "background-color 0.5s ease",
        fontWeight: "bold",
      }}>
        {isComplete ? "✓" : "..."}
      </span>
      {label}
      <span style={{
        marginLeft: "auto",
        fontSize: "0.8em",
        fontWeight: isComplete ? "bold" : "normal",
        color: isComplete ? "#00ff00" : "#999",
        transition: "color 0.5s ease",
      }}>
        {isComplete ? "Complete" : "Pending"}
      </span>
      <style jsx>{`
        @keyframes fadeIn {
          0% { opacity: 0.3; transform: scale(0.8); }
          70% { opacity: 1; transform: scale(1.1); }
          100% { opacity: 1; transform: scale(1); }
        }
      `}</style>
    </div>
  );

  return (
    <div style={{
      padding: '20px', // Added padding to see boundaries
      border: '5px solid red', // Added border to see boundaries
      fontFamily: 'Arial, sans-serif', // Basic font for test
      backgroundImage: "url(/UI_background.jpeg)",
      backgroundSize: "cover",
      backgroundPosition: "center",
      backgroundRepeat: "no-repeat",
      minHeight: "100vh",
      display: "flex",
      flexDirection: "column", // Changed to column to stack test elements
      justifyContent: "flex-start", // Changed to see top elements easily
      alignItems: "stretch", // Changed to allow full width
      position: "relative",
      color: "#fff", // Kept for original text if any
    }}>
      <h1 style={{color: 'lime', backgroundColor: 'black', padding: '10px', textAlign: 'center', fontSize: '24px'}}>SIMULATION.JSX RENDER CHECK V2</h1>
      
      {/* Debug Info Toggle - Simplified styling and positioning */}
      <div style={{
        margin: '10px 0',
        padding: '10px',
        backgroundColor: '#333',
        border: '2px solid yellow',
        color: 'white',
        fontFamily: 'monospace',
        fontSize: '14px'
      }}>
        <button 
          onClick={() => setShowDebugInfo(!showDebugInfo)}
          style={{
            padding: '8px 12px',
            backgroundColor: '#555',
            color: 'white',
            border: '1px solid #777',
            borderRadius: '5px',
            cursor: 'pointer',
            marginBottom: '10px'
          }}
        >
          {showDebugInfo ? "Hide" : "Show"} Raw Media URLs (Test V2)
        </button>
        {showDebugInfo && (
          <div style={{
            padding: '10px',
            backgroundColor: 'rgba(0,0,0,0.7)',
            border: '1px solid #666',
            borderRadius: '5px',
            color: '#0f0', // Lime green for visibility
            whiteSpace: 'pre-wrap', 
            maxHeight: '250px',
            overflowY: 'auto'
          }}>
            <p><strong>Video URLs (currentVideoUrls):</strong></p>
            <pre>{JSON.stringify(currentVideoUrls, null, 2)}</pre>
            <p style={{marginTop: '10px'}}><strong>Audio URL (currentAudioUrl):</strong></p>
            <pre>{JSON.stringify(currentAudioUrl, null, 2)}</pre>
            <p style={{marginTop: '10px'}}><strong>Type of video_urls:</strong> {typeof currentVideoUrls}</p>
            {currentVideoUrls !== null && currentVideoUrls !== undefined && <p><strong>Is video_urls an Array:</strong> {Array.isArray(currentVideoUrls).toString()}</p>}
          </div>
        )}
      </div>

      <Head>
        <title>Simulation Arcade</title>
        <link href="https://fonts.googleapis.com/css2?family=Press+Start+2P&display=swap" rel="stylesheet" />
      </Head>

      {/* Arcade Screen Content Area */}
      <div style={{
        position: "relative",
        width: "80%",
        margin: "20px auto",
        backgroundColor: "rgba(0, 0, 0, 0.8)",
        border: "5px solid #333",
        borderRadius: "10px",
        padding: "20px",
        display: "flex",
        flexDirection: "column",
        overflow: "hidden",
      }}>
        {/* Turn Counter */}
        <div style={{
          textAlign: "center",
          marginBottom: "10px",
          color: "#00ff00",
          textShadow: "0 0 5px #00ff00",
          fontSize: "0.8em",
          fontFamily: '"Press Start 2P", cursive',
        }}>
          TURN {turn > 0 ? turn : 1}/{MAX_TURNS}
        </div>

        {/* Content Grid */}
        <div style={{
          display: "grid",
          gridTemplateColumns: "1fr 1fr",
          gap: "15px",
          flex: 1,
          overflow: "hidden",
        }}>
          {/* Media Section - Now uses MediaHandler */}
          <div style={{
            backgroundColor: "#111",
            border: "2px solid #444",
            borderRadius: "5px",
            overflow: "hidden",
            display: "flex",
            justifyContent: "center",
            alignItems: "center",
            height: "100%",
            minHeight: '200px',
            position: 'relative',
          }}>
            {isLoading ? (
              <div style={{ 
                color: "#fff", 
                textAlign: "center", 
                padding: "20px",
                backgroundColor: "rgba(0,0,0,0.7)",
                borderRadius: "5px",
                fontFamily: 'monospace',
                width: "80%",
              }}>
                <div style={{ marginBottom: "20px", fontSize: "1.1em", color: "#00ff00" }}>
                  Generating Content...
                </div>
                <ProgressItem label="Scenario Generated" isComplete={scenarioGenerated} />
                <ProgressItem label="Videos Generated" isComplete={videosGenerated} />
                <ProgressItem label="Audio Generated" isComplete={audioGenerated} />
              </div>
            ) : (
              <MediaHandler 
                video_urls={currentVideoUrls}
                audio_url={currentAudioUrl}
                width="100%" 
                height="100%" 
              />
            )}
          </div>

          {/* Scenario & Chat Section */}
          <div style={{
            display: "flex",
            flexDirection: "column",
            gap: "10px",
            overflow: "hidden",
            height: "100%",
            fontFamily: '"Press Start 2P", cursive',
          }}>
            {/* Scenario Text Area */}
            <div style={{
              flex: "0 0 30%",
              backgroundColor: "#222",
              border: "2px solid #444",
              padding: "10px",
              borderRadius: "5px",
              overflowY: "auto",
              fontSize: "0.8em",
              lineHeight: "1.4",
              color: "#ddd",
            }}>
              {isLoading && !scenarioText ? (
                <div style={{ textAlign: "center" }}>
                  <span style={{ color: "#00ff00" }}>Generating scenario...</span>
                </div>
              ) : scenarioText}
            </div>

            {/* Chat History Area */}
            <div style={{
              flex: "1 1 auto",
              backgroundColor: "#1a1a1a",
              border: "2px solid #444",
              padding: "10px",
              borderRadius: "5px",
              overflowY: "auto",
              fontSize: "0.75em",
              display: "flex",
              flexDirection: "column-reverse",
            }}>
              <div ref={chatEndRef} />
              {[...history].reverse().map((msg, index) => (
                <div key={index} style={{
                  marginBottom: "8px",
                  textAlign: msg.role === "user" ? "right" : "left",
                }}>
                  <span style={{
                    backgroundColor: msg.role === "user" ? "#007bff" : "#333",
                    color: "white",
                    padding: "5px 10px",
                    borderRadius: "10px",
                    display: "inline-block",
                    maxWidth: "80%",
                  }}>
                    {msg.content}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* User Input Area - Below the grid */}
        <form onSubmit={handleSubmit} style={{
          marginTop: "15px",
          display: "flex",
          gap: "10px",
          fontFamily: '"Press Start 2P", cursive',
        }}>
          <input
            ref={inputRef}
            type="text"
            value={userInput}
            onChange={(e) => setUserInput(e.target.value)}
            placeholder={turn >= MAX_TURNS ? "Simulation ended." : "Your response..."}
            disabled={isLoading || turn >= MAX_TURNS}
            style={{
              flexGrow: 1,
              padding: "10px",
              borderRadius: "5px",
              border: "2px solid #444",
              backgroundColor: "#333",
              color: "#fff",
              fontFamily: 'inherit',
              fontSize: "0.8em",
            }}
          />
          <button type="submit" disabled={isLoading || turn >= MAX_TURNS} style={{
            padding: "10px 15px",
            borderRadius: "5px",
            border: "none",
            backgroundColor: "#00ff00",
            color: "#000",
            cursor: "pointer",
            fontFamily: 'inherit',
            fontSize: "0.8em",
            opacity: (isLoading || turn >= MAX_TURNS) ? 0.5 : 1,
          }}>
            Send
          </button>
        </form>
        
        {error && (
          <div style={{ color: "red", marginTop: "10px", fontSize: "0.8em", fontFamily: '"Press Start 2P", cursive' }}>
            Error: {error}
          </div>
        )}
      </div>
    </div>
  );
}

// getServerSideProps might need adjustment if initialScenario structure changes significantly
export async function getServerSideProps(context) {
  console.log("getServerSideProps called - TEST MARKER V2");
  try {
    return {
      props: {
        initialScenario: null, 
      },
    };
  } catch (error) {
    console.error("Error in getServerSideProps:", error);
    return {
      props: {
        initialScenario: null,
        error: error.message,
      },
    };
  }
}