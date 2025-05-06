import React, { useState, useEffect, useRef } from "react";
import Head from "next/head";
import MediaHandler from "../components/MediaHandler";

export default function SimulationPage({ initialScenario }) {
  const [scenario, setScenario] = useState(
    initialScenario || {
      situation_description: "Loading situation...",
      video_url: null,
      audio_url: null,
    },
  );

  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [turn, setTurn] = useState(0);
  const [MAX_TURNS, setMAX_TURNS] = useState(10);
  const [userInput, setUserInput] = useState("");
  const [videoUrl, setVideoUrl] = useState("");
  const [narrationUrl, setNarrationUrl] = useState("");
  const [history, setHistory] = useState([]);
  const inputRef = useRef(null);
  const chatEndRef = useRef(null);

  // Function to load a scenario
  const loadScenario = async () => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch("/api/scenario");
      if (!response.ok) {
        throw new Error(`Failed to fetch scenario: ${response.status}`);
      }

      const data = await response.json();
      setScenario(data);
    } catch (err) {
      console.error("Error loading scenario:", err);
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

  // Function to handle user response submission
  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!userInput.trim() || isLoading || turn >= MAX_TURNS) return;

    setIsLoading(true);
    setHistory((prev) => [...prev, { role: "user", content: userInput }]);
    setUserInput(""); // Clear input after sending

    try {
      // Call API to get the next turn's data
      const response = await fetch("/api/simulation/turn", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          turn: turn + 1,
          history: [...history, { role: "user", content: userInput }],
        }), // Send current turn + 1 and full history
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();

      console.log("Received data for turn:", turn + 1, data); // Log received data

      // Update state with new data
      setScenario(data.scenario || "Scenario generation failed.");
      setVideoUrl(data.videoUrl || "");
      setNarrationUrl(data.narrationUrl || "");
      setTurn((prev) => prev + 1); // Increment turn *after* successful processing
      setHistory((prev) => [
        ...prev,
        {
          role: "assistant",
          content: data.scenario || "No scenario generated.",
        },
      ]); // Add assistant response to history
    } catch (error) {
      console.error("Error fetching next turn:", error);
      setScenario(`Error advancing simulation: ${error.message}`);
      // Optionally reset or handle the error state further
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    // Focus the input field when the component mounts or updates
    if (inputRef.current) {
      inputRef.current.focus();
    }
    // Scroll to bottom when history updates
    if (chatEndRef.current) {
      chatEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [history, isLoading]); // Depend on history and loading state

  // Initial Turn Logic (Turn 0)
  useEffect(() => {
    const initializeSimulation = async () => {
      setIsLoading(true);
      try {
        console.log("Initializing simulation (Turn 0)");
        const response = await fetch("/api/simulation/turn", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ turn: 0, history: [] }), // Start with turn 0 and empty history
        });

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        console.log("Received data for Turn 0:", data);

        setScenario(
          data.scenario || "Welcome! Scenario generation failed for the start.",
        );
        setVideoUrl(data.videoUrl || "");
        setNarrationUrl(data.narrationUrl || "");
        setTurn(1); // Set turn to 1 after initialization
        setHistory([
          { role: "assistant", content: data.scenario || "Welcome!" },
        ]); // Initialize history
      } catch (error) {
        console.error("Error initializing simulation:", error);
        setScenario(`Error starting simulation: ${error.message}`);
      } finally {
        setIsLoading(false);
      }
    };

    initializeSimulation();
  }, []); // Empty dependency array ensures this runs only once on mount

  return (
    <div
      style={{
        backgroundImage: "url(/UI_background.jpeg)", // Use the image from public folder
        backgroundSize: "cover",
        backgroundPosition: "center",
        backgroundRepeat: "no-repeat",
        minHeight: "100vh", // Ensure it covers the full viewport height
        display: "flex",
        justifyContent: "center",
        alignItems: "center", // Center the arcade machine content area
        position: "relative", // Needed for absolute positioning of children
        fontFamily: '"Press Start 2P", cursive', // Example pixel font
        color: "#fff", // Default text color
      }}
    >
      <Head>
        <title>Arcade Simulation</title>
        {/* Add pixel font link if needed */}
        <link
          href="https://fonts.googleapis.com/css2?family=Press+Start+2P&display=swap"
          rel="stylesheet"
        />
      </Head>

      {/* Area representing the arcade screen */}
      {/* Adjust top, left, width, height based on the image dimensions and screen location */}
      <div
        style={{
          position: "absolute",
          top: "22%", // Approximate top position of the screen
          left: "50%", // Center horizontally
          transform: "translateX(-50%)", // Correct centering
          width: "56%", // Approximate width of the screen area
          height: "50%", // Approximate height of the screen area
          backgroundColor: "rgba(0, 0, 0, 0.8)", // Semi-transparent black background for readability
          border: "5px solid #333", // Optional border to mimic screen frame
          borderRadius: "10px", // Optional rounded corners
          padding: "20px",
          boxSizing: "border-box",
          display: "flex",
          flexDirection: "column",
          overflow: "hidden", // Hide overflow
        }}
      >
        {/* Top Section: Video Player & Scenario */}
        <div
          style={{
            flex: 1,
            display: "flex",
            gap: "15px",
            marginBottom: "15px",
            overflow: "hidden",
          }}
        >
          {/* Video Player Area */}
          <div
            style={{
              flex: "0 0 60%",
              backgroundColor: "#111",
              border: "2px solid #444",
              borderRadius: "5px",
              display: "flex",
              justifyContent: "center",
              alignItems: "center",
              overflow: "hidden",
            }}
          >
            {isLoading && !videoUrl && <p>Generating video...</p>}
            {!isLoading && !videoUrl && <p>Video will appear here.</p>}
            {videoUrl && (
              <video
                key={videoUrl}
                controls
                autoPlay
                muted
                style={{
                  maxWidth: "100%",
                  maxHeight: "100%",
                  display: "block",
                }}
              >
                <source src={videoUrl} type="video/mp4" />
                Your browser does not support the video tag.
              </video>
            )}
          </div>

          {/* Scenario & Narration Area */}
          <div
            style={{
              flex: 1,
              display: "flex",
              flexDirection: "column",
              gap: "10px",
              overflowY: "auto",
              paddingRight: "10px",
            }}
          >
            {/* Scenario Text */}
            <div
              style={{
                backgroundColor: "#222",
                border: "2px solid #444",
                padding: "10px",
                borderRadius: "5px",
                flexShrink: 0,
              }}
            >
              <h2
                style={{
                  fontSize: "1.1em",
                  marginBottom: "5px",
                  borderBottom: "1px solid #555",
                  paddingBottom: "5px",
                }}
              >
                Scenario (Turn {turn}/{MAX_TURNS})
              </h2>
              {isLoading && !scenario && <p>Loading scenario...</p>}
              <p style={{ fontSize: "0.9em", lineHeight: "1.4" }}>{scenario}</p>
            </div>

            {/* Narration Audio */}
            {narrationUrl && (
              <div
                style={{
                  backgroundColor: "#222",
                  border: "2px solid #444",
                  padding: "10px",
                  borderRadius: "5px",
                  flexShrink: 0,
                }}
              >
                <h3 style={{ fontSize: "1em", marginBottom: "5px" }}>
                  Narration
                </h3>
                <audio key={narrationUrl} controls style={{ width: "100%" }}>
                  <source src={narrationUrl} type="audio/mpeg" />
                  Your browser does not support the audio element.
                </audio>
              </div>
            )}
            {isLoading && !narrationUrl && <p>Generating narration...</p>}
          </div>
        </div>

        {/* Bottom Section: User Input */}
        <form onSubmit={handleSubmit} style={{ display: "flex", gap: "10px" }}>
          <input
            ref={inputRef}
            type="text"
            value={userInput}
            onChange={(e) => setUserInput(e.target.value)}
            placeholder={
              isLoading
                ? "Waiting for next turn..."
                : turn > MAX_TURNS
                  ? "Simulation Complete."
                  : "Enter your response..."
            }
            disabled={isLoading || turn > MAX_TURNS}
            style={{
              flexGrow: 1,
              padding: "10px",
              border: "2px solid #444",
              borderRadius: "5px",
              backgroundColor: "#111",
              color: "#fff",
              fontFamily: "inherit", // Inherit pixel font
              fontSize: "1em",
            }}
          />
          <button
            type="submit"
            disabled={isLoading || turn > MAX_TURNS || !userInput.trim()}
            style={{
              padding: "10px 15px",
              border: "2px solid #444",
              borderRadius: "5px",
              backgroundColor: "#3a3", // Greenish button
              color: "#fff",
              fontFamily: "inherit",
              fontSize: "1em",
              cursor: "pointer",
              opacity:
                isLoading || turn > MAX_TURNS || !userInput.trim() ? 0.5 : 1,
            }}
          >
            Send
          </button>
        </form>

        {/* Optional Chat History Area (if needed within the screen) */}
        {/* <div ref={chatContainerRef} style={{ flexGrow: 1, overflowY: 'auto', marginTop: '10px', border: '1px solid #ccc', padding: '5px' }}>
          {history.map((msg, index) => (
            <p key={index} style={{ color: msg.role === 'user' ? 'lightgreen' : 'lightblue' }}>
              <strong>{msg.role === 'user' ? 'You:' : 'System:'}</strong> {msg.content}
            </p>
          ))}
          <div ref={chatEndRef} />
        </div> */}
      </div>

      {/* Floating turn counter or other UI elements outside the screen if desired */}
      {/* <div style={{ position: 'absolute', top: '10px', right: '10px', backgroundColor: 'rgba(0,0,0,0.7)', padding: '5px 10px', borderRadius: '5px' }}>
          Turn: {turn}/{MAX_TURNS}
      </div> */}
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
        initialScenario: null,
      },
    };
  } catch (error) {
    return {
      props: {
        initialScenario: null,
      },
    };
  }
}
