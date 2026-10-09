import React, { useState, useEffect, Suspense, lazy } from 'react';
import { Header } from '@/components/Header';
import { Toaster } from '@/components/ui/sonner';
import { 
  CallCampaign, 
  CallTask, 
  INITIAL_CAMPAIGNS, 
  INITIAL_TASKS 
} from '@/services/api';

const DashboardView = lazy(() => import('@/components/DashboardView').then(m => ({ default: m.DashboardView })));
const LiveTelemetryView = lazy(() => import('@/components/LiveTelemetryView').then(m => ({ default: m.LiveTelemetryView })));
const CampaignLauncherView = lazy(() => import('@/components/CampaignLauncherView').then(m => ({ default: m.CampaignLauncherView })));
const TranscriptView = lazy(() => import('@/components/TranscriptView').then(m => ({ default: m.TranscriptView })));

const ViewFallback = () => (
  <div className="flex items-center justify-center min-h-[480px]">
    <div className="flex flex-col items-center space-y-3 p-6 glass-panel rounded-lg border border-hairline">
      <div className="w-6 h-6 border-2 border-primary border-t-transparent rounded-full animate-spin" />
      <span className="text-xs font-mono text-mute tracking-wider uppercase">Loading View Telemetry...</span>
    </div>
  </div>
);

export function App() {
  const [activeTab, setActiveTab] = useState<'dashboard' | 'telemetry' | 'campaigns' | 'transcripts'>('dashboard');
  const [campaigns, setCampaigns] = useState<CallCampaign[]>(INITIAL_CAMPAIGNS);
  const [tasks, setTasks] = useState<CallTask[]>(INITIAL_TASKS);

  // Background simulation for real-time telemetry updates
  useEffect(() => {
    const interval = setInterval(() => {
      setTasks(prevTasks => 
        prevTasks.map(t => {
          if (t.status === 'in_progress') {
            return {
              ...t,
              duration_sec: (t.duration_sec || 0) + 1,
            };
          }
          return t;
        })
      );
    }, 1000);

    return () => clearInterval(interval);
  }, []);

  const handleCampaignCreated = React.useCallback((newCampaign: CallCampaign) => {
    setCampaigns(prev => [newCampaign, ...prev]);

    // Generate mock tasks for newly launched campaign
    const newTasks: CallTask[] = [
      {
        id: Math.floor(Math.random() * 900) + 600,
        campaign_id: newCampaign.id,
        student_id: 3001,
        student_name: 'Harshil Shah',
        student_roll: '23BCE054',
        student_phone: '+91 98980 12345',
        script_id: newCampaign.script_id,
        status: 'in_progress',
        plivo_uuid: `plv_${Math.random().toString(36).substring(2, 9)}`,
        retry_count: 0,
        duration_sec: 4,
        placed_at: 'Just now',
        current_turn: "AI: 'नमस्ते, मैं निरमा यूनिवर्सिटी के अकाउंट ऑफिस से बोल रहा हूँ...'",
        turn_latency_ms: 1720,
      },
      {
        id: Math.floor(Math.random() * 900) + 700,
        campaign_id: newCampaign.id,
        student_id: 3002,
        student_name: 'Jiya Trivedi',
        student_roll: '23BCE088',
        student_phone: '+91 97240 56789',
        script_id: newCampaign.script_id,
        status: 'ringing',
        plivo_uuid: `plv_${Math.random().toString(36).substring(2, 9)}`,
        retry_count: 0,
        placed_at: '2s ago',
        current_turn: 'Ringing on PSTN network...',
        turn_latency_ms: 0,
      }
    ];

    setTasks(prev => [...newTasks, ...prev]);
    setActiveTab('telemetry');
  }, []);

  const handleLaunchNewCampaign = React.useCallback(() => setActiveTab('campaigns'), []);
  const handleViewTranscripts = React.useCallback(() => setActiveTab('transcripts'), []);
  const handleNavigateToTelemetry = React.useCallback(() => setActiveTab('telemetry'), []);
  const handleTabChange = React.useCallback((tab: string) => setActiveTab(tab as any), []);

  const activeCallCount = React.useMemo(() => {
    return tasks.filter(t => t.status === 'in_progress' || t.status === 'ringing').length;
  }, [tasks]);

  return (
    <div className="min-h-screen bg-canvas text-ink flex flex-col font-sans antialiased selection:bg-primary selection:text-white">
      {/* Sonner Toast Notification Container mounted once at root */}
      <Toaster position="top-right" richColors />

      {/* Navigation Masthead */}
      <Header 
        activeTab={activeTab} 
        setActiveTab={handleTabChange} 
        activeCallCount={activeCallCount}
      />

      {/* Main Content Viewport */}
      <main id="main-content" tabIndex={-1} className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6 focus:outline-none">
        <Suspense fallback={<ViewFallback />}>
          {activeTab === 'dashboard' && (
            <DashboardView 
              campaigns={campaigns}
              onLaunchNewCampaign={handleLaunchNewCampaign}
              onViewTranscripts={handleViewTranscripts}
            />
          )}

          {activeTab === 'telemetry' && (
            <LiveTelemetryView 
              tasks={tasks}
              onSelectTask={() => {}}
            />
          )}

          {activeTab === 'campaigns' && (
            <CampaignLauncherView 
              onCampaignCreated={handleCampaignCreated}
              onNavigateToTelemetry={handleNavigateToTelemetry}
            />
          )}

          {activeTab === 'transcripts' && (
            <TranscriptView />
          )}
        </Suspense>
      </main>

      {/* Footer */}
      <footer className="border-t border-hairline bg-canvas-subtle py-4 mt-auto">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between text-xs text-mute font-mono gap-2">
          <div>
            Nirma University • High-Performance Computing (HPC) AI Telephony Platform
          </div>
          <div className="flex items-center space-x-4">
            <span>TRAI Window: Active (09:00 - 21:00 IST)</span>
            <span>•</span>
            <span className="text-live-pulse">Plivo DID: +91 79 7160 0000</span>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default App;
