import React, { useState, useEffect, useRef } from 'react';

/**
 * MediaHandler component for displaying a sequence of videos and a synchronized audio track.
 */
const MediaHandler = ({ video_urls, audio_url, type = 'video/mp4', width = '100%', height = 'auto' }) => {
  console.log('MediaHandler props:', { video_urls, audio_url, type, width, height });

  const [error, setError] = useState(false);
  const [currentVideoIndex, setCurrentVideoIndex] = useState(0);
  const [activeVideoUrl, setActiveVideoUrl] = useState('');
  const [activeAudioUrl, setActiveAudioUrl] = useState('');

  const [isPlaying, setIsPlaying] = useState(false);
  const [allMediaReady, setAllMediaReady] = useState(false); 
  const [currentVideoReady, setCurrentVideoReady] = useState(false);
  const [nextVideoReady, setNextVideoReady] = useState(false);
  const [audioElementReady, setAudioElementReady] = useState(false);
  
  // Loading progress states
  const [videosLoading, setVideosLoading] = useState(0);
  const [videosTotal, setVideosTotal] = useState(0);
  const [showPlayButton, setShowPlayButton] = useState(false);
  const [hasUserInteracted, setHasUserInteracted] = useState(false);
  const [showLoadingProgress, setShowLoadingProgress] = useState(true);

  // Using two video elements for seamless playback (one plays while the other preloads)
  const primaryVideoRef = useRef(null);
  const bufferVideoRef = useRef(null);
  const audioRef = useRef(null);

  // Track which ref is currently active (primary or buffer)
  const [activeVideoRef, setActiveVideoRef] = useState('primary');
  const activeRef = activeVideoRef === 'primary' ? primaryVideoRef : bufferVideoRef;
  const inactiveRef = activeVideoRef === 'primary' ? bufferVideoRef : primaryVideoRef;

  const validVideoUrls = useRef([]);
  
  useEffect(() => {
    // Filter out null or empty URLs and prepare the playlist
    const playlist = [];
    if (Array.isArray(video_urls)) {
      video_urls.forEach(url => {
        if (url && typeof url === 'string') {
          const formattedUrl = url.startsWith('http') ? url : '/' + url.replace(/^\/+/, '');
          playlist.push(formattedUrl); // Each video plays once
        }
      });
    }
    validVideoUrls.current = playlist;
    console.log("Processed video playlist:", validVideoUrls.current);
    
    // Set total videos count for loading progress
    setVideosTotal(playlist.length);
    setVideosLoading(0);
    setShowLoadingProgress(true);

    setCurrentVideoIndex(0);
    setActiveVideoUrl(validVideoUrls.current.length > 0 ? validVideoUrls.current[0] : '');
    setCurrentVideoReady(false);
    setNextVideoReady(false);
    setAllMediaReady(false);
    
    // Format and set the audio URL
    if (audio_url && typeof audio_url === 'string') {
      const formattedAudio = audio_url.startsWith('http') ? audio_url : '/' + audio_url.replace(/^\/+/, '');
      setActiveAudioUrl(formattedAudio);
      console.log(`Setting audio URL to: ${formattedAudio}`);
      setAudioElementReady(false);
    } else {
      console.log('No audio source provided or invalid format');
      setActiveAudioUrl('');
      setAudioElementReady(true);
    }
    
    // Reset to primary video ref when playlist changes
    setActiveVideoRef('primary');
  }, [video_urls, audio_url]);

  // Load the current video in the active player
  useEffect(() => {
    const video = activeRef.current;
    if (!video || !activeVideoUrl) {
      setCurrentVideoReady(validVideoUrls.current.length === 0);
      return;
    }
    
    console.log(`Loading current video in ${activeVideoRef} player: ${activeVideoUrl}`);
    video.src = activeVideoUrl;
    video.load();
    
    const handleVideoCanPlay = () => {
      console.log(`Current video ${activeVideoUrl} can play`);
      setCurrentVideoReady(true);
      setVideosLoading(prev => prev + 1);
      setError(false);
    };
    
    const handleVideoError = (e) => {
      console.error(`Video error for ${activeVideoUrl}:`, e);
      setCurrentVideoReady(false);
      setVideosLoading(prev => prev + 1); // Still count as processed
      setError(true);
      // Attempt to play next video if this one fails
      handleVideoEnded(); 
    };

    video.addEventListener('canplay', handleVideoCanPlay);
    video.addEventListener('error', handleVideoError);
    
    return () => {
      video.removeEventListener('canplay', handleVideoCanPlay);
      video.removeEventListener('error', handleVideoError);
    };
  }, [activeVideoUrl, activeVideoRef]);
  
  // Preload the next video in the inactive player
  useEffect(() => {
    // Only preload if we have more than one video
    if (validVideoUrls.current.length <= 1) {
      setNextVideoReady(true);
      return;
    }
    
    const nextVideoIndex = (currentVideoIndex + 1) % validVideoUrls.current.length;
    const nextVideoUrl = validVideoUrls.current[nextVideoIndex];
    const bufferVideo = inactiveRef.current;
    
    if (!bufferVideo || !nextVideoUrl) {
      return;
    }
    
    console.log(`Preloading next video in ${activeVideoRef === 'primary' ? 'buffer' : 'primary'} player: ${nextVideoUrl}`);
    bufferVideo.src = nextVideoUrl;
    bufferVideo.load();
    
    const handleBufferCanPlay = () => {
      console.log(`Next video ${nextVideoUrl} is ready in buffer`);
      setNextVideoReady(true);
    };
    
    const handleBufferError = (e) => {
      console.error(`Error preloading next video ${nextVideoUrl}:`, e);
      setNextVideoReady(false);
    };
    
    bufferVideo.addEventListener('canplay', handleBufferCanPlay);
    bufferVideo.addEventListener('error', handleBufferError);
    
    return () => {
      bufferVideo.removeEventListener('canplay', handleBufferCanPlay);
      bufferVideo.removeEventListener('error', handleBufferError);
    };
  }, [currentVideoIndex, activeVideoRef, validVideoUrls.current.length]);
  
  // Effect to handle loading of the audio element
  useEffect(() => {
    const audio = audioRef.current;
    if (!audio || !activeAudioUrl) {
      setAudioElementReady(true);
      return;
    }
    
    console.log(`Setting up audio element with source: ${activeAudioUrl}`);
    audio.src = activeAudioUrl;
    audio.load();
    
    const handleAudioCanPlay = () => {
      console.log('Audio can play');
      setAudioElementReady(true);
    };
    
    const handleAudioError = (e) => {
      console.error('Audio error:', e, `URL: ${activeAudioUrl}`);
      setAudioElementReady(true);
    };

    audio.addEventListener('canplaythrough', handleAudioCanPlay);
    audio.addEventListener('error', handleAudioError);
    
    return () => {
      audio.removeEventListener('canplaythrough', handleAudioCanPlay);
      audio.removeEventListener('error', handleAudioError);
    };
  }, [activeAudioUrl]);
  
  // Update overall media readiness
  useEffect(() => {
    if (validVideoUrls.current.length === 0) {
        setAllMediaReady(true);
        // Don't hide progress immediately, leave it visible for a moment
        setTimeout(() => setShowLoadingProgress(false), 1000);
    } else {
        setAllMediaReady(currentVideoReady && audioElementReady);
        if (currentVideoReady && audioElementReady) {
          // Hide loading progress after a longer delay to ensure user sees completion
          setTimeout(() => setShowLoadingProgress(false), 1500);
        }
    }
  }, [currentVideoReady, audioElementReady, validVideoUrls.current.length]);

  // Show play button when media is ready (don't auto-play)
  useEffect(() => {
    if (allMediaReady && activeRef.current && validVideoUrls.current.length > 0) {
      console.log("All media ready, showing play button for user interaction.");
      setShowPlayButton(true);
    }
  }, [allMediaReady, activeVideoUrl]);

  const playCurrentMedia = () => {
    const video = activeRef.current;
    const audio = audioRef.current;
    
    if (video) {
      video.play().then(() => {
        setIsPlaying(true);
        setShowPlayButton(false);
        setHasUserInteracted(true);
        if (audio && activeAudioUrl && audio.readyState >= HTMLMediaElement.HAVE_ENOUGH_DATA) {
          if (currentVideoIndex === 0) {
            audio.currentTime = 0;
            audio.play().catch(e => console.error('Error playing audio:', e));
          } else if (audio.paused && activeAudioUrl) {
             audio.play().catch(e => console.error('Error resuming audio:', e));
          }
        }
      }).catch(e => {
        console.error('Error playing video:', e);
        // Show play button if autoplay fails and user hasn't interacted yet
        if (!hasUserInteracted) {
          setShowPlayButton(true);
        } else {
          setError(true);
          handleVideoEnded();
        }
      });
    }
  };

  // Handler for when a video finishes playing - swap to the preloaded buffer video
  const handleVideoEnded = () => {
    console.log(`Video ${activeVideoUrl} ended. Current index: ${currentVideoIndex}`);
    setIsPlaying(false);
    
    // Check if next video is ready in buffer
    if (!nextVideoReady) {
      console.log("Next video not ready yet, waiting...");
      // Wait a short time and try again
      setTimeout(handleVideoEnded, 20);
      return;
    }
    
    // Swap the video refs (primary <-> buffer)
    setActiveVideoRef(prev => prev === 'primary' ? 'buffer' : 'primary');
    
    // Update the currentVideoIndex for the next video
    const nextVideoIndex = (currentVideoIndex + 1) % validVideoUrls.current.length;
    setCurrentVideoIndex(nextVideoIndex);
    setActiveVideoUrl(validVideoUrls.current[nextVideoIndex]);
    
    // Reset readiness states for the swap
    setCurrentVideoReady(nextVideoReady); // The buffer video is now current
    setNextVideoReady(false);         // Need to load the next buffer video
  };

  // Video ended event handlers for both players
  useEffect(() => {
    const primaryVideo = primaryVideoRef.current;
    const bufferVideo = bufferVideoRef.current;
    
    if (!primaryVideo || !bufferVideo) return;
    
    const handlePrimaryEnded = () => {
      if (activeVideoRef === 'primary') {
        handleVideoEnded();
      }
    };
    
    const handleBufferEnded = () => {
      if (activeVideoRef === 'buffer') {
        handleVideoEnded();
      }
    };
    
    primaryVideo.addEventListener('ended', handlePrimaryEnded);
    bufferVideo.addEventListener('ended', handleBufferEnded);
    
    return () => {
      primaryVideo.removeEventListener('ended', handlePrimaryEnded);
      bufferVideo.removeEventListener('ended', handleBufferEnded);
    };
  }, [activeVideoRef, currentVideoIndex, nextVideoReady]);

  // Play/pause synchronization between video and audio
  useEffect(() => {
    const primaryVideo = primaryVideoRef.current;
    const bufferVideo = bufferVideoRef.current;
    const audio = audioRef.current;
    
    if (!primaryVideo || !bufferVideo || !audio) return;
    
    const syncPlay = (videoElement) => {
      if (audio.src && !audio.paused && videoElement.paused) {
        videoElement.play().catch(e => console.log('Error syncing video play:', e));
      }
    };
    
    const syncPause = (videoElement) => {
      if (audio.src && !videoElement.paused && audio.paused) {
        videoElement.pause();
      } else if (audio.src && !audio.paused && videoElement.paused) {
        videoElement.play().catch(e => console.log('Error resuming video on audio play:', e));
      }
    };
    
    const handleAudioPlay = () => {
      syncPlay(activeVideoRef === 'primary' ? primaryVideo : bufferVideo);
    };
    
    const handleAudioPause = () => {
      syncPause(activeVideoRef === 'primary' ? primaryVideo : bufferVideo);
    };
    
    audio.addEventListener('play', handleAudioPlay);
    audio.addEventListener('pause', handleAudioPause);
    
    return () => {
      audio.removeEventListener('play', handleAudioPlay);
      audio.removeEventListener('pause', handleAudioPause);
    };
  }, [activeVideoRef]);

  // When audio ends, pause the video but keep it visible
  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) return;
    
    const handleAudioEnd = () => {
      console.log("Audio ended, stopping video loop");
      // When audio ends, pause both videos but keep them visible
      if (primaryVideoRef.current && !primaryVideoRef.current.paused) {
        console.log("Pausing primary video");
        primaryVideoRef.current.pause();
      }
      if (bufferVideoRef.current && !bufferVideoRef.current.paused) {
        console.log("Pausing buffer video");
        bufferVideoRef.current.pause();
      }
      setIsPlaying(false);
      // Ensure we don't automatically continue to the next video
      setCurrentVideoReady(false);
      setNextVideoReady(false);
    };
    
    audio.addEventListener('ended', handleAudioEnd);
    
    return () => {
      audio.removeEventListener('ended', handleAudioEnd);
    };
  }, [activeAudioUrl]);

  // Cleanup audio on unmount
  useEffect(() => {
    return () => {
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current.src = '';
      }
      if (primaryVideoRef.current) {
        primaryVideoRef.current.pause();
        primaryVideoRef.current.src = '';
      }
      if (bufferVideoRef.current) {
        bufferVideoRef.current.pause();
        bufferVideoRef.current.src = '';
      }
    };
  }, []);

  // Render a progress indicator with checkmark and animation
  const ProgressItem = ({ label, isComplete }) => (
    <div style={{
      display: "flex",
      alignItems: "center",
      marginBottom: "12px",
      color: isComplete ? "#00ff00" : "#aaa",
      transition: "color 0.5s ease",
      fontSize: "0.9em",
      padding: "5px",
      borderRadius: "4px",
      backgroundColor: isComplete ? "rgba(0, 85, 0, 0.2)" : "transparent",
      transition: "background-color 0.5s ease, color 0.5s ease",
    }}>
      <span style={{
        display: "inline-flex",
        justifyContent: "center",
        alignItems: "center",
        width: "24px",
        height: "24px",
        borderRadius: "12px",
        backgroundColor: isComplete ? "#005500" : "#333",
        marginRight: "15px",
        transition: "background-color 0.5s ease",
        animation: isComplete ? "checkmarkPop 0.5s ease-in-out" : "none",
        fontWeight: "bold",
        fontSize: "16px",
      }}>
        {isComplete ? "✓" : "..."}
      </span>
      <span style={{ flex: 1 }}>{label}</span>
      <span style={{
        marginLeft: "10px",
        fontWeight: isComplete ? "bold" : "normal",
        color: isComplete ? "#00ff00" : "#888",
        transition: "color 0.5s ease",
        fontSize: "0.8em",
      }}>
        {isComplete ? "Complete" : "Pending"}
      </span>
    </div>
  );

  if (error && validVideoUrls.current.length > 0 && currentVideoIndex >= validVideoUrls.current.length - 1) {
    return (
      <div className="media-error">
        <p>Unable to load media. Please try again later.</p>
        {activeVideoUrl && <small>Failed on: {activeVideoUrl}</small>}
      </div>
    );
  }
  
  if (validVideoUrls.current.length === 0 && !activeAudioUrl) {
      return (
        <div className="media-loading">
            <p>No media to display.</p>
        </div>
      )
  }

  return (
    <div className="media-container">
      {showLoadingProgress && !error && (
        <div className="media-loading-overlay" style={{
          position: 'absolute',
          top: 0,
          left: 0,
          width: '100%',
          height: '100%',
          backgroundColor: 'rgba(0, 0, 0, 0.85)',
          zIndex: 10,
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'center',
          alignItems: 'center',
          padding: '20px',
          boxSizing: 'border-box',
          animation: 'fadeIn 0.3s ease-in-out',
        }}>
          <h3 style={{ 
            color: '#00ff00', 
            marginBottom: '20px', 
            textAlign: 'center',
            textShadow: '0 0 10px rgba(0, 255, 0, 0.5)',
            fontSize: '1.2em',
          }}>
            Loading Media Assets
          </h3>
          
          <div style={{
            backgroundColor: 'rgba(0, 0, 0, 0.5)',
            padding: '20px',
            borderRadius: '8px',
            width: '80%',
            maxWidth: '400px',
          }}>
            <ProgressItem 
              label={`Video Files (${videosLoading}/${videosTotal})`} 
              isComplete={videosLoading >= videosTotal} 
            />
            
            <ProgressItem 
              label={`Audio Track`} 
              isComplete={audioElementReady} 
            />
            
            {videosTotal > 0 && (
              <div style={{ width: '100%', marginTop: '20px' }}>
                <div style={{ 
                  backgroundColor: '#333', 
                  height: '10px',
                  borderRadius: '5px',
                  overflow: 'hidden',
                  marginTop: '5px',
                  border: '1px solid #444',
                }}>
                  <div style={{ 
                    width: `${(videosLoading / videosTotal) * 100}%`, 
                    height: '100%', 
                    backgroundColor: '#00aa00',
                    transition: 'width 0.5s ease',
                    backgroundImage: 'linear-gradient(to right, #008800, #00dd00)',
                    boxShadow: '0 0 5px rgba(0, 255, 0, 0.5)',
                  }}></div>
                </div>
                <div style={{ 
                  textAlign: 'center', 
                  marginTop: '8px', 
                  fontSize: '0.9em',
                  color: '#aaa',
                  fontWeight: videosLoading === videosTotal ? 'bold' : 'normal',
                  color: videosLoading === videosTotal ? '#00ff00' : '#aaa',
                }}>
                  {Math.round((videosLoading / videosTotal) * 100)}% complete
                </div>
              </div>
            )}
          </div>
        </div>
      )}
      
      <div className="media-player" style={{ position: 'relative', width, height, backgroundColor: '#000' }}>
        {/* Primary video element */}
        <video 
          ref={primaryVideoRef}
          width="100%" 
          height="100%"
          controls={false}
          muted={true}
          playsInline={true}
          style={{ 
            display: activeVideoRef === 'primary' ? 'block' : 'none', 
            objectFit: 'contain' 
          }}
        >
          Your browser does not support the video tag.
        </video>

        {/* Buffer video element */}
        <video 
          ref={bufferVideoRef}
          width="100%" 
          height="100%"
          controls={false}
          muted={true}
          playsInline={true}
          style={{ 
            display: activeVideoRef === 'buffer' ? 'block' : 'none', 
            objectFit: 'contain' 
          }}
        >
          Your browser does not support the video tag.
        </video>

        {/* Audio element - always present for potential playback, but hidden */}
        {activeAudioUrl && (
          <audio ref={audioRef} preload="auto" loop={false} />
        )}
        
        {/* Play button overlay when autoplay is blocked */}
        {showPlayButton && !isPlaying && (
          <div style={{
            position: 'absolute',
            top: 0,
            left: 0,
            width: '100%',
            height: '100%',
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            backgroundColor: 'rgba(0, 0, 0, 0.7)',
            cursor: 'pointer',
            zIndex: 10,
          }} onClick={() => {
            setShowPlayButton(false);
            playCurrentVideo();
          }}>
            <button style={{
              width: '80px',
              height: '80px',
              borderRadius: '50%',
              backgroundColor: '#00ff00',
              border: 'none',
              cursor: 'pointer',
              display: 'flex',
              justifyContent: 'center',
              alignItems: 'center',
              fontSize: '40px',
              color: '#000',
            }}>
              ▶
            </button>
          </div>
        )}
      </div>
      
      <style jsx>{`
        .media-container {
          width: ${width};
          height: ${height};
          position: relative;
        }
        video::-webkit-media-controls {
          display: none !important;
        }
        video::-moz-media-controls {
          display: none !important;
        }
        .media-loading, .media-error {
          display: flex;
          justify-content: center;
          align-items: center;
          width: 100%;
          height: 100%;
          background-color: #111;
          color: #666;
          text-align: center;
        }
        .media-error p { color: #ff6666; }
        
        @keyframes fadeIn {
          from { opacity: 0; }
          to { opacity: 1; }
        }
        
        @keyframes checkmarkPop {
          0% { transform: scale(0.5); opacity: 0.5; }
          70% { transform: scale(1.2); opacity: 1; }
          100% { transform: scale(1); opacity: 1; }
        }
      `}</style>
    </div>
  );
};

export default MediaHandler; 