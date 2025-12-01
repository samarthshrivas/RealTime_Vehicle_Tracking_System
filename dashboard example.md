import React, { useState, useRef, useEffect, useMemo } from 'react';
import { 
  Upload, 
  Play, 
  Pause, 
  Settings, 
  Activity, 
  Truck, 
  Car, 
  Bike, 
  AlertCircle,
  Video,
  Image as ImageIcon,
  Maximize2,
  Cpu,
  Layers,
  ChevronRight,
  Download,
  Trash2,
  Eye,
  EyeOff
} from 'lucide-react';

/**
 * MOCK DATA GENERATOR
 * In a real app, this would be replaced by a WebSocket connection to your Python YOLOv11 Backend.
 */
const generateMockDetections = (width, height) => {
  const count = Math.floor(Math.random() * 5) + 1; // 1-5 objects
  const detections = [];
  const classes = ['car', 'truck', 'bus', 'motorbike'];
  
  for (let i = 0; i < count; i++) {
    detections.push({
      id: Math.random().toString(36).substr(2, 9),
      class: classes[Math.floor(Math.random() * classes.length)],
      confidence: Math.random() * (0.99 - 0.70) + 0.70,
      x: Math.random() * (width - 100),
      y: Math.random() * (height - 100),
      w: Math.random() * 100 + 50,
      h: Math.random() * 80 + 40,
    });
  }
  return detections;
};

// --- COMPONENTS ---

const StatCard = ({ title, count, icon: Icon, color, trend }) => (
  <div className="bg-slate-900/50 backdrop-blur-md border border-slate-700/50 p-4 rounded-xl flex items-center justify-between hover:border-slate-500 transition-all group">
    <div>
      <p className="text-slate-400 text-xs font-medium uppercase tracking-wider mb-1">{title}</p>
      <div className="flex items-end gap-2">
        <h3 className="text-3xl font-bold text-white">{count}</h3>
        {trend && (
          <span className="text-emerald-400 text-xs font-medium mb-1.5 flex items-center">
            +{trend} <Activity size={10} className="ml-1" />
          </span>
        )}
      </div>
    </div>
    <div className={`p-3 rounded-lg bg-opacity-20 ${color} group-hover:scale-110 transition-transform`}>
      <Icon size={24} className={color.replace('bg-', 'text-')} />
    </div>
  </div>
);

const DetectionLogItem = ({ type, time, confidence }) => {
  const getIcon = () => {
    switch (type) {
      case 'truck': return <Truck size={14} />;
      case 'motorbike': return <Bike size={14} />;
      default: return <Car size={14} />;
    }
  };

  const getColor = () => {
    switch (type) {
      case 'truck': return 'text-orange-400';
      case 'motorbike': return 'text-purple-400';
      default: return 'text-blue-400';
    }
  };

  return (
    <div className="flex items-center justify-between p-3 border-b border-slate-800 hover:bg-slate-800/50 transition-colors text-sm">
      <div className="flex items-center gap-3">
        <span className={`p-1.5 rounded-md bg-slate-800 ${getColor()}`}>{getIcon()}</span>
        <div>
          <p className="font-medium text-slate-200 capitalize">{type}</p>
          <p className="text-xs text-slate-500">{time}</p>
        </div>
      </div>
      <div className="flex items-center gap-2">
        <div className="h-1.5 w-16 bg-slate-800 rounded-full overflow-hidden">
          <div 
            className="h-full bg-emerald-500 rounded-full" 
            style={{ width: `${confidence * 100}%` }}
          />
        </div>
        <span className="text-xs font-mono text-slate-400">{(confidence * 100).toFixed(0)}%</span>
      </div>
    </div>
  );
};

export default function VehicleDetectionApp() {
  // State
  const [file, setFile] = useState(null);
  const [fileUrl, setFileUrl] = useState(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [showOverlay, setShowOverlay] = useState(true);
  
  // Analytics State
  const [stats, setStats] = useState({ cars: 0, trucks: 0, buses: 0, bikes: 0 });
  const [fps, setFps] = useState(0);
  const [logs, setLogs] = useState([]);
  
  // Settings
  const [confidenceThreshold, setConfidenceThreshold] = useState(0.5);
  const [iouThreshold, setIouThreshold] = useState(0.45);

  // Refs
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const animationRef = useRef(null);

  // Handlers
  const handleFileUpload = (e) => {
    const uploadedFile = e.target.files[0];
    if (uploadedFile) {
      const url = URL.createObjectURL(uploadedFile);
      setFile(uploadedFile);
      setFileUrl(url);
      // Reset stats
      setStats({ cars: 0, trucks: 0, buses: 0, bikes: 0 });
      setLogs([]);
    }
  };

  const togglePlayback = () => {
    if (!videoRef.current) return;
    
    if (isPlaying) {
      videoRef.current.pause();
      setIsPlaying(false);
      setIsProcessing(false);
      cancelAnimationFrame(animationRef.current);
    } else {
      videoRef.current.play();
      setIsPlaying(true);
      setIsProcessing(true);
    }
  };

  // The "Game Loop" - Simulating YOLO Inference
  useEffect(() => {
    if (!isProcessing || !videoRef.current || !canvasRef.current) return;

    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    const video = videoRef.current;

    let lastTime = performance.now();
    let frameCount = 0;
    let lastFpsTime = lastTime;

    const processFrame = () => {
      const currentTime = performance.now();
      frameCount++;

      // Update FPS every second
      if (currentTime - lastFpsTime >= 1000) {
        setFps(Math.round((frameCount * 1000) / (currentTime - lastFpsTime)));
        frameCount = 0;
        lastFpsTime = currentTime;
      }

      // 1. Draw Video Frame to Canvas (if you want to process pixel data)
      // Or just clear canvas to draw overlays
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      if (showOverlay) {
        // 2. Generate MOCK Detections (Replace with API call)
        // In real app: const detections = await sendToBackend(videoFrame);
        const detections = generateMockDetections(canvas.width, canvas.height);

        // 3. Draw Bounding Boxes
        detections.forEach(det => {
          if (det.confidence < confidenceThreshold) return;

          // Color selection
          let color = '#3b82f6'; // blue default
          if (det.class === 'truck') color = '#f97316'; // orange
          if (det.class === 'bus') color = '#eab308'; // yellow
          if (det.class === 'motorbike') color = '#a855f7'; // purple

          // Box
          ctx.strokeStyle = color;
          ctx.lineWidth = 3;
          ctx.strokeRect(det.x, det.y, det.w, det.h);

          // Label background
          ctx.fillStyle = color;
          ctx.globalAlpha = 0.8;
          const label = `${det.class} ${Math.round(det.confidence * 100)}%`;
          const width = ctx.measureText(label).width;
          ctx.fillRect(det.x, det.y - 25, width + 10, 25);

          // Label text
          ctx.fillStyle = '#ffffff';
          ctx.globalAlpha = 1.0;
          ctx.font = 'bold 14px Inter, sans-serif';
          ctx.fillText(label, det.x + 5, det.y - 7);

          // Update Stats (Randomly increment for demo feel)
          if (Math.random() > 0.95) {
             setStats(prev => {
               const newStats = { ...prev };
               const key = det.class === 'motorbike' ? 'bikes' : det.class + 's';
               if (newStats[key] !== undefined) newStats[key]++;
               return newStats;
             });
             
             // Add to log
             const now = new Date();
             const timeString = `${now.getHours()}:${now.getMinutes()}:${now.getSeconds()}`;
             setLogs(prev => [{
               id: Date.now(),
               type: det.class,
               time: timeString,
               confidence: det.confidence
             }, ...prev].slice(0, 50)); // Keep last 50
          }
        });
      }

      if (!video.paused && !video.ended) {
        animationRef.current = requestAnimationFrame(processFrame);
      }
    };

    animationRef.current = requestAnimationFrame(processFrame);

    return () => cancelAnimationFrame(animationRef.current);
  }, [isProcessing, showOverlay, confidenceThreshold]);


  return (
    <div className="flex h-screen bg-[#0f172a] text-slate-200 font-sans overflow-hidden selection:bg-indigo-500 selection:text-white">
      
      {/* --- SIDEBAR --- */}
      <aside className="w-20 lg:w-64 bg-slate-900 border-r border-slate-800 flex flex-col justify-between hidden md:flex transition-all duration-300">
        <div>
          <div className="h-16 flex items-center justify-center lg:justify-start lg:px-6 border-b border-slate-800">
            <div className="w-8 h-8 bg-indigo-600 rounded-lg flex items-center justify-center mr-0 lg:mr-3 shadow-lg shadow-indigo-500/30">
              <Eye className="text-white" size={20} />
            </div>
            <span className="font-bold text-xl tracking-tight hidden lg:block text-white">YOLO<span className="text-indigo-500">Vision</span></span>
          </div>

          <nav className="p-4 space-y-2">
            <button className="w-full flex items-center gap-3 px-4 py-3 bg-indigo-600/10 text-indigo-400 border border-indigo-600/20 rounded-xl transition-all">
              <Layers size={20} />
              <span className="font-medium hidden lg:block">Dashboard</span>
            </button>
            <button className="w-full flex items-center gap-3 px-4 py-3 text-slate-400 hover:bg-slate-800/50 hover:text-slate-200 rounded-xl transition-all">
              <Video size={20} />
              <span className="font-medium hidden lg:block">Live Feed</span>
            </button>
            <button className="w-full flex items-center gap-3 px-4 py-3 text-slate-400 hover:bg-slate-800/50 hover:text-slate-200 rounded-xl transition-all">
              <Activity size={20} />
              <span className="font-medium hidden lg:block">Analytics</span>
            </button>
            <button className="w-full flex items-center gap-3 px-4 py-3 text-slate-400 hover:bg-slate-800/50 hover:text-slate-200 rounded-xl transition-all">
              <Settings size={20} />
              <span className="font-medium hidden lg:block">Settings</span>
            </button>
          </nav>
        </div>

        <div className="p-4 border-t border-slate-800">
          <div className="bg-slate-800/50 rounded-xl p-4 hidden lg:block">
            <div className="flex items-center gap-3 mb-2">
              <div className="p-2 bg-emerald-500/10 rounded-lg">
                <Cpu size={18} className="text-emerald-400" />
              </div>
              <div>
                <p className="text-xs text-slate-400">System Status</p>
                <p className="text-sm font-bold text-emerald-400">Online</p>
              </div>
            </div>
            <div className="space-y-2">
              <div className="flex justify-between text-xs text-slate-400">
                <span>GPU Usage</span>
                <span>34%</span>
              </div>
              <div className="h-1.5 bg-slate-700 rounded-full overflow-hidden">
                <div className="w-[34%] h-full bg-indigo-500 rounded-full"></div>
              </div>
            </div>
          </div>
        </div>
      </aside>

      {/* --- MAIN CONTENT --- */}
      <main className="flex-1 flex flex-col min-w-0 overflow-hidden relative">
        
        {/* Header */}
        <header className="h-16 bg-slate-900/50 backdrop-blur border-b border-slate-800 flex items-center justify-between px-6 z-10">
          <h1 className="text-lg font-medium text-slate-200 flex items-center gap-2">
            <span className="text-indigo-400">Project:</span> Highway_Surveillance_Cam_04
          </h1>
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2 px-3 py-1.5 bg-slate-800 rounded-lg border border-slate-700">
              <span className={`w-2 h-2 rounded-full ${isProcessing ? 'bg-emerald-500 animate-pulse' : 'bg-amber-500'}`}></span>
              <span className="text-xs font-mono text-slate-400">{isProcessing ? `PROCESSING ${fps} FPS` : 'IDLE'}</span>
            </div>
            <button className="p-2 hover:bg-slate-800 rounded-lg transition-colors text-slate-400 hover:text-white">
              <AlertCircle size={20} />
            </button>
            <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-indigo-500 to-purple-500 border-2 border-slate-800"></div>
          </div>
        </header>

        <div className="flex-1 overflow-auto p-4 lg:p-6 space-y-6 scrollbar-thin scrollbar-thumb-slate-700">
          
          {/* Stats Row */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <StatCard title="Total Cars" count={stats.cars} icon={Car} color="bg-blue-500" trend={12} />
            <StatCard title="Heavy Trucks" count={stats.trucks} icon={Truck} color="bg-orange-500" trend={4} />
            <StatCard title="Motorbikes" count={stats.bikes} icon={Bike} color="bg-purple-500" trend={8} />
            <StatCard title="Buses" count={stats.buses} icon={Activity} color="bg-emerald-500" />
          </div>

          {/* Main Workspace */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 h-[600px]">
            
            {/* Video Player Column */}
            <div className="lg:col-span-2 flex flex-col gap-4">
              <div className="relative flex-1 bg-black rounded-2xl overflow-hidden border border-slate-800 shadow-2xl group">
                
                {/* Video & Canvas */}
                {fileUrl ? (
                  <>
                    <video
                      ref={videoRef}
                      src={fileUrl}
                      className="absolute inset-0 w-full h-full object-contain"
                      loop
                      muted
                      onPlay={() => setIsPlaying(true)}
                      onPause={() => setIsPlaying(false)}
                    />
                    <canvas
                      ref={canvasRef}
                      className="absolute inset-0 w-full h-full pointer-events-none"
                    />
                  </>
                ) : (
                  <div className="absolute inset-0 flex flex-col items-center justify-center text-slate-500">
                    <div className="w-20 h-20 bg-slate-800/50 rounded-full flex items-center justify-center mb-4">
                      <Upload size={32} className="text-indigo-400" />
                    </div>
                    <p className="font-medium text-lg text-slate-300">Drop a video file to begin analysis</p>
                    <p className="text-sm mt-2">Supports MP4, AVI, MOV</p>
                    <label className="mt-6 px-6 py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white font-medium rounded-lg cursor-pointer transition-all hover:scale-105 active:scale-95 shadow-lg shadow-indigo-500/25">
                      Select File
                      <input type="file" accept="video/*" onChange={handleFileUpload} className="hidden" />
                    </label>
                  </div>
                )}

                {/* Player Controls Overlay (Hover) */}
                <div className={`absolute bottom-0 left-0 right-0 p-6 bg-gradient-to-t from-black/90 to-transparent transition-opacity duration-300 ${fileUrl ? 'opacity-0 group-hover:opacity-100' : 'hidden'}`}>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4">
                      <button 
                        onClick={togglePlayback}
                        className="w-12 h-12 flex items-center justify-center bg-white text-black rounded-full hover:scale-110 transition-all"
                      >
                        {isPlaying ? <Pause size={20} fill="currentColor" /> : <Play size={20} fill="currentColor" className="ml-1" />}
                      </button>
                      <div>
                        <h3 className="font-medium text-white text-sm">{file?.name || 'Unknown source'}</h3>
                        <p className="text-xs text-slate-400 font-mono">1920x1080 • 60FPS • H.264</p>
                      </div>
                    </div>
                    
                    <div className="flex items-center gap-2">
                       <button 
                         onClick={() => setShowOverlay(!showOverlay)}
                         className={`p-2 rounded-lg border ${showOverlay ? 'bg-indigo-500/20 border-indigo-500 text-indigo-400' : 'border-slate-600 text-slate-400'}`}
                         title="Toggle Bounding Boxes"
                       >
                         {showOverlay ? <Eye size={18} /> : <EyeOff size={18} />}
                       </button>
                       <button 
                         onClick={() => { setFile(null); setFileUrl(null); setIsPlaying(false); }}
                         className="p-2 hover:bg-red-500/20 hover:text-red-400 text-slate-400 rounded-lg transition-colors"
                       >
                         <Trash2 size={18} />
                       </button>
                    </div>
                  </div>
                </div>
              </div>

              {/* Quick Settings */}
              <div className="grid grid-cols-2 gap-4">
                <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl">
                  <div className="flex justify-between mb-2">
                    <label className="text-xs font-semibold text-slate-400 uppercase">Confidence Threshold</label>
                    <span className="text-xs font-mono text-indigo-400">{(confidenceThreshold * 100).toFixed(0)}%</span>
                  </div>
                  <input 
                    type="range" 
                    min="0" max="1" step="0.05" 
                    value={confidenceThreshold}
                    onChange={(e) => setConfidenceThreshold(parseFloat(e.target.value))}
                    className="w-full h-1.5 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-indigo-500" 
                  />
                </div>
                <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl">
                  <div className="flex justify-between mb-2">
                    <label className="text-xs font-semibold text-slate-400 uppercase">IOU Threshold</label>
                    <span className="text-xs font-mono text-indigo-400">{(iouThreshold * 100).toFixed(0)}%</span>
                  </div>
                  <input 
                    type="range" 
                    min="0" max="1" step="0.05" 
                    value={iouThreshold}
                    onChange={(e) => setIouThreshold(parseFloat(e.target.value))}
                    className="w-full h-1.5 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-indigo-500" 
                  />
                </div>
              </div>
            </div>

            {/* Right Panel: Logs & Details */}
            <div className="flex flex-col gap-4 h-full overflow-hidden">
              
              {/* Detection Log */}
              <div className="flex-1 bg-slate-900 border border-slate-800 rounded-2xl flex flex-col overflow-hidden">
                <div className="p-4 border-b border-slate-800 flex justify-between items-center bg-slate-900/50">
                  <h3 className="font-semibold text-slate-200 flex items-center gap-2">
                    <Activity size={16} className="text-indigo-400" />
                    Live Detections
                  </h3>
                  <span className="text-xs font-mono bg-slate-800 px-2 py-1 rounded text-slate-400">{logs.length} Events</span>
                </div>
                <div className="flex-1 overflow-y-auto scrollbar-thin scrollbar-thumb-slate-700">
                  {logs.length === 0 ? (
                    <div className="h-full flex flex-col items-center justify-center text-slate-500 opacity-60">
                      <Activity size={48} className="mb-2" />
                      <p className="text-sm">Waiting for detection stream...</p>
                    </div>
                  ) : (
                    logs.map(log => (
                      <DetectionLogItem key={log.id} {...log} />
                    ))
                  )}
                </div>
              </div>

              {/* Model Info */}
              <div className="bg-gradient-to-br from-indigo-900/20 to-slate-900 border border-slate-800 p-5 rounded-2xl">
                <div className="flex items-start justify-between mb-4">
                  <div>
                    <h3 className="font-bold text-white text-lg">YOLO v11 Nano</h3>
                    <p className="text-xs text-indigo-400 font-mono">v11.0.2-prod</p>
                  </div>
                  <div className="p-2 bg-indigo-500/20 rounded-lg border border-indigo-500/30">
                    <Cpu size={20} className="text-indigo-400" />
                  </div>
                </div>
                <div className="space-y-3">
                  <div className="flex justify-between text-sm border-b border-slate-800 pb-2">
                    <span className="text-slate-400">Input Resolution</span>
                    <span className="font-mono text-slate-200">640x640</span>
                  </div>
                  <div className="flex justify-between text-sm border-b border-slate-800 pb-2">
                    <span className="text-slate-400">Inference Time</span>
                    <span className="font-mono text-emerald-400">12.4ms</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-slate-400">Classes</span>
                    <span className="font-mono text-slate-200">80 COCO</span>
                  </div>
                </div>
                <button className="w-full mt-4 py-2 bg-slate-800 hover:bg-slate-700 text-sm font-medium rounded-lg text-slate-300 transition-colors flex items-center justify-center gap-2">
                  <Download size={14} /> Export CSV Report
                </button>
              </div>

            </div>
          </div>
        </div>
      </main>
    </div>
  );
}