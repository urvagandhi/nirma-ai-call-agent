import React, { useState } from 'react';
import { 
  Search, 
  Play, 
  Pause, 
  RotateCcw, 
  Volume2, 
  User, 
  Bot
} from 'lucide-react';
import { toast } from 'sonner';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { 
  Table, 
  TableBody, 
  TableCell, 
  TableHead, 
  TableHeader, 
  TableRow 
} from '@/components/ui/table';
import { 
  type CallTask,
  CallLog, 
  INITIAL_TASKS, 
  INITIAL_TRANSCRIPTS 
} from '@/services/api';

export const TranscriptView: React.FC = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedTaskId, setSelectedTaskId] = useState<number>(501);
  const [isPlaying, setIsPlaying] = useState(false);
  const [playbackSpeed, setPlaybackSpeed] = useState<number>(1);

  const filteredTasks = INITIAL_TASKS.filter(task => 
    task.student_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    task.student_roll.toLowerCase().includes(searchTerm.toLowerCase()) ||
    task.student_phone.includes(searchTerm)
  );

  const selectedTask = INITIAL_TASKS.find(t => t.id === selectedTaskId) || INITIAL_TASKS[0];
  const activeLog: CallLog = INITIAL_TRANSCRIPTS[selectedTaskId] || INITIAL_TRANSCRIPTS[501];

  const togglePlayAudio = () => {
    setIsPlaying(!isPlaying);
    if (!isPlaying) {
      toast.info(`Playing call recording for ${selectedTask.student_name}`, {
        description: `Source: MinIO audio archive (${selectedTask.duration_sec}s connected duration)`
      });
    }
  };

  const handleManualRetry = (task: CallTask) => {
    toast.promise(
      new Promise((resolve) => setTimeout(resolve, 800)),
      {
        loading: `Queueing manual PSTN retry for ${task.student_phone}...`,
        success: `Call task #${task.id} reset to pending. Carrier dial dispatched.`,
        error: 'Failed to reset task'
      }
    );
  };

  return (
    <div className="space-y-6">
      {/* View Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-hairline pb-5">
        <div>
          <div className="flex items-center space-x-2">
            <h1 className="text-2xl font-semibold tracking-tight text-ink font-sans">
              Conversation Transcripts & Audio Inspector
            </h1>
            <Badge variant="mono" className="text-[10px]">
              AUDIT COMPLIANT
            </Badge>
          </div>
          <p className="text-xs text-body mt-1">
            Review multi-turn speech transcripts, provider attribution, and conversational latencies for all completed calls
          </p>
        </div>

        {/* Search Input */}
        <div className="relative w-full sm:w-72">
          <Search className="w-3.5 h-3.5 absolute left-3 top-2.5 text-mute" />
          <Input 
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search roll, name, or phone..."
            className="pl-9 bg-canvas-soft border-hairline text-xs"
          />
        </div>
      </div>

      {/* Main Grid: Left Tasks Table (5 cols) | Right Transcript & Audio Console (7 cols) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Call Records Table */}
        <div className="lg:col-span-5">
          <Card className="bg-canvas-soft border-hairline overflow-hidden">
            <CardHeader className="p-4 border-b border-hairline">
              <div className="flex items-center justify-between">
                <CardTitle className="text-xs font-mono font-semibold uppercase tracking-wider text-body">
                  CALL LOG ARCHIVE
                </CardTitle>
                <Badge variant="mono" className="text-[10px]">
                  {filteredTasks.length} Records
                </Badge>
              </div>
            </CardHeader>
            <CardContent className="p-0">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>STUDENT</TableHead>
                    <TableHead>STATUS</TableHead>
                    <TableHead className="text-right">DURATION</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredTasks.map((task) => {
                    const isSelected = task.id === selectedTaskId;
                    return (
                      <TableRow 
                        key={task.id}
                        onClick={() => setSelectedTaskId(task.id)}
                        className={`cursor-pointer transition-colors ${
                          isSelected 
                            ? 'bg-canvas-elevated border-l-2 border-l-primary' 
                            : 'hover:bg-canvas-elevated/40'
                        }`}
                      >
                        <TableCell className="py-3">
                          <div className="font-semibold text-xs text-ink">{task.student_name}</div>
                          <div className="text-[11px] font-mono text-mute">{task.student_roll} • {task.student_phone}</div>
                        </TableCell>
                        <TableCell className="py-3">
                          <Badge 
                            variant={
                              task.status === 'completed' ? 'secondary' : 
                              task.status === 'in_progress' ? 'live' : 
                              task.status === 'ringing' ? 'ringing' : 'destructive'
                            }
                            className="text-[10px] font-mono uppercase"
                          >
                            {task.outcome || task.status}
                          </Badge>
                        </TableCell>
                        <TableCell className="text-right font-mono text-xs tabular-nums text-ink py-3">
                          {task.duration_sec ? `${task.duration_sec}s` : '0s'}
                        </TableCell>
                      </TableRow>
                    );
                  })}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </div>

        {/* Right Column: Audio Player & Turn-by-Turn Transcript */}
        <div className="lg:col-span-7 space-y-5">
          {/* Audio Player Card */}
          <Card className="bg-canvas-elevated border-hairline-strong shadow-lg">
            <CardContent className="p-5 space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-sm font-semibold text-ink">{selectedTask.student_name}</div>
                  <div className="text-xs text-mute font-mono">
                    Call Record #{selectedTask.id} • Plivo UUID: {selectedTask.plivo_uuid}
                  </div>
                </div>

                {selectedTask.status === 'failed' && (
                  <Button 
                    variant="outline" 
                    size="sm"
                    onClick={() => handleManualRetry(selectedTask)}
                    className="border-primary/40 text-primary hover:bg-primary/10 text-xs h-7"
                  >
                    <RotateCcw className="w-3 h-3 mr-1" />
                    Retry Call
                  </Button>
                )}
              </div>

              {/* Waveform & Timeline Slider */}
              <div className="p-3.5 rounded-md bg-canvas-soft border border-hairline space-y-3">
                <div className="flex items-center justify-between text-xs font-mono text-mute">
                  <div className="flex items-center space-x-1.5 text-ink">
                    <Volume2 className="w-3.5 h-3.5 text-primary" />
                    <span>Carrier Audio Track (8kHz mono)</span>
                  </div>
                  <div className="tabular-nums">
                    00:18 / 00:{selectedTask.duration_sec || 42}
                  </div>
                </div>

                {/* Animated Waveform Visualization */}
                <div className="h-8 flex items-center justify-between space-x-1 px-1">
                  {Array.from({ length: 36 }).map((_, i) => {
                    const heights = [6, 12, 18, 24, 10, 16, 28, 20, 8, 14, 22, 16, 26, 12, 18, 8];
                    const height = heights[i % heights.length];
                    const isPassed = i < 14;
                    return (
                      <div 
                        key={i} 
                        className={`w-1 rounded-full transition-all ${
                          isPassed ? 'bg-primary' : 'bg-canvas-elevated'
                        }`} 
                        style={{ height: `${height}px` }} 
                      />
                    );
                  })}
                </div>

                {/* Audio Controls */}
                <div className="flex items-center justify-between pt-1">
                  <div className="flex items-center space-x-2">
                    <Button 
                      variant="default" 
                      size="sm" 
                      onClick={togglePlayAudio}
                      className="h-8 px-3 rounded-full bg-primary"
                    >
                      {isPlaying ? <Pause className="w-3.5 h-3.5 mr-1" /> : <Play className="w-3.5 h-3.5 mr-1" />}
                      <span>{isPlaying ? 'Pause' : 'Play Audio'}</span>
                    </Button>
                  </div>

                  <div className="flex items-center space-x-1">
                    {[1, 1.25, 1.5].map((speed) => (
                      <button
                        key={speed}
                        onClick={() => setPlaybackSpeed(speed)}
                        className={`px-2 py-0.5 rounded text-[10px] font-mono border ${
                          playbackSpeed === speed 
                            ? 'bg-primary text-white border-primary' 
                            : 'bg-canvas-elevated text-mute border-hairline hover:text-ink'
                        }`}
                      >
                        {speed}x
                      </button>
                    ))}
                  </div>
                </div>
              </div>

              {/* AI Engine Attribution Card */}
              <div className="grid grid-cols-3 gap-2.5 p-3 rounded-md bg-canvas-soft border border-hairline text-xs font-mono">
                <div>
                  <div className="text-[10px] text-mute uppercase">STT Engine</div>
                  <div className="text-ink font-semibold truncate">{activeLog.stt_provider}</div>
                </div>
                <div>
                  <div className="text-[10px] text-mute uppercase">LLM Engine</div>
                  <div className="text-ink font-semibold truncate">{activeLog.llm_provider}</div>
                </div>
                <div>
                  <div className="text-[10px] text-mute uppercase">TTS Engine</div>
                  <div className="text-ink font-semibold truncate">{activeLog.tts_provider}</div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Full Turn Dialogue Bubble Stream */}
          <Card className="bg-canvas-soft border-hairline">
            <CardHeader className="p-4 border-b border-hairline">
              <div className="flex items-center justify-between">
                <CardTitle className="text-xs font-mono font-semibold uppercase tracking-wider text-body">
                  FULL MULTI-TURN TRANSCRIPT
                </CardTitle>
                <span className="text-xs font-mono text-mute">
                  Average Turn Latency: <strong className="text-live-pulse">{activeLog.avg_latency_ms} ms</strong>
                </span>
              </div>
            </CardHeader>
            <CardContent className="p-5 space-y-4 max-h-[420px] overflow-y-auto">
              {activeLog.transcript.map((turn, index) => {
                const isAssistant = turn.role === 'assistant';
                return (
                  <div 
                    key={index} 
                    className={`flex flex-col ${isAssistant ? 'items-start' : 'items-end'}`}
                  >
                    <div className="flex items-center space-x-1.5 mb-1 text-[11px] font-mono text-mute">
                      <span className="flex items-center space-x-1 text-ink font-medium">
                        {isAssistant ? (
                          <>
                            <Bot className="w-3 h-3 text-primary inline" />
                            <span>AI Caller (Nirma University)</span>
                          </>
                        ) : (
                          <>
                            <User className="w-3 h-3 text-telemetry-cyan inline" />
                            <span>Recipient Speech</span>
                          </>
                        )}
                      </span>
                      <span>•</span>
                      <span>{turn.timestamp}</span>
                      {turn.latency_ms && (
                        <span className="text-live-pulse font-semibold">
                          [{turn.latency_ms} ms turnaround]
                        </span>
                      )}
                    </div>

                    <div
                      className={`max-w-[85%] rounded-md p-3.5 text-xs leading-relaxed border ${
                        isAssistant
                          ? 'bg-live-pulse/5 border-live-pulse/20 text-ink shadow-sm'
                          : 'bg-canvas-elevated border-hairline text-ink'
                      }`}
                    >
                      {turn.text}
                    </div>
                  </div>
                );
              })}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};
