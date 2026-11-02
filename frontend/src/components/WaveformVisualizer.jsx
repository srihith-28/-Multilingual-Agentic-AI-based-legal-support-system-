import React, { useEffect, useRef } from 'react';

/**
 * WaveformVisualizer
 * Renders an animated audio waveform from the microphone MediaStream.
 * When `isRecording` is false and no stream is provided, shows a static idle wave.
 */
export default function WaveformVisualizer({ stream, isRecording }) {
  const canvasRef = useRef(null);
  const animFrameRef = useRef(null);
  const analyserRef = useRef(null);
  const dataArrayRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');

    if (isRecording && stream) {
      // Live waveform from microphone
      const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
      const source = audioCtx.createMediaStreamSource(stream);
      const analyser = audioCtx.createAnalyser();
      analyser.fftSize = 256;
      source.connect(analyser);

      const bufferLength = analyser.frequencyBinCount;
      const dataArray = new Uint8Array(bufferLength);

      analyserRef.current = analyser;
      dataArrayRef.current = dataArray;

      const draw = () => {
        animFrameRef.current = requestAnimationFrame(draw);
        analyser.getByteTimeDomainData(dataArray);

        const W = canvas.width;
        const H = canvas.height;
        ctx.clearRect(0, 0, W, H);

        // Gradient stroke
        const grad = ctx.createLinearGradient(0, 0, W, 0);
        grad.addColorStop(0, 'rgba(14,165,233,0.7)');
        grad.addColorStop(0.5, 'rgba(56,189,248,0.95)');
        grad.addColorStop(1, 'rgba(245,158,11,0.7)');

        ctx.lineWidth = 2;
        ctx.strokeStyle = grad;
        ctx.beginPath();

        const sliceWidth = W / bufferLength;
        let x = 0;
        for (let i = 0; i < bufferLength; i++) {
          const v = dataArray[i] / 128.0;
          const y = (v * H) / 2;
          if (i === 0) ctx.moveTo(x, y);
          else ctx.lineTo(x, y);
          x += sliceWidth;
        }
        ctx.lineTo(W, H / 2);
        ctx.stroke();
      };

      draw();

      return () => {
        cancelAnimationFrame(animFrameRef.current);
        audioCtx.close();
      };
    } else {
      // Idle animated sine wave
      let phase = 0;
      const drawIdle = () => {
        animFrameRef.current = requestAnimationFrame(drawIdle);
        const W = canvas.width;
        const H = canvas.height;
        ctx.clearRect(0, 0, W, H);

        ctx.lineWidth = 1.5;
        ctx.strokeStyle = 'rgba(14,165,233,0.4)';
        ctx.beginPath();

        for (let x = 0; x <= W; x++) {
          const y = H / 2 + Math.sin((x / W) * Math.PI * 6 + phase) * 6;
          if (x === 0) ctx.moveTo(x, y);
          else ctx.lineTo(x, y);
        }
        ctx.stroke();
        phase += 0.04;
      };

      drawIdle();

      return () => cancelAnimationFrame(animFrameRef.current);
    }
  }, [stream, isRecording]);

  return (
    <canvas
      ref={canvasRef}
      width={180}
      height={36}
      style={{ display: 'block' }}
      className="waveform-canvas"
    />
  );
}
