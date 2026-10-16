import React, { useState, useEffect, useRef } from 'react';
import { 
  Play, Pause, RotateCcw, Volume2, VolumeX, Download, 
  Layers, MessageSquare, Music, Sliders, ExternalLink,
  ZoomIn, ZoomOut, Sparkles, CheckCircle2
} from 'lucide-react';

interface TrackItem {
  id: string;
  name: string;
  display: {
    from: number;
    to: number;
  };
  details: {
    src?: string;
    volume?: number;
    text?: string;
  };
  metadata?: {
    speaker?: string;
    text?: string;
    sfx_name?: string;
  };
}

interface Track {
  id: string;
  type: string;
  title: string;
  items: TrackItem[];
}

interface TimelineData {
  fps: number;
  duration: number;
  tracks: Track[];
}

interface ProjectData {
  id: string;
  title: string;
  author: string;
  status: string;
  summary: string;
}

export default function App() {
  const [projectId, setProjectId] = useState<string>('');
  const [project, setProject] = useState<ProjectData | null>(null);
  const [timeline, setTimeline] = useState<TimelineData | null>(null);
  const [currentTime, setCurrentTime] = useState<number>(0);
  const [isPlaying, setIsPlaying] = useState<boolean>(false);
  const [zoomLevel, setZoomLevel] = useState<number>(30); // pixels per second
  const [selectedItem, setSelectedItem] = useState<TrackItem | null>(null);
  const [isExporting, setIsExporting] = useState<boolean>(false);
  const [exportUrl, setExportUrl] = useState<string>('');
  const [isMuted, setIsMuted] = useState<boolean>(false);

  const timelineContainerRef = useRef<HTMLDivElement>(null);
  const audioElementsRef = useRef<{ [key: string]: HTMLAudioElement }>({});
  const animationFrameRef = useRef<number | null>(null);
  const startTimeRef = useRef<number>(0);

  // Parse project_id from URL
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const pid = params.get('project_id') || '';
    setProjectId(pid);
    if (pid) {
      fetchTimeline(pid);
    } else {
      // Fallback demo timeline
      loadDemoTimeline();
    }
  }, []);

  const getApiBase = () => {
    return `${window.location.protocol}//${window.location.hostname}:8100`;
  };

  const fetchTimeline = async (pid: string) => {
    try {
      const res = await fetch(`${getApiBase()}/api/projects/${pid}/timeline`);
      const data = await res.json();
      setProject(data.project);
      setTimeline(data.timeline);
    } catch (err) {
      console.error('Error fetching timeline:', err);
      loadDemoTimeline();
    }
  };

  const loadDemoTimeline = () => {
    setProject({
      id: 'demo-1',
      title: 'رواية ليلة في القصر العتيق (تجريبي)',
      author: 'مؤلف تجريبي',
      status: 'READY',
      summary: 'أحداث غامضة تقع في ليلة ماطرة بعد وصول أحمد إلى القصر القديم.'
    });

    setTimeline({
      fps: 30,
      duration: 25.0,
      tracks: [
        {
          id: 'track_subtitles',
          type: 'text',
          title: 'النصوص والترجمة',
          items: [
            { id: 'sub-1', name: 'الراوي: كانت الليلة عاصفة...', display: { from: 0.0, to: 6.0 }, details: { text: '[الراوي] كَانَتِ اللَّيْلَةُ عَاصِفَةً وَصَوْتُ المَطَرِ يَهْطِلُ بِشِدَّةٍ.' }, metadata: { speaker: 'الراوي' } },
            { id: 'sub-2', name: 'أحمد: هل من أحد هنا؟', display: { from: 6.5, to: 12.0 }, details: { text: '[أحمد] هَلْ مِنْ أَحَدٍ هُنَا؟ أَرْجُوكُمْ افْتَحُوا البَابَ!' }, metadata: { speaker: 'أحمد' } },
            { id: 'sub-3', name: 'الراوي: لم يجب أحد...', display: { from: 12.5, to: 18.0 }, details: { text: '[الراوي] لَمْ يُجِبْ أَحَدٌ، لَكِنَّ وَقْعَ أَقْدَامٍ بَدَأَ يَقْتَرِبُ مِنَ الدَّاخِلِ.' }, metadata: { speaker: 'الراوي' } },
            { id: 'sub-4', name: 'ليلى: من يطرق في هذا الوقت؟', display: { from: 18.5, to: 24.5 }, details: { text: '[ليلى] مَنْ يَطْرُقُ البَابَ فِي هَذَا الوَقْتِ المُتَأَخِّرِ؟!' }, metadata: { speaker: 'ليلى' } },
          ]
        },
        {
          id: 'track_dialogue',
          type: 'audio',
          title: 'أصوات الشخصيات (Gemini TTS)',
          items: [
            { id: 'dia-1', name: 'الراوي (Charon)', display: { from: 0.0, to: 6.0 }, details: { src: 'http://127.0.0.1:9100/hexmedia-assets/sfx/suspense_drone.wav', volume: 100 }, metadata: { speaker: 'الراوي', text: 'كانت الليلة عاصفة...' } },
            { id: 'dia-2', name: 'أحمد (Puck)', display: { from: 6.5, to: 12.0 }, details: { src: 'http://127.0.0.1:9100/hexmedia-assets/sfx/door_knock.wav', volume: 100 }, metadata: { speaker: 'أحمد', text: 'هل من أحد هنا؟' } },
            { id: 'dia-3', name: 'الراوي (Charon)', display: { from: 12.5, to: 18.0 }, details: { src: 'http://127.0.0.1:9100/hexmedia-assets/sfx/footsteps.wav', volume: 100 }, metadata: { speaker: 'الراوي', text: 'لم يجب أحد...' } },
            { id: 'dia-4', name: 'ليلى (Kore)', display: { from: 18.5, to: 24.5 }, details: { src: 'http://127.0.0.1:9100/hexmedia-assets/sfx/suspense_drone.wav', volume: 100 }, metadata: { speaker: 'ليلى', text: 'من يطرق في هذا الوقت؟' } },
          ]
        },
        {
          id: 'track_sfx',
          type: 'audio',
          title: 'المؤثرات الصوتية (SFX)',
          items: [
            { id: 'sfx-1', name: 'مطر مستمر', display: { from: 0.0, to: 6.0 }, details: { src: 'http://127.0.0.1:9100/hexmedia-assets/sfx/rain.wav', volume: 50 }, metadata: { sfx_name: 'rain' } },
            { id: 'sfx-2', name: 'طرق الباب', display: { from: 6.5, to: 9.0 }, details: { src: 'http://127.0.0.1:9100/hexmedia-assets/sfx/door_knock.wav', volume: 80 }, metadata: { sfx_name: 'door_knock' } },
            { id: 'sfx-3', name: 'خطوات أقدام', display: { from: 13.0, to: 17.5 }, details: { src: 'http://127.0.0.1:9100/hexmedia-assets/sfx/footsteps.wav', volume: 70 }, metadata: { sfx_name: 'footsteps' } },
          ]
        },
        {
          id: 'track_bgm',
          type: 'audio',
          title: 'الموسيقى التصويرية (BGM)',
          items: [
            { id: 'bgm-1', name: 'موسيقى ترقب وغموض', display: { from: 0.0, to: 25.0 }, details: { src: 'http://127.0.0.1:9100/hexmedia-assets/sfx/suspense_drone.wav', volume: 30 } }
          ]
        }
      ]
    });
  };

  // Initialize and synchronize audio elements for all audio clips
  useEffect(() => {
    if (!timeline) return;

    // Cleanup previous audio elements
    Object.values(audioElementsRef.current).forEach(audio => {
      audio.pause();
      audio.src = '';
    });
    audioElementsRef.current = {};

    // Build audio pool for all audio track items
    const resolveAudioUrl = (url?: string) => {
      if (!url) return '';
      try {
        const parsed = new URL(url);
        if (parsed.port === '9100') {
          parsed.hostname = window.location.hostname;
          return parsed.toString();
        }
      } catch (e) {
        // Relative URL
      }
      return url;
    };

    timeline.tracks.forEach(track => {
      if (track.type === 'audio' || track.id.startsWith('track_')) {
        track.items.forEach(item => {
          if (item.details?.src) {
            const audio = new Audio();
            audio.crossOrigin = 'anonymous';
            audio.src = resolveAudioUrl(item.details.src);
            audio.preload = 'auto';
            const baseVol = (item.details.volume ?? 100) / 100;
            audio.volume = isMuted ? 0 : Math.max(0, Math.min(1, baseVol));
            audioElementsRef.current[item.id] = audio;
          }
        });
      }
    });

    return () => {
      Object.values(audioElementsRef.current).forEach(audio => {
        audio.pause();
        audio.src = '';
      });
      audioElementsRef.current = {};
    };
  }, [timeline]);

  // Handle Mute / Unmute changes
  useEffect(() => {
    if (!timeline) return;
    timeline.tracks.forEach(track => {
      track.items.forEach(item => {
        const audio = audioElementsRef.current[item.id];
        if (audio) {
          const baseVol = (item.details?.volume ?? 100) / 100;
          audio.volume = isMuted ? 0 : Math.max(0, Math.min(1, baseVol));
        }
      });
    });
  }, [isMuted, timeline]);

  // Synchronize All Multi-Track Audios
  const syncAudioPlayback = (time: number, isCurrentlyPlaying: boolean) => {
    if (!timeline) return;

    timeline.tracks.forEach(track => {
      if (track.type === 'audio' || track.id.startsWith('track_')) {
        track.items.forEach(item => {
          const audio = audioElementsRef.current[item.id];
          if (!audio || !item.details?.src) return;

          const { from, to } = item.display;
          const isActive = time >= from && time < to;

          if (isActive && isCurrentlyPlaying) {
            const targetOffset = time - from;
            if (audio.paused) {
              audio.currentTime = targetOffset;
              audio.play().catch(e => {
                // Autoplay policy or fetch error
                console.warn(`Playback notice for ${item.name}:`, e);
              });
            } else if (Math.abs(audio.currentTime - targetOffset) > 0.25) {
              audio.currentTime = targetOffset;
            }
          } else {
            if (!audio.paused) {
              audio.pause();
            }
            if (!isActive) {
              audio.currentTime = 0;
            }
          }
        });
      }
    });
  };

  // Playback Loop
  const togglePlay = () => {
    if (isPlaying) {
      pausePlayback();
    } else {
      startPlayback();
    }
  };

  const startPlayback = () => {
    setIsPlaying(true);
    startTimeRef.current = performance.now() - (currentTime * 1000);

    // Initial audio sync trigger
    syncAudioPlayback(currentTime, true);

    const loop = (timestamp: number) => {
      const elapsed = (timestamp - startTimeRef.current) / 1000;
      const totalDur = timeline?.duration || 30;

      if (elapsed >= totalDur) {
        pausePlayback();
        setCurrentTime(0);
        handleSeek(0);
      } else {
        setCurrentTime(elapsed);
        syncAudioPlayback(elapsed, true);
        animationFrameRef.current = requestAnimationFrame(loop);
      }
    };

    animationFrameRef.current = requestAnimationFrame(loop);
  };

  const pausePlayback = () => {
    setIsPlaying(false);
    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current);
    }
    // Pause all audio elements immediately
    Object.values(audioElementsRef.current).forEach(audio => {
      if (!audio.paused) {
        audio.pause();
      }
    });
  };

  const handleSeek = (time: number) => {
    const clamped = Math.max(0, Math.min(timeline?.duration || 30, time));
    setCurrentTime(clamped);
    if (isPlaying) {
      startTimeRef.current = performance.now() - (clamped * 1000);
      syncAudioPlayback(clamped, true);
    } else {
      syncAudioPlayback(clamped, false);
    }
  };

  const handleTimelineClick = (e: React.MouseEvent<HTMLDivElement>) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const clickX = e.clientX - rect.left;
    const seekTime = clickX / zoomLevel;
    handleSeek(seekTime);
  };

  // Export Trigger
  const handleExport = async () => {
    if (!projectId) {
      alert('مشروع تجريبي، لتصدير مشروع حقيقي يرجى فتحه من الشات الرئيسي.');
      return;
    }
    setIsExporting(true);
    try {
      const res = await fetch(`${getApiBase()}/api/projects/${projectId}/export`, {
        method: 'POST'
      });
      const data = await res.json();
      setIsExporting(false);
      if (data.audio_url) {
        setExportUrl(data.audio_url);
        window.open(data.audio_url, '_blank');
      } else {
        alert(data.message);
      }
    } catch (err: any) {
      setIsExporting(false);
      alert('خطأ أثناء التصدير: ' + err.message);
    }
  };

  // Format Time Helper (00:00.0)
  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    const ms = Math.floor((seconds % 1) * 10);
    return `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}.${ms}`;
  };

  // Find currently active subtitle
  const activeSubtitle = timeline?.tracks
    .find(t => t.type === 'text')
    ?.items.find(item => currentTime >= item.display.from && currentTime <= item.display.to);

  const totalDuration = timeline?.duration || 30;

  return (
    <div className="flex flex-col h-screen bg-[#0d0d11] text-zinc-100 select-none overflow-hidden">
      
      {/* ==================== TOP NAVIGATION BAR ==================== */}
      <header className="h-14 border-b border-zinc-800/80 px-6 flex items-center justify-between bg-[#131318] z-20">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-blue-600 to-indigo-500 flex items-center justify-center text-white shadow-md">
              <Sliders size={18} />
            </div>
            <div>
              <h1 className="font-bold text-sm leading-tight">{project?.title || 'استوديو DesignCombo'}</h1>
              <span className="text-[10px] text-blue-400 font-semibold">محرر التايم لاين والمونتاج الصوتي</span>
            </div>
          </div>
        </div>

        {/* Center Playback Controls */}
        <div className="flex items-center gap-3">
          <button 
            onClick={() => handleSeek(0)} 
            title="إعادة للبداية"
            className="p-2 rounded-lg hover:bg-zinc-800 text-zinc-400 hover:text-white transition">
            <RotateCcw size={16} />
          </button>

          <button 
            onClick={togglePlay} 
            className="w-10 h-10 rounded-full bg-blue-600 hover:bg-blue-500 text-white flex items-center justify-center shadow-lg shadow-blue-500/20 transition">
            {isPlaying ? <Pause size={18} /> : <Play size={18} className="mr-0.5" />}
          </button>

          <button 
            onClick={() => setIsMuted(!isMuted)} 
            title={isMuted ? "إلغاء الكتم" : "كتم الصوت"}
            className="p-2 rounded-lg hover:bg-zinc-800 text-zinc-400 hover:text-white transition">
            {isMuted ? <VolumeX size={16} className="text-red-400" /> : <Volume2 size={16} className="text-zinc-300" />}
          </button>

          <div className="font-mono text-xs text-zinc-300 bg-zinc-900 border border-zinc-800 px-3 py-1.5 rounded-lg flex items-center gap-1.5">
            <span className="text-blue-400 font-bold">{formatTime(currentTime)}</span>
            <span className="text-zinc-600">/</span>
            <span>{formatTime(totalDuration)}</span>
          </div>
        </div>

        {/* Right Action Buttons */}
        <div className="flex items-center gap-3">
          <a 
            href={`${getApiBase()}/?project_id=${projectId}`}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs text-zinc-300 hover:bg-zinc-800 border border-zinc-800 transition">
            <MessageSquare size={14} className="text-blue-400" />
            <span>العودة للشات</span>
          </a>

          <button 
            onClick={handleExport}
            disabled={isExporting}
            className="flex items-center gap-2 px-4 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold shadow-md shadow-emerald-500/20 transition disabled:opacity-50">
            {isExporting ? (
              <span className="inline-block w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></span>
            ) : (
              <Download size={14} />
            )}
            <span>تصدير الدراما الصوتية</span>
          </button>
        </div>
      </header>

      {/* ==================== WORKSPACE: PREVIEW & INSPECTOR ==================== */}
      <div className="flex-1 flex overflow-hidden">
        
        {/* Left / Center: Audiogram & Kinetic Subtitle Canvas */}
        <div className="flex-1 flex flex-col items-center justify-center p-6 bg-gradient-to-b from-[#131318] to-[#0d0d11] relative">
          
          {/* Main Visualizer Stage */}
          <div className="w-full max-w-3xl aspect-[16/9] rounded-2xl bg-zinc-950 border border-zinc-800/80 shadow-2xl flex flex-col items-center justify-center p-8 relative overflow-hidden group">
            
            {/* Dynamic Waveform Visualizer simulation */}
            <div className="flex items-center justify-center gap-1.5 h-24 mb-6">
              {[...Array(32)].map((_, i) => {
                const height = isPlaying 
                  ? Math.max(12, Math.sin(currentTime * 8 + i * 0.5) * 60 + 30) 
                  : 8;
                return (
                  <div 
                    key={i} 
                    className="w-1.5 rounded-full bg-gradient-to-t from-blue-600 via-indigo-500 to-cyan-400 transition-all duration-75"
                    style={{ height: `${height}px` }}
                  />
                );
              })}
            </div>

            {/* Kinetic Active Subtitle */}
            <div className="min-h-[60px] flex items-center justify-center text-center px-6">
              {activeSubtitle ? (
                <div className="animate-fade-in space-y-1">
                  <span className="inline-block px-2.5 py-0.5 rounded-full text-xs font-bold bg-blue-500/20 text-blue-400 border border-blue-500/30">
                    {activeSubtitle.metadata?.speaker || 'متحدث'}
                  </span>
                  <p className="text-xl md:text-2xl font-bold text-white leading-relaxed tracking-wide drop-shadow-md">
                    {activeSubtitle.details.text}
                  </p>
                </div>
              ) : (
                <p className="text-sm text-zinc-600 italic">
                  [ صمت أو وقفة درامية ]
                </p>
              )}
            </div>

            {/* Overlay Status Badge */}
            <div className="absolute top-4 right-4 flex items-center gap-2 px-3 py-1 rounded-full bg-zinc-900/80 border border-zinc-800 text-[11px] text-zinc-400">
              <span className={`w-2 h-2 rounded-full ${isPlaying ? 'bg-emerald-400 animate-pulse' : 'bg-zinc-600'}`}></span>
              <span>{isPlaying ? 'تشغيل حي' : 'متوقف'}</span>
            </div>
          </div>

        </div>

        {/* Right Sidebar: Selected Scene Inspector */}
        <aside className="w-80 border-r border-zinc-800/80 bg-[#131318] flex flex-col p-4">
          <div className="flex items-center gap-2 pb-3 border-b border-zinc-800 text-xs font-bold text-zinc-300">
            <Sliders size={14} className="text-blue-400" />
            <span>خصائص المقطع المحدد (Inspector)</span>
          </div>

          <div className="flex-1 overflow-y-auto py-4 space-y-4">
            {selectedItem ? (
              <div className="space-y-4">
                <div className="p-3 rounded-xl bg-zinc-900 border border-zinc-800 space-y-1">
                  <span className="text-[10px] uppercase font-bold text-zinc-400">اسم المقطع</span>
                  <div className="text-sm font-semibold text-white">{selectedItem.name}</div>
                </div>

                <div className="grid grid-cols-2 gap-2 text-xs">
                  <div className="p-2.5 rounded-lg bg-zinc-900 border border-zinc-800">
                    <span className="text-[10px] text-zinc-400 block">البداية</span>
                    <span className="font-mono text-blue-400 font-bold">{selectedItem.display.from.toFixed(1)} ثانية</span>
                  </div>
                  <div className="p-2.5 rounded-lg bg-zinc-900 border border-zinc-800">
                    <span className="text-[10px] text-zinc-400 block">النهاية</span>
                    <span className="font-mono text-blue-400 font-bold">{selectedItem.display.to.toFixed(1)} ثانية</span>
                  </div>
                </div>

                {selectedItem.details.text && (
                  <div className="p-3 rounded-xl bg-zinc-900 border border-zinc-800 space-y-1">
                    <span className="text-[10px] uppercase font-bold text-zinc-400">نص الحوار</span>
                    <p className="text-xs text-zinc-200 leading-relaxed">{selectedItem.details.text}</p>
                  </div>
                )}

                {selectedItem.details.src && (
                  <div className="p-3 rounded-xl bg-zinc-900 border border-zinc-800 space-y-2">
                    <span className="text-[10px] uppercase font-bold text-zinc-400">معاينة الصوت المنفرد</span>
                    <audio controls className="w-full h-8" src={selectedItem.details.src}></audio>
                  </div>
                )}
              </div>
            ) : (
              <div className="text-center py-12 text-zinc-400 text-xs space-y-2">
                <Layers size={24} className="mx-auto text-zinc-400" />
                <p>اضغط على أي مقطع في شريط التايم لاين بالأسفل لعرض خصائصه وتعديله.</p>
              </div>
            )}
          </div>
        </aside>

      </div>

      {/* ==================== BOTTOM: MULTI-TRACK TIMELINE ==================== */}
      <div className="h-72 border-t border-zinc-800/80 bg-[#111116] flex flex-col z-10">
        
        {/* Timeline Header Toolbar */}
        <div className="h-10 border-b border-zinc-800 px-4 flex items-center justify-between text-xs text-zinc-400">
          <div className="flex items-center gap-4">
            <span className="font-bold text-zinc-200 flex items-center gap-1.5">
              <Layers size={14} className="text-blue-400" />
              <span>المسارات الصوتية (Tracks)</span>
            </span>
          </div>

          <div className="flex items-center gap-2">
            <button 
              onClick={() => setZoomLevel(Math.max(10, zoomLevel - 5))}
              className="p-1.5 rounded hover:bg-zinc-800 text-zinc-400 hover:text-white transition">
              <ZoomOut size={14} />
            </button>
            <span className="text-[11px] font-mono">{zoomLevel}px/s</span>
            <button 
              onClick={() => setZoomLevel(Math.min(80, zoomLevel + 5))}
              className="p-1.5 rounded hover:bg-zinc-800 text-zinc-400 hover:text-white transition">
              <ZoomIn size={14} />
            </button>
          </div>
        </div>

        {/* Tracks Scroll Area */}
        <div className="flex-1 overflow-x-auto overflow-y-auto relative" ref={timelineContainerRef}>
          
          <div 
            className="min-w-full relative" 
            style={{ width: `${Math.max(1000, totalDuration * zoomLevel + 100)}px` }}>
            
            {/* Time Ruler */}
            <div 
              onClick={handleTimelineClick}
              className="h-7 border-b border-zinc-800 bg-zinc-950/80 sticky top-0 z-10 flex items-end cursor-pointer">
              {[...Array(Math.ceil(totalDuration) + 1)].map((_, sec) => (
                <div 
                  key={sec} 
                  className="absolute bottom-0 border-r border-zinc-800 h-3 text-[10px] text-zinc-400 pr-1 flex items-end font-mono"
                  style={{ left: `${sec * zoomLevel}px` }}>
                  {sec % 5 === 0 ? `${sec}s` : ''}
                </div>
              ))}
            </div>

            {/* Red Playhead Indicator */}
            <div 
              className="absolute top-0 bottom-0 w-[2px] bg-red-500 z-30 pointer-events-none"
              style={{ left: `${currentTime * zoomLevel}px` }}>
              <div className="w-3 h-3 rounded-full bg-red-500 -ml-[5px] -mt-1 shadow-md"></div>
            </div>

            {/* Tracks Container */}
            <div className="p-2 space-y-2">
              {timeline?.tracks.map((track) => {
                const isSelected = (itemId: string) => selectedItem?.id === itemId;

                const getTrackBadge = () => {
                  switch (track.id) {
                    case 'track_subtitles': return 'bg-purple-500/20 text-purple-300 border-purple-500/30';
                    case 'track_dialogue': return 'bg-blue-500/20 text-blue-300 border-blue-500/30';
                    case 'track_sfx': return 'bg-amber-500/20 text-amber-300 border-amber-500/30';
                    case 'track_bgm': return 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30';
                    default: return 'bg-zinc-800 text-zinc-300';
                  }
                };

                const getClipColor = () => {
                  switch (track.id) {
                    case 'track_subtitles': return 'from-purple-900/60 to-purple-800/80 border-purple-500/40 text-purple-200';
                    case 'track_dialogue': return 'from-blue-900/70 to-blue-800/90 border-blue-500/50 text-blue-100';
                    case 'track_sfx': return 'from-amber-900/60 to-amber-800/80 border-amber-500/50 text-amber-200';
                    case 'track_bgm': return 'from-emerald-950/70 to-emerald-900/80 border-emerald-500/40 text-emerald-300';
                    default: return 'from-zinc-800 to-zinc-700 border-zinc-600 text-zinc-200';
                  }
                };

                return (
                  <div key={track.id} className="flex items-center gap-2 group">
                    {/* Track Label */}
                    <div className="w-40 shrink-0 flex items-center justify-between px-2.5 py-2 rounded-lg bg-zinc-900 border border-zinc-800">
                      <span className="text-xs font-semibold text-zinc-300 truncate">{track.title}</span>
                      <span className={`text-[9px] px-1.5 py-0.5 rounded border font-mono ${getTrackBadge()}`}>
                        {track.items.length}
                      </span>
                    </div>

                    {/* Track Timeline Lane */}
                    <div 
                      onClick={handleTimelineClick}
                      className="flex-1 h-12 bg-zinc-950/60 border border-zinc-800/60 rounded-lg relative overflow-hidden cursor-pointer">
                      
                      {track.items.map((item) => {
                        const left = item.display.from * zoomLevel;
                        const width = Math.max(30, (item.display.to - item.display.from) * zoomLevel);
                        
                        return (
                          <div
                            key={item.id}
                            onClick={(e) => {
                              e.stopPropagation();
                              setSelectedItem(item);
                            }}
                            className={`absolute top-1 bottom-1 rounded-md px-2 flex items-center justify-between text-xs font-medium cursor-pointer shadow-sm transition border bg-gradient-to-r ${getClipColor()} ${isSelected(item.id) ? 'ring-2 ring-white border-white' : ''}`}
                            style={{
                              left: `${left}px`,
                              width: `${width}px`
                            }}>
                            <span className="truncate text-[11px] font-semibold">{item.name}</span>
                            <span className="text-[9px] opacity-75 font-mono ml-1">
                              {(item.display.to - item.display.from).toFixed(1)}s
                            </span>
                          </div>
                        );
                      })}

                    </div>
                  </div>
                );
              })}
            </div>

          </div>

        </div>

      </div>

    </div>
  );
}
