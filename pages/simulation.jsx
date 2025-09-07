import React, { useState, useEffect, useRef } from "react";
import Head from "next/head";
import MediaHandler from "../components/MediaHandler";

export default function SimulationPage({ initialScenario }) {
  // Removed scenarioText state - using history instead

  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [turn, setTurn] = useState(0);
  // These values now come from backend
  const [maxTurns, setMaxTurns] = useState(3);
  const [submissionCount, setSubmissionCount] = useState(0);
  const [userInput, setUserInput] = useState("");

  // State for media URLs received from the backend
  const [currentVideoUrls, setCurrentVideoUrls] = useState([]);
  const [currentAudioUrl, setCurrentAudioUrl] = useState(null);

  // New generation progress states
  const [scenarioGenerated, setScenarioGenerated] = useState(false);
  const [videosGenerated, setVideosGenerated] = useState(false);
  const [audioGenerated, setAudioGenerated] = useState(false);
  
  // Conclusion state
  const [showConclusion, setShowConclusion] = useState(false);
  const [conclusionData, setConclusionData] = useState(null);

  const [history, setHistory] = useState([]);
  const inputRef = useRef(null);
  const chatEndRef = useRef(null);
  const wsRef = useRef(null); // Ref to hold the WebSocket connection
  const [simulationId, setSimulationId] = useState(null); // To manage simulation ID for WebSocket

  // State for managing simulation initialization
  const [simulationStarted, setSimulationStarted] = useState(false);
  
  // State for backend port discovery
  const [backendPort, setBackendPort] = useState(8000);
  const [backendUrl, setBackendUrl] = useState('http://localhost:8000');
  const [backendWsUrl, setBackendWsUrl] = useState('ws://localhost:8000');
  
  // Discover backend port on component mount
  useEffect(() => {
    async function discoverBackendPort() {
      try {
        const response = await fetch('/api/backend-port');
        if (response.ok) {
          const data = await response.json();
          console.log('Backend discovered on port:', data.port);
          setBackendPort(data.port);
          setBackendUrl(data.url);
          setBackendWsUrl(data.wsUrl);
        }
      } catch (error) {
        console.error('Failed to discover backend port, using default:', error);
      }
    }
    
    discoverBackendPort();
  }, []); // Run only once on mount

  // WebSocket setup and handling effect
  useEffect(() => {
    if (!simulationId) return;

    // Connect directly to backend using discovered port
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const wsUrl = `${protocol}//localhost:${backendPort}/ws/simulations/${simulationId}`;
    console.log('Connecting WebSocket to:', wsUrl);
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
        
        // CRITICAL: If simulation is complete, conclusion is stored at turn+1 (turn 4)
        const checkTurn = message.simulation.is_complete ? currentTurnNumber + 1 : currentTurnNumber;
        const currentTurn = message.simulation.turns?.find(t => t.turn_number === checkTurn);
        
        console.log(`[DEBUG] Looking for turn data at turn ${checkTurn} (is_complete: ${message.simulation.is_complete})`);
        
        // Update frontend state from backend
        setMaxTurns(message.simulation.max_turns || 3);
        setSubmissionCount(message.simulation.submission_count || 0);
        
        // Special logging for final turn
        if (currentTurnNumber === message.simulation.max_turns) {
          console.log(`[FINAL TURN] [WEBSOCKET] 🔵 Received update for Turn ${currentTurnNumber}`);
          console.log(`[FINAL TURN] Current turn data:`, currentTurn);
          console.log(`[FINAL TURN] is_complete: ${message.simulation.is_complete}`);
          console.log(`[FINAL TURN] submission_count: ${message.simulation.submission_count}/${message.simulation.max_turns}`);
          if (currentTurn?.selected_scenario) {
            console.log(`[FINAL TURN] Selected scenario has grade?: ${currentTurn.selected_scenario.grade !== undefined}`);
            if (currentTurn.selected_scenario.grade !== undefined) {
              console.log(`[FINAL TURN] 🎯 CONCLUSION DETECTED! Grade: ${currentTurn.selected_scenario.grade}/100`);
            }
          }
        }
        
        // Extract media URLs first (before they're used in conclusion data)
        const videoUrls = currentTurn?.video_urls || message.simulation.video_urls || [];
        const audioUrl = currentTurn?.audio_url || message.simulation.audio_url || null;
        
        // Extract all scenario parts and format them properly
        const scenario = currentTurn?.selected_scenario;
        let scenarioDisplay = "";
        if (scenario) {
          scenarioDisplay = scenario.situation_description || "";
          // Only include user_role for the very first turn (submissionCount === 0)
          if (scenario.user_role && submissionCount === 0) {
            scenarioDisplay += "\n\n" + scenario.user_role;
          }
          // Check for conclusion (grade present)
          console.log(`[DEBUG] Checking for conclusion - grade: ${scenario.grade}, turn: ${currentTurnNumber}`);
          if (scenario.grade !== undefined && scenario.grade !== null) {
            // This is a conclusion scenario
            console.log(`[DEBUG] 🎯 CONCLUSION DETECTED! Grade: ${scenario.grade}/100`);
            console.log(`[DEBUG] Conclusion Audio URL: ${audioUrl}`);
            console.log(`[DEBUG] Conclusion Video URLs:`, videoUrls);
            console.log(`[DEBUG] Full Grade Explanation Length: ${scenario.grade_explanation?.length || 0} characters`);
            console.log(`[DEBUG] Full Grade Explanation:`, scenario.grade_explanation);
            setConclusionData({
              scenario: scenarioDisplay,
              grade: scenario.grade,
              gradeExplanation: scenario.grade_explanation || "",
              videoUrls: videoUrls,
              audioUrl: audioUrl
            });
            setShowConclusion(true);
          } else if (scenario.user_prompt) {
            console.log(`[DEBUG] Regular turn ${currentTurnNumber} - User prompt present`);
            // Regular turn with user prompt
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
        
        setCurrentVideoUrls(videoUrls);
        setCurrentAudioUrl(audioUrl);
        setTurn(currentTurnNumber);
        
        // Update generation flags based on actual media presence
        setVideosGenerated(videoUrls.length > 0);
        setAudioGenerated(!!audioUrl);
        // Removed duplicate setHistory - scenario already added above with all fields

        // Hide loading after a delay to allow seeing final checkmarks
        console.log(`[STATE] Setting isLoading to false after 1 second delay (turn ${currentTurnNumber})`);
        setTimeout(() => {
          setIsLoading(false);
          console.log(`[STATE] isLoading set to false (turn ${currentTurnNumber})`);
          if (submissionCount >= message.simulation.max_turns - 1) {
            console.log(`[FINAL TURN] [STATE] 🟢 isLoading is now FALSE - submit button should be enabled`);
            console.log(`[FINAL TURN] [STATE] Current states: turn=${currentTurnNumber}, submissions=${submissionCount}/${message.simulation.max_turns}, isLoading=false, showConclusion=${scenario?.grade !== undefined}`);
          }
        }, 1000);

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
  }, [simulationId, backendPort]); // Re-run effect if simulationId or backendPort changes

  // Function to handle user response submission
  const handleSubmit = async (e) => {
    e.preventDefault();
    
    // Debug logging for turn 3 submission tracking
    console.log(`[DEBUG] handleSubmit called - Turn: ${turn}/${maxTurns}, Submissions: ${submissionCount}/${maxTurns}, Loading: ${isLoading}`);
    console.log(`[DEBUG] User input: "${userInput}", SimulationId: ${simulationId}`);
    
    // Check submission conditions
    if (!userInput.trim()) {
      console.log("[DEBUG] Submission blocked: Empty input");
      return;
    }
    if (isLoading) {
      console.log("[DEBUG] Submission blocked: Already loading");
      return;
    }
    // Let backend handle submission count validation
    if (submissionCount >= maxTurns && !showConclusion) {
      console.log(`[DEBUG] Submission blocked: Already reached max submissions ${submissionCount}/${maxTurns}`);
      return;
    }
    
    console.log(`[DEBUG] ✅ Submission proceeding for turn ${turn}`);

    setIsLoading(true);
    setScenarioGenerated(false);
    setVideosGenerated(false);
    setAudioGenerated(false);
    
    // Backend will increment submission counter

    const currentInput = userInput;
    // Update history immediately for user feedback
    setHistory((prev) => [...prev, { role: "user", content: currentInput }]);
    setUserInput("");

    try {
      // Ensure simulationId is available before making the call
      if (!simulationId) {
        console.error("[DEBUG] ERROR: Simulation ID is not set. Cannot submit response.");
        throw new Error("Simulation ID is not set. Cannot submit response.");
      }

      // Add 5-minute timeout for response processing (to allow for retries)
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 300000); // 5 minutes
      
      // Log the request details
      const requestUrl = `${backendUrl}/simulations/${simulationId}/respond`;
      const requestBody = { response_text: currentInput };
      console.log(`[DEBUG] Making POST request to: ${requestUrl}`);
      console.log(`[DEBUG] Request body:`, requestBody);
      console.log(`[DEBUG] This is submission #${submissionCount + 1} (conclusion triggers at ${maxTurns})`);
      
      // Call backend directly to avoid proxy timeout issues
      const response = await fetch(requestUrl, { // NEW: Use respond endpoint
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(requestBody),
        signal: controller.signal // Add abort signal for timeout
      });
      
      clearTimeout(timeoutId); // Clear timeout if request completes
      console.log(`[DEBUG] Response received: Status ${response.status}`);

      if (!response.ok) {
        const errorData = await response.text();
        console.error(`[DEBUG] ERROR: HTTP error! status: ${response.status}, ${errorData}`);
        throw new Error(`HTTP error! status: ${response.status}, ${errorData}`);
      }
      
      console.log(`[DEBUG] ✅ Turn ${turn} response submitted successfully`);
      // Backend will now send simulation_state/progress_updates via WebSocket.
      // The setIsLoading(false) will be handled by the WebSocket onmessage handler.
      // const data = await response.json(); // No longer need to process data here directly for UI updates

    } catch (error) {
      console.error(`[DEBUG] Error on turn ${turn} submission:`, error);
      console.error("[DEBUG] Error details:", {
        turn: turn,
        maxTurns: maxTurns,
        simulationId: simulationId,
        userInput: currentInput,
        errorMessage: error.message,
        errorStack: error.stack
      });
      setError(`Error advancing simulation on turn ${turn}: ${error.message}`);
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
  
  // Track submit button state for Turn 3
  useEffect(() => {
    const isDisabled = isLoading || (submissionCount >= maxTurns && !showConclusion) || !simulationId;
    if (submissionCount === maxTurns - 1) {
      console.log(`[FINAL SUBMISSION] [BUTTON STATE] 🔍 Submit button state check:`);
      console.log(`[FINAL SUBMISSION] - isLoading: ${isLoading}`);
      console.log(`[FINAL SUBMISSION] - submissions: ${submissionCount}/${maxTurns}`);
      console.log(`[FINAL SUBMISSION] - !simulationId: ${!simulationId} (id: ${simulationId})`);
      console.log(`[FINAL SUBMISSION] - Button disabled: ${isDisabled}`);
      if (!isDisabled) {
        console.log(`[FINAL SUBMISSION] 🟢 Submit button SHOULD BE ENABLED - user can submit`);
      } else {
        console.log(`[FINAL SUBMISSION] 🔴 Submit button IS DISABLED - user CANNOT submit`);
      }
    }
  }, [isLoading, turn, maxTurns, submissionCount, simulationId, showConclusion]);

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
      const response = await fetch(`${backendUrl}/simulations`, { 
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

  // Conclusion Overlay Component
  const ConclusionOverlay = () => {
    if (!showConclusion || !conclusionData) return null;
    
    return (
      <div style={{
        position: "fixed",
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: "rgba(0, 0, 0, 0.95)",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        zIndex: 1000,
        padding: "20px",
        fontFamily: '"Press Start 2P", cursive',
        overflowY: "hidden",
      }}>
        <div style={{
          maxWidth: "900px",
          width: "100%",
          maxHeight: "90vh",
          overflowY: "auto",
          backgroundColor: "#1a1a1a",
          border: "3px solid #00ff00",
          borderRadius: "10px",
          padding: "30px",
          boxShadow: "0 0 30px rgba(0, 255, 0, 0.5)",
          margin: "auto",
        }}>
          <h2 style={{
            color: "#00ff00",
            textAlign: "center",
            marginBottom: "20px",
            fontSize: "1.5em",
            textShadow: "2px 2px 4px rgba(0, 255, 0, 0.3)",
          }}>
            SIMULATION COMPLETE
          </h2>
          
          {/* Final Video */}
          {conclusionData.videoUrls && conclusionData.videoUrls.length > 0 && (
            <div style={{
              marginBottom: "20px",
              display: "flex",
              justifyContent: "center",
            }}>
              <video
                src={conclusionData.videoUrls[0]}
                autoPlay
                loop
                muted
                style={{
                  width: "400px",
                  height: "225px",
                  borderRadius: "5px",
                  border: "2px solid #444",
                }}
              />
            </div>
          )}
          
          {/* Conclusion Audio - Hidden but autoplaying */}
          {conclusionData.audioUrl && (
            <audio
              src={conclusionData.audioUrl}
              autoPlay
              style={{ display: "none" }}
            />
          )}
          
          {/* Conclusion Scenario */}
          <div style={{
            backgroundColor: "#2a2a2a",
            padding: "20px",
            borderRadius: "5px",
            marginBottom: "20px",
            border: "1px solid #444",
          }}>
            <h3 style={{ color: "#66ff66", marginBottom: "10px", fontSize: "0.9em" }}>
              Final Assessment:
            </h3>
            <p style={{ color: "#fff", lineHeight: "1.6", fontSize: "0.8em", whiteSpace: "pre-wrap" }}>
              {conclusionData.scenario}
            </p>
          </div>
          
          {/* Performance Analysis - Moved before Grade Display */}
          <div style={{
            backgroundColor: "#2a2a2a",
            padding: "20px",
            borderRadius: "5px",
            marginBottom: "20px",
            border: "1px solid #444",
          }}>
            <h3 style={{ color: "#66ff66", marginBottom: "10px", fontSize: "0.9em" }}>
              Performance Analysis:
            </h3>
            <p style={{ color: "#fff", lineHeight: "1.6", fontSize: "0.8em", whiteSpace: "pre-wrap" }}>
              {conclusionData.gradeExplanation}
            </p>
          </div>
          
          {/* Grade Display - Now after Performance Analysis */}
          <div style={{
            textAlign: "center",
            marginBottom: "20px",
          }}>
            <div style={{
              fontSize: "3em",
              color: conclusionData.grade >= 70 ? "#00ff00" : conclusionData.grade >= 40 ? "#ffff00" : "#ff4444",
              textShadow: "3px 3px 6px rgba(0, 0, 0, 0.5)",
              marginBottom: "10px",
            }}>
              SCORE: {conclusionData.grade}/100
            </div>
          </div>
          
          {/* Restart Button */}
          <div style={{ textAlign: "center" }}>
            <button
              onClick={() => {
                setShowConclusion(false);
                setConclusionData(null);
                window.location.reload();
              }}
              style={{
                backgroundColor: "#00ff00",
                color: "#000",
                border: "none",
                padding: "15px 30px",
                fontSize: "0.9em",
                fontFamily: '"Press Start 2P", cursive',
                cursor: "pointer",
                borderRadius: "5px",
                boxShadow: "0 4px 6px rgba(0, 255, 0, 0.3)",
                transition: "all 0.3s ease",
              }}
              onMouseOver={(e) => e.target.style.transform = "scale(1.05)"}
              onMouseOut={(e) => e.target.style.transform = "scale(1)"}
            >
              NEW SIMULATION
            </button>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div style={{
      fontFamily: 'Arial, sans-serif',
      backgroundColor: "#000000",  // Black background for better contrast
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
        <style>{`
          body, html {
            margin: 0;
            padding: 0;
            background-color: #000000;
            overflow-x: hidden;
          }
          * {
            box-sizing: border-box;
          }
        `}</style>
      </Head>

      {/* Start New Simulation Button - Show when not started */}
      {!simulationStarted && (
        <>
          <style jsx>{`
            @keyframes glow-pulse {
              0% {
                box-shadow: 0 0 5px rgba(0, 255, 0, 0.5),
                            0 0 10px rgba(0, 255, 0, 0.5),
                            0 0 15px rgba(0, 255, 0, 0.5),
                            0 0 20px rgba(0, 255, 0, 0.3);
                transform: scale(1);
              }
              50% {
                box-shadow: 0 0 10px rgba(0, 255, 0, 0.8),
                            0 0 20px rgba(0, 255, 0, 0.8),
                            0 0 30px rgba(0, 255, 0, 0.8),
                            0 0 40px rgba(0, 255, 0, 0.5);
                transform: scale(1.05);
              }
              100% {
                box-shadow: 0 0 5px rgba(0, 255, 0, 0.5),
                            0 0 10px rgba(0, 255, 0, 0.5),
                            0 0 15px rgba(0, 255, 0, 0.5),
                            0 0 20px rgba(0, 255, 0, 0.3);
                transform: scale(1);
              }
            }
            
            .begin-button {
              animation: glow-pulse 2s ease-in-out infinite;
            }
            
            .begin-button:hover {
              animation: glow-pulse 0.5s ease-in-out infinite !important;
              transform: scale(1.1) !important;
            }
          `}</style>
          <div style={{
            position: "absolute",
            top: "40.5%",  // Centered in the middle of the arcade screen
            left: "50%",
            transform: "translate(-50%, -50%)",
            zIndex: 100,
          }}>
            <button
              className="begin-button"
            onClick={() => {
              setSimulationStarted(true);
              initializeSimulation();
            }}
            disabled={isLoading}
            style={{
              padding: "12px 24px",
              fontSize: "0.8em",
              fontFamily: '"Press Start 2P", cursive',
              backgroundColor: "#00ff00",
              color: "#000",
              border: "2px solid #004400",
              borderRadius: "6px",
              cursor: isLoading ? "not-allowed" : "pointer",
              fontWeight: "bold",
              letterSpacing: "2px",
              textShadow: "1px 1px 2px rgba(0, 0, 0, 0.5)",
              textTransform: "uppercase",
              opacity: isLoading ? 0.5 : 1,
              transition: "all 0.3s ease",
            }}
          >
            {isLoading ? "Loading..." : "Begin"}
            </button>
          </div>
        </>
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
          TURN {Math.min(turn > 0 ? turn : 1, maxTurns)}/{maxTurns}
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
            placeholder={(submissionCount >= maxTurns && !showConclusion) ? "Simulation ended." : !simulationId ? "Start a simulation first..." : "Your response..."}
            disabled={isLoading || (submissionCount >= maxTurns && !showConclusion) || !simulationId}
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
          <button type="submit" disabled={isLoading || (submissionCount >= maxTurns && !showConclusion) || !simulationId} style={{
            padding: "10px 15px",
            borderRadius: "5px",
            border: "none",
            backgroundColor: "#00ff00",
            color: "#000",
            cursor: "pointer",
            fontFamily: 'inherit',
            fontSize: "0.8em",
            opacity: (isLoading || (submissionCount >= maxTurns && !showConclusion) || !simulationId) ? 0.5 : 1,
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
      
      {/* Render Conclusion Overlay */}
      <ConclusionOverlay />
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