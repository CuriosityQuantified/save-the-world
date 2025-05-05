import React from 'react';
import Head from 'next/head';
import MediaHandler from '../components/MediaHandler';

export default function MediaTestPage() {
  // Direct test URLs for debugging
  const testVideoUrl = "/media/videos/sample_video.mp4";
  const testAudioUrl = "/media/audio/sample_audio.mp3";

  return (
    <div className="container">
      <Head>
        <title>Media Test Page</title>
        <meta name="description" content="Testing media playback" />
      </Head>

      <main>
        <h1>Media File Test Page</h1>
        <p>This page tests direct media file loading to debug playback issues.</p>

        <div className="test-section">
          <h2>Video Test</h2>
          <p>File path: <code>{testVideoUrl}</code></p>
          
          <div className="media-container">
            <h3>Using MediaHandler Component (Video Only):</h3>
            <MediaHandler src={testVideoUrl} type="video/mp4" />
            <p className="help-text">The custom controls should show a single play button that enables only when video is ready.</p>
          </div>
          
          <div className="media-container">
            <h3>Using direct Video tag (Browser controls):</h3>
            <video controls width="100%">
              <source src={testVideoUrl} type="video/mp4" />
              Your browser does not support the video tag.
            </video>
            <p className="help-text">For comparison: Default browser video controls.</p>
          </div>
        </div>

        <div className="test-section">
          <h2>Audio Test</h2>
          <p>File path: <code>{testAudioUrl}</code></p>
          
          <div className="media-container">
            <h3>Using Audio tag (Browser controls):</h3>
            <audio controls style={{ width: '100%' }}>
              <source src={testAudioUrl} type="audio/mpeg" />
              Your browser does not support the audio element.
            </audio>
            <p className="help-text">For comparison: Default browser audio controls.</p>
          </div>
        </div>
        
        <div className="test-section">
          <h2>Synchronized Video and Audio Test</h2>
          <p>Testing video: <code>{testVideoUrl}</code> with audio: <code>{testAudioUrl}</code></p>
          
          <div className="media-container">
            <h3>Using Updated MediaHandler with Unified Controls:</h3>
            <MediaHandler 
              src={testVideoUrl} 
              audioSrc={testAudioUrl} 
              type="video/mp4" 
            />
            <p className="help-text">The custom control will be enabled only when both video and audio are ready to play. 
              A single play button controls both. The play button will be disabled until both media files are loaded.</p>
          </div>
        </div>
        
        <div className="debug-info">
          <h2>Debugging Information</h2>
          <ul>
            <li>Video and audio files must be present in the correct public directories</li>
            <li>Check browser console for any loading errors</li>
            <li>The component shows a loading state while media files are being prepared</li>
            <li>If audio fails to load, video will still be playable</li>
            <li>Verify that both video and audio stay in sync during playback</li>
          </ul>
        </div>
      </main>

      <style jsx>{`
        .container {
          max-width: 800px;
          margin: 0 auto;
          padding: 20px;
        }
        
        h1 {
          text-align: center;
          margin-bottom: 30px;
        }
        
        .test-section {
          border: 1px solid #eaeaea;
          border-radius: 8px;
          padding: 20px;
          margin-bottom: 30px;
        }
        
        .media-container {
          margin-bottom: 20px;
        }
        
        code {
          background-color: #f1f1f1;
          padding: 2px 6px;
          border-radius: 4px;
          font-family: monospace;
        }
        
        .help-text {
          font-style: italic;
          color: #666;
          margin-top: 8px;
        }
        
        .debug-info {
          background-color: #f8f9fa;
          border-left: 4px solid #0070f3;
          padding: 15px;
          margin-top: 30px;
        }
        
        .debug-info ul {
          margin: 10px 0;
          padding-left: 20px;
        }
        
        .debug-info li {
          margin-bottom: 8px;
        }
      `}</style>
    </div>
  );
} 