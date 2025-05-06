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
    <div style={{
      backgroundImage: "url(/UI_background.jpeg)",
      backgroundSize: "cover",
      backgroundPosition: "center",
      backgroundRepeat: "no-repeat",
      minHeight: "100vh",
      display: "flex",
      justifyContent: "center",
      alignItems: "center",
      position: "relative",
      fontFamily: '"Press Start 2P", cursive',
      color: "#fff",
    }}>
      <Head>
        <title>Simulation Arcade</title>
        <link href="https://fonts.googleapis.com/css2?family=Press+Start+2P&display=swap" rel="stylesheet" />
      </Head>

      {/* Arcade Screen Content Area */}
      <div style={{
        position: "absolute",
        top: "22%",
        left: "50%",
        transform: "translateX(-50%)",
        width: "56%",
        height: "50%",
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
        }}>
          TURN {turn}/{MAX_TURNS}
        </div>

        {/* Content Grid */}
        <div style={{
          display: "grid",
          gridTemplateColumns: "1fr 1fr",
          gap: "15px",
          flex: 1,
          overflow: "hidden",
        }}>
          {/* Video Section */}
          <div style={{
            backgroundColor: "#111",
            border: "2px solid #444",
            borderRadius: "5px",
            overflow: "hidden",
            display: "flex",
            justifyContent: "center",
            alignItems: "center",
          }}>
            {videoUrl ? (
              <video
                key={videoUrl}
                controls
                autoPlay
                muted
                style={{ maxWidth: "100%", maxHeight: "100%" }}
              >
                <source src={videoUrl} type="video/mp4" />
                Your browser does not support the video tag.
              </video>
            ) : (
              <p style={{ color: "#666", textAlign: "center" }}>
                {isLoading ? "Generating video..." : "Video will appear here"}
              </p>
            )}
          </div>

          {/* Scenario Section */}
          <div style={{
            display: "flex",
            flexDirection: "column",
            gap: "10px",
            overflow: "hidden",
          }}>
            <div style={{
              flex: 1,
              backgroundColor: "#222",
              border: "2px solid #444",
              padding: "10px",
              borderRadius: "5px",
              overflow: "auto",
              fontSize: "0.8em",
              lineHeight: "1.4",
            }}>
              {isLoading ? "Loading scenario..." : scenario}
            </div>

            {/* Audio Player */}
            {narrationUrl && (
              <audio
                key={narrationUrl}
                controls
                style={{ width: "100%" }}
              >
                <source src={narrationUrl} type="audio/mpeg" />
                Your browser does not support the audio element.
              </audio>
            )}
          </div>
        </div>

        {/* Input Section */}
        <form onSubmit={handleSubmit} style={{
          marginTop: "15px",
          display: "flex",
          gap: "10px",
        }}>
          <input
            ref={inputRef}
            type="text"
            value={userInput}
            onChange={(e) => setUserInput(e.target.value)}
            placeholder={isLoading ? "Waiting..." : "Enter your response..."}
            disabled={isLoading || turn >= MAX_TURNS}
            style={{
              flex: 1,
              padding: "8px",
              backgroundColor: "#111",
              border: "2px solid #444",
              borderRadius: "5px",
              color: "#fff",
              fontFamily: "inherit",
              fontSize: "0.8em",
            }}
          />
          <button
            type="submit"
            disabled={isLoading || turn >= MAX_TURNS || !userInput.trim()}
            style={{
              padding: "8px 15px",
              backgroundColor: "#3a3",
              border: "none",
              borderRadius: "5px",
              color: "#fff",
              fontFamily: "inherit",
              fontSize: "0.8em",
              cursor: "pointer",
              opacity: isLoading || turn >= MAX_TURNS || !userInput.trim() ? 0.5 : 1,
            }}
          >
            SEND
          </button>
        </form>
      </div>
    </div>
  );
}

// Keep the getServerSideProps function unchanged
export async function getServerSideProps() {
  try {
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