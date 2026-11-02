import React, { useState, useRef } from 'react';
import { Mic, Square, Loader2, X } from 'lucide-react';
import WaveformVisualizer from './WaveformVisualizer';

export default function VoiceRecorder({ onTranscription, language, disabled }) {
  const [isRecording, setIsRecording]   = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [liveStream, setLiveStream]     = useState(null);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef   = useRef([]);
  const abortControllerRef = useRef(null);

  const startRecording = async () => {
    try {
      audioChunksRef.current = [];
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      setLiveStream(stream);

      const mediaRecorder = new MediaRecorder(stream, { mimeType: 'audio/webm;codecs=opus' });
      mediaRecorderRef.current = mediaRecorder;

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        stream.getTracks().forEach((track) => track.stop());
        setLiveStream(null);
        await handleAudioUpload(audioBlob);
      };

      mediaRecorder.start();
      setIsRecording(true);
    } catch (err) {
      console.error('Error accessing microphone:', err);
      alert('Could not access your microphone. Please ensure microphone permissions are granted.');
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      setIsProcessing(true);
    }
  };

  const cancelRecording = () => {
    // Abort in-flight network request if processing
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }

    // Stop recorder without triggering upload
    if (mediaRecorderRef.current) {
      mediaRecorderRef.current.onstop = null;
      try {
        if (mediaRecorderRef.current.state !== 'inactive') {
          mediaRecorderRef.current.stop();
        }
      } catch (err) {
        console.warn('Error stopping recorder on exit:', err);
      }
    }

    // Stop audio stream tracks to release microphone
    if (liveStream) {
      liveStream.getTracks().forEach((track) => track.stop());
      setLiveStream(null);
    }

    audioChunksRef.current = [];
    setIsRecording(false);
    setIsProcessing(false);
  };

  const handleAudioUpload = async (audioBlob) => {
    try {
      abortControllerRef.current = new AbortController();
      const formData = new FormData();
      formData.append('audio', audioBlob, 'query.webm');
      formData.append('language_hint', language);

      const response = await fetch('/api/audio/transcribe', {
        method: 'POST',
        body: formData,
        signal: abortControllerRef.current.signal,
      });

      if (!response.ok) {
        throw new Error(`Voice transcription failed: ${response.statusText}`);
      }

      const data = await response.json();
      if (data.transcript) {
        onTranscription(data.transcript, data.detected_language);
      }
    } catch (err) {
      if (err.name === 'AbortError') {
        return;
      }
      console.error('Transcription error:', err);
      alert('Failed to transcribe voice. Please try typing your query.');
    } finally {
      setIsProcessing(false);
      abortControllerRef.current = null;
    }
  };

  return (
    <div className="voice-recorder-wrapper">
      {/* Live waveform – shown during recording */}
      {(isRecording || isProcessing) && (
        <div className="waveform-area">
          <WaveformVisualizer stream={liveStream} isRecording={isRecording} />
        </div>
      )}

      <button
        id="mic-btn"
        type="button"
        className={`mic-btn ${isRecording ? 'recording' : ''}`}
        onClick={isRecording ? stopRecording : startRecording}
        disabled={disabled || isProcessing}
        title={
          isRecording
            ? 'Click to stop and transcribe'
            : 'Click to speak in your selected Indian language'
        }
      >
        {isProcessing ? (
          <Loader2 size={20} className="animate-spin" />
        ) : isRecording ? (
          <Square size={18} />
        ) : (
          <Mic size={20} />
        )}
      </button>

      {/* Cross (Exit) button to end or exit speaking */}
      {(isRecording || isProcessing) && (
        <button
          id="voice-exit-btn"
          type="button"
          className="voice-exit-btn"
          onClick={cancelRecording}
          title="Exit / Cancel speaking"
          aria-label="Exit speaking"
        >
          <X size={18} />
        </button>
      )}
    </div>
  );
}
