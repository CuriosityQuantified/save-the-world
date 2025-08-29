import React, { useState, useEffect, useRef } from "react";
import Head from "next/head";
import MediaHandler from "../components/MediaHandler";

export default function SimulationPage({ initialScenario }) {
  // Removed scenarioText state - using history instead

  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [turn, setTurn] = useState(0);
  const [MAX_TURNS, setMAX_TURNS] = useState(4);
  const [userTurn, setUserTurn] = useState(0);  // Track actual user submissions
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

  // State for managing simulation initialization
  const [simulationStarted, setSimulationStarted] = useState(false);

  // WebSocket setup and handling effect
  useEffect(() => {
    if (!simulationId) return;

    // Connect directly to backend on port 8000, bypassing proxy
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const wsUrl = `${protocol}//localhost:8000/ws/simulations/${simulationId}`;
    wsRef.current = new WebSocket(wsUrl);

    wsRef.current.onopen = () => {
      console.log("WebSocket connection established for React component");
    };

    wsRef.current.onmessage = (event) => {
      const message = JSON.parse(event.data);
      console.log("WebSocket message received in React component:", message);

      if (message.type === "simulation_state" || message.type === "simulation_updated") {
        // Get the current turn data
        const currentTurnNumber = message.simulation.current_turn_number || 1;
        const currentTurn = message.simulation.turns?.find(t => t.turn_number === currentTurnNumber);
        
        // Extract all scenario parts and format them properly
        const scenario = currentTurn?.selected_scenario;
        let scenarioDisplay = "";
        if (scenario) {
          scenarioDisplay = scenario.situation_description || "";
          // Only include user_role for the very first turn (userTurn === 0)
          if (scenario.user_role && userTurn === 0) {
            scenarioDisplay += "\n\n" + scenario.user_role;
          }
          if (scenario.user_prompt) {
            scenarioDisplay += "\n\n" + scenario.user_prompt;
          }
        } else {
          scenarioDisplay = message.simulation.scenario?.situation_description || 
                          message.simulation.scenario || 
                          "Scenario loading...";
        }
        // Add scenario to history as assistant message instead of separate display
        setHistory(prev => {
          // Only add if it's a new scenario (avoid duplicates)
          const lastAssistantMsg = [...prev].reverse().find(msg => msg.role === "assistant");
          if (!lastAssistantMsg || lastAssistantMsg.content !== scenarioDisplay) {
            return [...prev, { role: "assistant", content: scenarioDisplay }];
          }
          return prev;
        });
        const videoUrls = currentTurn?.video_urls || message.simulation.video_urls || [];
        const audioUrl = currentTurn?.audio_url || message.simulation.audio_url || null;
        
        setCurrentVideoUrls(videoUrls);
        setCurrentAudioUrl(audioUrl);
        setTurn(currentTurnNumber);
        
        // Update generation flags based on actual media presence
        setVideosGenerated(videoUrls.length > 0);
        setAudioGenerated(!!audioUrl);
        // Removed duplicate setHistory - scenario already added above with all fields

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
    if (!userInput.trim() || isLoading || turn > MAX_TURNS) return;

    setIsLoading(true);
    setScenarioGenerated(false);
    setVideosGenerated(false);
    setAudioGenerated(false);
    
    // Increment userTurn counter after first submission
    setUserTurn(prev => prev + 1);

    const currentInput = userInput;
    // Update history immediately for user feedback
    setHistory((prev) => [...prev, { role: "user", content: currentInput }]);
    setUserInput("");

    try {
      // Ensure simulationId is available before making the call
      if (!simulationId) {
        throw new Error("Simulation ID is not set. Cannot submit response.");
      }

      // Add 5-minute timeout for response processing (to allow for retries)
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 300000); // 5 minutes
      
      // Call backend directly to avoid proxy timeout issues
      const response = await fetch(`http://localhost:8000/simulations/${simulationId}/respond`, { // NEW: Use respond endpoint
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ // NEW: Body according to UserResponseRequest model
           response_text: currentInput 
        }),
        signal: controller.signal // Add abort signal for timeout
      });
      
      clearTimeout(timeoutId); // Clear timeout if request completes

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
      console.log("Initializing simulation - React V4 - Using POST /api/simulations");
      
      // Add 5-minute timeout for video generation (to allow for retries)
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 300000); // 5 minutes
      
      // Call backend directly to avoid proxy timeout issues
      const response = await fetch("http://localhost:8000/simulations", { 
        method: "POST",
        headers: { "Content-Type": "application/json" },
        // Send an initial prompt or other required data if necessary
        // Assuming SimulationRequest might just need developer_mode or an empty prompt for now
        body: JSON.stringify({ 
            initial_prompt: "Start a new simulation.", // Example initial prompt
            developer_mode: false // Assuming default behavior
        }),
        signal: controller.signal // Add abort signal for timeout
      });
      
      clearTimeout(timeoutId); // Clear timeout if request completes

      if (!response.ok) {
        const errorData = await response.text();
        throw new Error(`HTTP error! status: ${response.status}, ${errorData}`);
      }

      const data = await response.json(); // data should be the initial SimulationState
      console.log("Received data from initial POST /api/simulations (React):", data);

      // Set the simulation ID from the response to trigger WebSocket connection
      if (data.simulation_id) {
          setSimulationId(data.simulation_id);

          // Get the current turn data from the nested structure
          const currentTurnNumber = data.current_turn_number || 0;
          const currentTurn = data.turns?.find(t => t.turn_number === currentTurnNumber);

          // Manually update state based on the initial response, as WebSocket might take time
          // Build the full scenario display for the history
          let fullScenario = "";
          if (currentTurn?.selected_scenario) {
            fullScenario = currentTurn.selected_scenario.situation_description || "";
            if (currentTurn.selected_scenario.user_role) {
              fullScenario += "\n\n" + currentTurn.selected_scenario.user_role;
            }
            if (currentTurn.selected_scenario.user_prompt) {
              fullScenario += "\n\n" + currentTurn.selected_scenario.user_prompt;
            }
          } else if (data.scenario?.situation_description) {
            fullScenario = data.scenario.situation_description;
          } else {
            fullScenario = "Scenario loading...";
          }
          setCurrentVideoUrls(currentTurn?.video_urls || data.video_urls || []);
          setCurrentAudioUrl(currentTurn?.audio_url || data.audio_url || null);
          setTurn(currentTurnNumber); // Start at turn 0 or 1 as per backend logic
          // Initial history with the full scenario
          setHistory([{ role: "assistant", content: fullScenario || "Welcome!" }]);

          // Update progress based on initial state (maybe nothing is generated yet)
          setScenarioGenerated(!!currentTurn?.selected_scenario?.situation_description || !!data.scenario?.situation_description);
          setVideosGenerated(!!(currentTurn?.video_urls && currentTurn.video_urls.length > 0) || !!(data.video_urls && data.video_urls.length > 0));
          setAudioGenerated(!!currentTurn?.audio_url || !!data.audio_url);

      } else {
          throw new Error("Simulation ID not received in the initialization response.");
      }

      // Hide loading *after* initial state is set, before WebSocket takes over fully
      setIsLoading(false); 

    } catch (error) {
      console.error("Error initializing simulation (React):", error);
      setError(`Error starting simulation: ${error.message}`);
      setIsLoading(false); // Ensure loading is false on error
    }
  };

  // Removed automatic initialization - now triggered by button click

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
      fontFamily: 'Arial, sans-serif',
      backgroundColor: "#d4c5a0",  // Warm vintage color matching comic panels
      backgroundImage: "url(/UI_background.jpeg)",
      backgroundSize: "contain",  // Changed from 'cover' to 'contain' to show full image
      backgroundPosition: "center",
      backgroundRepeat: "no-repeat",
      minHeight: "100vh",
      display: "flex",
      flexDirection: "column",
      justifyContent: "center",
      alignItems: "center",
      position: "relative",
      color: "#fff",
    }}>

      <Head>
        <title>Simulation Arcade</title>
        <link href="https://fonts.googleapis.com/css2?family=Press+Start+2P&display=swap" rel="stylesheet" />
      </Head>

      {/* Start New Simulation Button - Show when not started */}
      {!simulationStarted && (
        <div style={{
          textAlign: "center",
          marginBottom: "40px",
        }}>
          <button
            onClick={() => {
              setSimulationStarted(true);
              initializeSimulation();
            }}
            disabled={isLoading}
            style={{
              padding: "20px 40px",
              fontSize: "1.2em",
              fontFamily: '"Press Start 2P", cursive',
              backgroundColor: "#00ff00",
              color: "#000",
              border: "none",
              borderRadius: "10px",
              cursor: "pointer",
              textShadow: "0 0 5px #00ff00",
              boxShadow: "0 0 20px rgba(0, 255, 0, 0.5)",
              transition: "all 0.3s ease",
              opacity: isLoading ? 0.5 : 1,
            }}
            onMouseOver={(e) => {
              if (!isLoading) {
                e.target.style.transform = "scale(1.1)";
                e.target.style.boxShadow = "0 0 30px rgba(0, 255, 0, 0.8)";
              }
            }}
            onMouseOut={(e) => {
              e.target.style.transform = "scale(1)";
              e.target.style.boxShadow = "0 0 20px rgba(0, 255, 0, 0.5)";
            }}
          >
            {isLoading ? "Starting..." : "Start New Simulation"}
          </button>
        </div>
      )}

      {/* Arcade Screen Content Area - Show after simulation starts */}
      {simulationStarted && (
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
          height: "500px",  // Fixed height to prevent growing
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

          {/* Chat Section - Single window matching video height */}
          <div style={{
            height: "100%",
            backgroundColor: "#1a1a1a",
            border: "2px solid #444",
            padding: "10px",
            borderRadius: "5px",
            overflowY: "auto",
            fontSize: "0.75em",
            display: "flex",
            flexDirection: isLoading && history.length === 0 ? "column" : "column-reverse",
            justifyContent: isLoading && history.length === 0 ? "center" : "flex-start",
            alignItems: isLoading && history.length === 0 ? "center" : "stretch",
            fontFamily: '"Press Start 2P", cursive',
          }}>
            <div ref={chatEndRef} />
            {isLoading && history.length === 0 ? (
              <div style={{ textAlign: "center" }}>
                <span style={{ color: "#00ff00" }}>Generating scenario...</span>
              </div>
            ) : (
              [...history].reverse().map((msg, index) => (
                <div key={index} style={{
                  marginBottom: "12px",
                  textAlign: msg.role === "user" ? "right" : "left",
                }}>
                  <div style={{
                    fontSize: "0.6em",
                    color: msg.role === "user" ? "#66aaff" : "#66ff66",
                    marginBottom: "4px",
                  }}>
                    {msg.role === "user" ? "You:" : "Scenario:"}
                  </div>
                  <span style={{
                    backgroundColor: msg.role === "user" ? "#007bff" : "#333",
                    color: "white",
                    padding: "8px 12px",
                    borderRadius: "10px",
                    display: "inline-block",
                    maxWidth: "85%",
                    whiteSpace: "pre-wrap",
                    lineHeight: "1.4",
                  }}>
                    {msg.content}
                  </span>
                </div>
              ))
            )}
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
            placeholder={turn > MAX_TURNS ? "Simulation ended." : !simulationId ? "Start a simulation first..." : "Your response..."}
            disabled={isLoading || turn > MAX_TURNS || !simulationId}
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
          <button type="submit" disabled={isLoading || turn > MAX_TURNS || !simulationId} style={{
            padding: "10px 15px",
            borderRadius: "5px",
            border: "none",
            backgroundColor: "#00ff00",
            color: "#000",
            cursor: "pointer",
            fontFamily: 'inherit',
            fontSize: "0.8em",
            opacity: (isLoading || turn > MAX_TURNS || !simulationId) ? 0.5 : 1,
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
      )}
    </div>
  );
}

export async function getServerSideProps(context) {
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