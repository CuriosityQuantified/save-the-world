
export default function handler(req, res) {
  const scenario = {
    situation_description: "In a bizarre turn of events, all the world's coffee has suddenly turned into liquid gold. While this might seem like an economic windfall, it has thrown the global workforce into chaos as millions struggle to stay awake and productive.",
    user_role: "Global Crisis Management Specialist",
    user_prompt: "How would you handle this unprecedented situation and prevent global economic collapse while dealing with a severely caffeine-deprived population?",
    video_url: null,
    audio_url: null
  };
  
  setTimeout(() => {
    res.status(200).json(scenario);
  }, 1000);
}
