/**
 * API endpoint to fetch a simulation scenario
 * 
 * This would normally connect to your backend services
 * but for testing purposes it returns a sample scenario
 */
export default function handler(req, res) {
  // Sample scenario data with media URLs
  const scenario = {
    situation_description: "You are attending an important business meeting with potential investors. The presentation is about to begin, but you notice a critical error in the financial projections slide.",
    user_role: "Senior Business Analyst",
    user_prompt: "How would you handle this situation in front of the investors?",
    video_url: "/media/videos/sample_video.mp4", // Points to public/media/videos/sample_video.mp4
    audio_url: "/media/audio/sample_audio.mp3"   // Points to public/media/audio/sample_audio.mp3
  };
  
  // Simulate a slight delay to test loading state
  setTimeout(() => {
    res.status(200).json(scenario);
  }, 500);
} 