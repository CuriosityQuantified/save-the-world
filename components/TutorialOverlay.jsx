import React, { useEffect, useState } from "react";

const STEPS = [
  {
    title: "Welcome, crisis manager",
    description: "You will guide a crisis response across three turns. Read the situation, choose a response, and learn from the score at the end.",
  },
  {
    title: "Read the scenario",
    description: "Every turn starts with a scenario. Look for the problem, the people affected, and the goal before deciding what to do.",
  },
  {
    title: "Make your first response",
    description: "There is no single perfect answer. Pick a response below to practice making a decision, then try the real game in your own words.",
  },
  {
    title: "Advance the turns",
    description: "Your response moves the simulation forward. New information appears each turn, so adapt your plan as the situation changes.",
  },
  {
    title: "Learn from your score",
    description: "The final score reflects the impact and clarity of your choices. Treat the feedback as a guide for your next attempt.",
  },
  {
    title: "You are ready to explore",
    description: "Start a simulation whenever you are ready. You can replay this walkthrough from Settings at any time.",
  },
];

const sampleScenario = "A coastal city has lost power. The hospital has backup batteries for one hour.";

function StepIllustration({ stepIndex, selectedResponse, onSelectResponse, demoTurn, onAdvanceDemo, scoreRevealed, onRevealScore }) {
  if (stepIndex === 0) {
    return (
      <div data-testid="tutorial-welcome" style={styles.illustration}>
        <div style={styles.illustrationIcon} aria-hidden="true">✦</div>
        <strong style={styles.illustrationTitle}>Observe → Decide → Adapt</strong>
        <span style={styles.illustrationText}>The best strategy is to make a thoughtful choice, then use the next turn to improve it.</span>
      </div>
    );
  }

  if (stepIndex === 1) {
    return (
      <div data-testid="tutorial-sample-scenario" style={styles.scenarioCard}>
        <span style={styles.cardLabel}>SAMPLE SCENARIO</span>
        <p style={styles.scenarioText}>{sampleScenario}</p>
        <span style={styles.scenarioHint}>Hint: prioritize the people at greatest risk.</span>
      </div>
    );
  }

  if (stepIndex === 2) {
    return (
      <div data-testid="tutorial-response-choice" style={styles.interactiveCard}>
        <span style={styles.cardLabel}>CHOOSE A RESPONSE</span>
        <div style={styles.choiceList}>
          <button
            type="button"
            data-testid="tutorial-response-protect"
            onClick={() => onSelectResponse("protect")}
            aria-pressed={selectedResponse === "protect"}
            style={{ ...styles.choiceButton, ...(selectedResponse === "protect" ? styles.choiceButtonSelected : {}) }}
          >
            Protect the hospital first
          </button>
          <button
            type="button"
            data-testid="tutorial-response-restore"
            onClick={() => onSelectResponse("restore")}
            aria-pressed={selectedResponse === "restore"}
            style={{ ...styles.choiceButton, ...(selectedResponse === "restore" ? styles.choiceButtonSelected : {}) }}
          >
            Restore the city grid
          </button>
        </div>
        <span data-testid="tutorial-response-feedback" style={styles.feedback}>
          {selectedResponse ? "Good choice — the next turn will reveal its consequences." : "Select an option to continue."}
        </span>
      </div>
    );
  }

  if (stepIndex === 3) {
    return (
      <div data-testid="tutorial-turn-demo" style={styles.interactiveCard}>
        <span style={styles.cardLabel}>TURN PROGRESSION</span>
        <div data-testid="tutorial-turn-indicator" style={styles.turnIndicator}>TURN {demoTurn} / 3</div>
        <p style={styles.illustrationText}>
          {demoTurn === 1 ? "Your first response is in. Advance the demo to see how a new turn builds on it." : "Turn 2 brings new information. Re-read the situation and adapt your next response."}
        </p>
        <button type="button" data-testid="tutorial-advance-turn" onClick={onAdvanceDemo} disabled={demoTurn > 1} style={styles.secondaryButton}>
          {demoTurn > 1 ? "Turn advanced" : "Advance demo turn"}
        </button>
      </div>
    );
  }

  if (stepIndex === 4) {
    return (
      <div data-testid="tutorial-score-demo" style={styles.interactiveCard}>
        <span style={styles.cardLabel}>SAMPLE SCORE</span>
        {scoreRevealed ? (
          <div data-testid="tutorial-score-result" style={styles.scoreGrid}>
            <div><strong style={styles.scoreValue}>80</strong><span style={styles.scoreLabel}>Impact</span></div>
            <div><strong style={styles.scoreValue}>90</strong><span style={styles.scoreLabel}>Clarity</span></div>
            <div><strong style={styles.scoreValue}>85</strong><span style={styles.scoreLabel}>Overall</span></div>
          </div>
        ) : (
          <button type="button" data-testid="tutorial-reveal-score" onClick={onRevealScore} style={styles.secondaryButton}>
            Reveal sample score
          </button>
        )}
        <span style={styles.feedback}>{scoreRevealed ? "Use the feedback to shape a stronger next response." : "Reveal the score to see how choices are evaluated."}</span>
      </div>
    );
  }

  return (
    <div data-testid="tutorial-ready" style={styles.illustration}>
      <div style={styles.illustrationIcon} aria-hidden="true">✓</div>
      <strong style={styles.illustrationTitle}>Start with a clear plan</strong>
      <span style={styles.illustrationText}>You can pause, skip, or replay the tutorial from Settings whenever you need a refresher.</span>
    </div>
  );
}

export default function TutorialOverlay({ isOpen, onComplete, onSkip }) {
  const [stepIndex, setStepIndex] = useState(0);
  const [selectedResponse, setSelectedResponse] = useState(null);
  const [demoTurn, setDemoTurn] = useState(1);
  const [scoreRevealed, setScoreRevealed] = useState(false);

  useEffect(() => {
    if (isOpen) {
      setStepIndex(0);
      setSelectedResponse(null);
      setDemoTurn(1);
      setScoreRevealed(false);
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const needsResponse = stepIndex === 2 && !selectedResponse;
  const needsTurnAdvance = stepIndex === 3 && demoTurn === 1;
  const needsScoreReveal = stepIndex === 4 && !scoreRevealed;
  const canContinue = !needsResponse && !needsTurnAdvance && !needsScoreReveal;
  const isLastStep = stepIndex === STEPS.length - 1;

  const handleContinue = () => {
    if (!canContinue) return;
    if (isLastStep) {
      onComplete();
      return;
    }
    setStepIndex((current) => current + 1);
  };

  const currentStep = STEPS[stepIndex];

  return (
    <div role="dialog" aria-modal="true" aria-labelledby="tutorial-title" data-testid="tutorial-overlay" style={styles.overlay}>
      <div style={styles.modal}>
        <div style={styles.progressRow}>
          <span style={styles.eyebrow}>INTERACTIVE TUTORIAL</span>
          <span data-testid="tutorial-progress" style={styles.progress}>STEP {stepIndex + 1} OF {STEPS.length}</span>
        </div>
        <div style={styles.progressTrack} aria-hidden="true">
          <div style={{ ...styles.progressBar, width: `${((stepIndex + 1) / STEPS.length) * 100}%` }} />
        </div>

        <h1 id="tutorial-title" data-testid="tutorial-title" style={styles.title}>{currentStep.title}</h1>
        <p data-testid="tutorial-description" style={styles.description}>{currentStep.description}</p>

        <StepIllustration
          stepIndex={stepIndex}
          selectedResponse={selectedResponse}
          onSelectResponse={setSelectedResponse}
          demoTurn={demoTurn}
          onAdvanceDemo={() => setDemoTurn(2)}
          scoreRevealed={scoreRevealed}
          onRevealScore={() => setScoreRevealed(true)}
        />

        <div style={styles.actions}>
          <button type="button" data-testid="tutorial-skip" onClick={onSkip} style={styles.skipButton}>Skip tutorial</button>
          <div style={styles.navigation}>
            {stepIndex > 0 && (
              <button type="button" data-testid="tutorial-back" onClick={() => setStepIndex((current) => current - 1)} style={styles.backButton}>Back</button>
            )}
            <button type="button" data-testid="tutorial-next" onClick={handleContinue} disabled={!canContinue} style={{ ...styles.nextButton, ...(!canContinue ? styles.nextButtonDisabled : {}) }}>
              {isLastStep ? "Finish tutorial" : "Continue"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

const styles = {
  overlay: {
    position: "fixed",
    inset: 0,
    zIndex: 2000,
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    padding: "16px",
    backgroundColor: "rgba(0, 0, 0, 0.88)",
    color: "#fff",
    fontFamily: "Arial, sans-serif",
  },
  modal: {
    width: "min(100%, 760px)",
    maxHeight: "92vh",
    overflowY: "auto",
    padding: "28px",
    border: "2px solid #00ff00",
    borderRadius: "12px",
    background: "linear-gradient(145deg, #101c18, #111827)",
    boxShadow: "0 0 35px rgba(0, 255, 0, 0.28)",
  },
  progressRow: {
    display: "flex",
    justifyContent: "space-between",
    gap: "12px",
    alignItems: "center",
    color: "#9ca3af",
    fontSize: "12px",
    letterSpacing: "1px",
  },
  eyebrow: { color: "#00ff00", fontWeight: 700 },
  progress: { whiteSpace: "nowrap" },
  progressTrack: {
    height: "5px",
    marginTop: "12px",
    marginBottom: "26px",
    overflow: "hidden",
    borderRadius: "999px",
    backgroundColor: "#263238",
  },
  progressBar: { height: "100%", borderRadius: "999px", backgroundColor: "#00ff00", transition: "width 0.2s ease" },
  title: { margin: "0 0 10px", color: "#fff", fontSize: "clamp(24px, 4vw, 34px)" },
  description: { margin: "0 0 22px", color: "#d1d5db", fontSize: "16px", lineHeight: 1.55 },
  illustration: {
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    gap: "10px",
    minHeight: "170px",
    justifyContent: "center",
    padding: "24px",
    border: "1px solid #35594a",
    borderRadius: "10px",
    backgroundColor: "rgba(0, 255, 0, 0.05)",
    textAlign: "center",
  },
  illustrationIcon: { color: "#00ff00", fontSize: "40px" },
  illustrationTitle: { color: "#b7ffca", fontSize: "18px" },
  illustrationText: { color: "#c7d2d0", fontSize: "14px", lineHeight: 1.5 },
  scenarioCard: { padding: "22px", border: "1px solid #345a87", borderRadius: "10px", backgroundColor: "rgba(0, 140, 255, 0.1)" },
  cardLabel: { display: "block", marginBottom: "12px", color: "#67e8f9", fontSize: "11px", fontWeight: 700, letterSpacing: "1.4px" },
  scenarioText: { margin: "0 0 14px", color: "#fff", fontSize: "19px", lineHeight: 1.5 },
  scenarioHint: { color: "#9ca3af", fontSize: "13px" },
  interactiveCard: { padding: "22px", border: "1px solid #4b5563", borderRadius: "10px", backgroundColor: "rgba(17, 24, 39, 0.9)" },
  choiceList: { display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: "12px" },
  choiceButton: { minHeight: "52px", padding: "12px", border: "1px solid #4b5563", borderRadius: "7px", backgroundColor: "#1f2937", color: "#e5e7eb", cursor: "pointer", fontSize: "14px" },
  choiceButtonSelected: { borderColor: "#00ff00", backgroundColor: "#123b24", color: "#b7ffca" },
  feedback: { display: "block", marginTop: "16px", color: "#9ca3af", fontSize: "13px" },
  turnIndicator: { display: "inline-block", marginBottom: "14px", padding: "9px 14px", borderRadius: "6px", color: "#00ff00", backgroundColor: "#123b24", fontWeight: 700, letterSpacing: "1px" },
  secondaryButton: { minHeight: "44px", padding: "10px 16px", border: "1px solid #67e8f9", borderRadius: "6px", backgroundColor: "#0f2933", color: "#a5f3fc", cursor: "pointer", fontWeight: 700 },
  scoreGrid: { display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: "12px", marginBottom: "12px", textAlign: "center" },
  scoreValue: { display: "block", color: "#00ff00", fontSize: "28px" },
  scoreLabel: { display: "block", marginTop: "5px", color: "#d1d5db", fontSize: "12px" },
  actions: { display: "flex", justifyContent: "space-between", alignItems: "center", gap: "12px", marginTop: "28px" },
  navigation: { display: "flex", gap: "10px", marginLeft: "auto" },
  skipButton: { minHeight: "44px", padding: "10px 14px", border: "none", background: "transparent", color: "#9ca3af", cursor: "pointer", textDecoration: "underline" },
  backButton: { minHeight: "44px", padding: "10px 16px", border: "1px solid #4b5563", borderRadius: "6px", backgroundColor: "transparent", color: "#d1d5db", cursor: "pointer" },
  nextButton: { minHeight: "44px", padding: "10px 18px", border: "2px solid #00ff00", borderRadius: "6px", backgroundColor: "#00ff00", color: "#061006", cursor: "pointer", fontWeight: 700 },
  nextButtonDisabled: { borderColor: "#4b5563", backgroundColor: "#374151", color: "#9ca3af", cursor: "not-allowed" },
};
