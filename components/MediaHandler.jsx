import React, { useState, useEffect, useRef } from 'react';

/**
 * MediaHandler component for displaying videos and audio with synchronized playback
 */
const MediaHandler = ({ src, audioSrc, type = 'video/mp4', width = '100%', height = 'auto' }) => {
  console.log('MediaHandler props:', { src, audioSrc, type, width, height });

  const [error, setError] = useState(false);
  const [mediaUrl, setMediaUrl] = useState('');
  const [audioUrl, setAudioUrl] = useState('');
  const [isPlaying, setIsPlaying] = useState(false);
  const [isReady, setIsReady] = useState(false);
  const [videoReady, setVideoReady] = useState(false);
  const [audioReady, setAudioReady] = useState(false);
  const videoRef = useRef(null);
  const audioRef = useRef(null);
  
  useEffect(() => {
    // Format the URL correctly, ensuring it doesn't have duplicate slashes
    let formattedSrc = src;
    if (src && !src.startsWith('http')) {
      // Remove any leading slash and ensure it starts with /
      formattedSrc = '/' + src.replace(/^\/+/, '');
    }
    setMediaUrl(formattedSrc);
    setVideoReady(false); // Reset ready state when source changes
    
    // Format the audio URL if provided
    if (audioSrc) {
      let formattedAudioSrc = audioSrc;
      if (audioSrc && !audioSrc.startsWith('http')) {
        formattedAudioSrc = '/' + audioSrc.replace(/^\/+/, '');
      }
      setAudioUrl(formattedAudioSrc);
      console.log(`Setting audio URL to: ${formattedAudioSrc}`);
      setAudioReady(false); // Reset ready state when source changes
    } else {
      console.log('No audio source provided');
      setAudioReady(true); // No audio means audio is "ready"
    }
  }, [src, audioSrc]);

  // Set up event listeners for readiness tracking
  useEffect(() => {
    const video = videoRef.current;
    const audio = audioRef.current;
    
    if (!video) return;
    
    const handleVideoCanPlay = () => {
      console.log('Video can play');
      setVideoReady(true);
    };
    
    const handleVideoError = (e) => {
      console.error('Video error:', e);
      setVideoReady(false);
      setError(true);
    };
    
    // Add event listeners
    video.addEventListener('canplay', handleVideoCanPlay);
    video.addEventListener('error', handleVideoError);
    
    // Clean up event listeners
    return () => {
      video.removeEventListener('canplay', handleVideoCanPlay);
      video.removeEventListener('error', handleVideoError);
    };
  }, [mediaUrl]);
  
  // Set up event listeners for audio readiness
  useEffect(() => {
    const audio = audioRef.current;
    
    if (!audio || !audioUrl) {
      // If no audio element or no audio URL, consider audio as ready
      console.log('No audio element or URL - marking audio as ready');
      setAudioReady(true);
      return;
    }
    
    console.log(`Setting up audio element with source: ${audioUrl}`);
    
    const handleAudioCanPlay = () => {
      console.log('Audio can play');
      setAudioReady(true);
    };
    
    const handleAudioError = (e) => {
      console.error('Audio error:', e);
      console.error(`Failed to load audio from ${audioUrl}`);
      setAudioReady(false);
      // Don't set the overall error state, we can still play video without audio
    };
    
    // Add event listeners
    audio.addEventListener('canplay', handleAudioCanPlay);
    audio.addEventListener('error', handleAudioError);
    
    // Clean up event listeners
    return () => {
      audio.removeEventListener('canplay', handleAudioCanPlay);
      audio.removeEventListener('error', handleAudioError);
    };
  }, [audioUrl]);
  
  // Update overall ready state when both audio and video are ready
  useEffect(() => {
    setIsReady(videoReady && audioReady);
  }, [videoReady, audioReady]);

  // Set up synchronization between video and audio elements
  useEffect(() => {
    const video = videoRef.current;
    const audio = audioRef.current;
    
    if (!video || !audio || !audioUrl) return;
    
    const handlePlay = () => {
      audio.currentTime = video.currentTime;
      audio.play().catch(e => console.error('Error playing audio:', e));
      setIsPlaying(true);
    };
    
    const handlePause = () => {
      audio.pause();
      setIsPlaying(false);
    };
    
    const handleEnded = () => {
      setIsPlaying(false);
    };
    
    const handleSeeked = () => {
      audio.currentTime = video.currentTime;
    };
    
    // Add event listeners
    video.addEventListener('play', handlePlay);
    video.addEventListener('pause', handlePause);
    video.addEventListener('seeked', handleSeeked);
    video.addEventListener('ended', handleEnded);
    
    // Clean up event listeners
    return () => {
      video.removeEventListener('play', handlePlay);
      video.removeEventListener('pause', handlePause);
      video.removeEventListener('seeked', handleSeeked);
      video.removeEventListener('ended', handleEnded);
    };
  }, [audioUrl]);

  const handlePlayPause = () => {
    const video = videoRef.current;
    const audio = audioRef.current;
    
    if (!video) return;
    
    if (isPlaying) {
      console.log('Pausing media');
      video.pause();
    } else {
      console.log('Attempting to play media');
      if (audio) {
        console.log('Audio element exists, attempting to play synchronized');
      }
      
      video.play().catch(e => {
        console.error('Error playing video:', e);
        setError(true);
      });
    }
  };

  if (error) {
    return (
      <div className="media-error">
        <p>Unable to load media. Please try again later.</p>
        <small>{mediaUrl}</small>
      </div>
    );
  }

  return (
    <div className="media-container">
      {/* Loading Indicator */}
      {!isReady && !error && (
        <div className="media-loading">
          <p>Loading media...</p>
        </div>
      )}
      
      {/* Custom controls wrapper - positioned relatively for overlay if needed */}
      <div className="media-player" style={{ position: 'relative' }}>
        <video 
          ref={videoRef}
          width={width}
          height={height}
          controls={false}
          onError={() => setError(true)}
          style={{ display: isReady ? 'block' : 'none' }}
        >
          <source src={mediaUrl} type={type} />
          Your browser does not support the video tag.
        </video>

        {/* Audio element - hidden */}
        {audioUrl && (
          <audio ref={audioRef} src={audioUrl} preload="auto" />
        )}
      </div>
      
      <style jsx>{`
        video::-webkit-media-controls {
          display: none !important;
        }
        video::-moz-media-controls {
          display: none !important;
        }
      `}</style>
      
      {/* Debug info (optional) */}
      {/* 
      <div style={{ marginTop: '10px', fontSize: '0.8em' }}>
        <p>Video Ready: {videoReady.toString()}</p>
        <p>Audio Ready: {audioReady.toString()}</p>
        <p>Overall Ready: {isReady.toString()}</p>
        <p>Is Playing: {isPlaying.toString()}</p>
        <p>Video URL: {mediaUrl || 'N/A'}</p>
        <p>Audio URL: {audioUrl || 'N/A'}</p>
        <p>Error: {error.toString()}</p>
      </div>
      */}
    </div>
  );
};

export default MediaHandler; 