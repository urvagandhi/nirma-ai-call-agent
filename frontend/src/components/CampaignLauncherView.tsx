import React, { useState } from 'react';
import { 
  PhoneCall, 
  Users, 
  ShieldAlert, 
  Volume2
} from 'lucide-react';
import { toast } from 'sonner';

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { 
  Select, 
  SelectContent, 
  SelectItem, 
  SelectTrigger, 
  SelectValue 
} from '@/components/ui/select';
import { Slider } from '@/components/ui/slider';
import { 
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { CallCampaign, INITIAL_SCRIPTS } from '@/services/api';

interface CampaignLauncherViewProps {
  onCampaignCreated: (newCampaign: CallCampaign) => void;
  onNavigateToTelemetry: () => void;
}

const DEPARTMENTS = [
  'All Departments',
  'Computer Science & Engineering',
  'Information Technology',
  'Mechanical Engineering',
  'Civil Engineering',
  'Institute of Pharmacy',
  'Institute of Management'
];

export const CampaignLauncherView: React.FC<CampaignLauncherViewProps> = React.memo(({
  onCampaignCreated,
  onNavigateToTelemetry,
}) => {
  const [campaignName, setCampaignName] = useState('Winter 2026 Tuition Fee Reminder Round 2');
  const [selectedDept, setSelectedDept] = useState('Computer Science & Engineering');
  const [selectedSemesters, setSelectedSemesters] = useState<number[]>([3, 5]);
  const [selectedScriptId, setSelectedScriptId] = useState<number>(1);
  const [attendanceThreshold, setAttendanceThreshold] = useState<number>(75);
  const [feeStatus, setFeeStatus] = useState<string>('pending');
  const [throttleRate, setThrottleRate] = useState<number>(20); // 20 calls/min
  const [isConfirmOpen, setIsConfirmOpen] = useState(false);

  const selectedScript = INITIAL_SCRIPTS.find(s => s.id === selectedScriptId) || INITIAL_SCRIPTS[0];

  // Dynamic estimated recipient count based on filters
  const estimatedStudents = React.useMemo(() => {
    return selectedDept === 'All Departments' 
      ? 1240 
      : selectedSemesters.length * 64;
  }, [selectedDept, selectedSemesters.length]);

  const toggleSemester = React.useCallback((sem: number) => {
    setSelectedSemesters(prev => 
      prev.includes(sem) ? prev.filter(s => s !== sem) : [...prev, sem].sort()
    );
  }, []);

  const handleLaunchCampaign = React.useCallback(() => {
    setIsConfirmOpen(false);

    const newCampaign: CallCampaign = {
      id: Math.floor(Math.random() * 900) + 200,
      name: campaignName,
      script_id: selectedScriptId,
      target_filter: {
        department: selectedDept,
        semesters: selectedSemesters,
        attendance_lt: attendanceThreshold,
        fee_status: feeStatus
      },
      scheduled_at: new Date().toISOString(),
      max_retries: 2,
      retry_delay_min: 45,
      status: 'running',
      total_tasks: estimatedStudents,
      completed_tasks: 0,
      failed_tasks: 0
    };

    toast.promise(
      new Promise((resolve) => setTimeout(resolve, 1200)),
      {
        loading: `Queueing ${estimatedStudents} PSTN calls via Plivo carrier...`,
        success: () => {
          onCampaignCreated(newCampaign);
          if (onNavigateToTelemetry) {
            setTimeout(onNavigateToTelemetry, 700);
          }
          return `Campaign "${campaignName}" launched! Calls in progress.`;
        },
        error: 'Failed to dispatch carrier calls'
      }
    );
  }, [campaignName, selectedScriptId, selectedDept, selectedSemesters, attendanceThreshold, feeStatus, estimatedStudents, onCampaignCreated, onNavigateToTelemetry]);

  return (
    <div id="panel-campaigns" role="tabpanel" aria-labelledby="tab-campaigns" className="space-y-6">
      {/* View Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-hairline pb-5">
        <div>
          <div className="flex items-center space-x-2">
            <h1 className="text-2xl font-semibold tracking-tight text-ink font-sans">
              Outbound Voice Campaign Wizard & Dispatcher
            </h1>
            <Badge variant="mono" className="text-[10px] text-primary border-hairline-terracotta bg-primary/10">
              TRAI COMPLIANT
            </Badge>
          </div>
          <p className="text-xs text-body mt-1">
            Configure student recipient filters, select verified AI prompts, and schedule bulk telephone dispatching
          </p>
        </div>

        {/* TRAI Window Alert Banner */}
        <div className="flex items-center space-x-2.5 text-xs font-mono text-body bg-telemetry-amber/10 border border-telemetry-amber/25 px-3.5 py-2 rounded-md">
          <ShieldAlert className="w-4 h-4 text-telemetry-amber shrink-0" />
          <div>
            <div className="text-ink font-semibold">Active Calling Window: 09:00 - 21:00 IST</div>
            <div className="text-[10px] text-mute">Telecom Regulatory Authority of India (TRAI) automated dialer rules active</div>
          </div>
        </div>
      </div>

      {/* Main Grid: Form Left (7 cols) | Summary Preview Right (5 cols) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Campaign Form */}
        <div className="lg:col-span-7 space-y-5">
          {/* 1. Campaign Basics */}
          <Card className="bg-canvas-soft border-hairline">
            <CardHeader className="p-5 pb-3">
              <div className="flex items-center space-x-2">
                <span className="w-5 h-5 rounded-full bg-primary/20 text-primary font-mono text-xs flex items-center justify-center font-bold">1</span>
                <CardTitle className="text-sm font-semibold text-ink">Campaign Identity</CardTitle>
              </div>
              <CardDescription className="text-xs text-body">
                Give your batch dispatch a clear administrative reference name
              </CardDescription>
            </CardHeader>
            <CardContent className="p-5 pt-0 space-y-3">
              <div className="space-y-1.5">
                <label htmlFor="campaign-title-input" className="text-xs font-medium text-body">Campaign Title</label>
                <Input 
                  id="campaign-title-input"
                  value={campaignName}
                  onChange={(e) => setCampaignName(e.target.value)}
                  placeholder="e.g. BTech Semester 5 Tuition Fee Notice"
                  className="bg-canvas-elevated text-ink"
                />
              </div>
            </CardContent>
          </Card>

          {/* 2. Target Student Recipient Filters */}
          <Card className="bg-canvas-soft border-hairline">
            <CardHeader className="p-5 pb-3">
              <div className="flex items-center space-x-2">
                <span className="w-5 h-5 rounded-full bg-primary/20 text-primary font-mono text-xs flex items-center justify-center font-bold" aria-hidden="true">2</span>
                <CardTitle className="text-sm font-semibold text-ink">Target Audience & Filters</CardTitle>
              </div>
              <CardDescription className="text-xs text-body">
                Filter eligible students from the Nirma academic ERP database
              </CardDescription>
            </CardHeader>
            <CardContent className="p-5 pt-0 space-y-4">
              {/* Department */}
              <div className="space-y-1.5">
                <label id="dept-select-label" className="text-xs font-medium text-body">Academic Department</label>
                <Select value={selectedDept} onValueChange={setSelectedDept}>
                  <SelectTrigger aria-labelledby="dept-select-label" className="bg-canvas-elevated">
                    <SelectValue placeholder="Select Department" />
                  </SelectTrigger>
                  <SelectContent>
                    {DEPARTMENTS.map((dept) => (
                      <SelectItem key={dept} value={dept}>{dept}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {/* Semester Multi-Select Chips */}
              <div className="space-y-1.5">
                <label id="sem-group-label" className="text-xs font-medium text-body">Enrolled Semesters</label>
                <div className="flex flex-wrap gap-2" role="group" aria-labelledby="sem-group-label">
                  {[1, 2, 3, 4, 5, 6, 7, 8].map((sem) => {
                    const isSelected = selectedSemesters.includes(sem);
                    return (
                      <button
                        key={sem}
                        type="button"
                        aria-pressed={isSelected}
                        onClick={() => toggleSemester(sem)}
                        className={`px-3 py-1 rounded text-xs font-mono font-medium border transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary ${
                          isSelected
                            ? 'bg-primary text-white border-primary shadow-sm'
                            : 'bg-canvas-elevated text-body border-hairline hover:text-ink hover:border-hairline-strong'
                        }`}
                      >
                        Sem {sem}
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* Attendance Threshold Slider */}
              <div className="space-y-2 pt-1">
                <div className="flex items-center justify-between text-xs">
                  <label id="attendance-slider-label" className="text-body font-medium">Attendance Filter Criteria</label>
                  <span className="font-mono text-ink tabular-nums font-semibold">&lt; {attendanceThreshold}%</span>
                </div>
                <Slider 
                  aria-labelledby="attendance-slider-label"
                  value={[attendanceThreshold]} 
                  onValueChange={(vals) => setAttendanceThreshold(vals[0])}
                  min={50} 
                  max={90} 
                  step={5} 
                />
                <div className="flex justify-between text-[10px] text-mute font-mono" aria-hidden="true">
                  <span>50% (Critical)</span>
                  <span>75% (University Mandate)</span>
                  <span>90% (Distinction)</span>
                </div>
              </div>

              {/* Fee Clearance Filter */}
              <div className="space-y-1.5 pt-2">
                <label id="fee-status-label" className="text-xs text-body font-medium">Fee Clearance Status</label>
                <div className="grid grid-cols-3 gap-2" role="group" aria-labelledby="fee-status-label">
                  {[
                    { id: 'all', label: 'All Records' },
                    { id: 'pending', label: 'Pending Dues' },
                    { id: 'cleared', label: 'Fee Cleared' }
                  ].map((fee) => (
                    <button
                      key={fee.id}
                      type="button"
                      aria-pressed={feeStatus === fee.id}
                      onClick={() => setFeeStatus(fee.id)}
                      className={`h-8 rounded text-xs font-mono border transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary ${
                        feeStatus === fee.id
                          ? 'bg-primary text-white border-primary shadow-sm'
                          : 'bg-canvas-elevated text-body border-hairline hover:text-ink hover:border-hairline-strong'
                      }`}
                    >
                      {fee.label}
                    </button>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>

          {/* 3. Script Selection & Persona */}
          <Card className="bg-canvas-soft border-hairline">
            <CardHeader className="p-5 pb-3">
              <div className="flex items-center space-x-2">
                <span className="w-5 h-5 rounded-full bg-primary/20 text-primary font-mono text-xs flex items-center justify-center font-bold" aria-hidden="true">3</span>
                <CardTitle className="text-sm font-semibold text-ink">Call Script & Telephony Template</CardTitle>
              </div>
              <CardDescription className="text-xs text-body">
                Select predefined prompt approved by University Academic Cell
              </CardDescription>
            </CardHeader>
            <CardContent className="p-5 pt-0 space-y-3">
              <div className="space-y-1.5">
                <label id="script-select-label" className="text-xs font-medium text-body">Verified Call Script</label>
                <Select 
                  value={selectedScriptId.toString()} 
                  onValueChange={(val) => setSelectedScriptId(parseInt(val, 10))}
                >
                  <SelectTrigger aria-labelledby="script-select-label" className="bg-canvas-elevated">
                    <SelectValue placeholder="Select Call Script" />
                  </SelectTrigger>
                  <SelectContent>
                    {INITIAL_SCRIPTS.map((script) => (
                      <SelectItem key={script.id} value={script.id.toString()}>
                        {script.name} ({script.language.toUpperCase()})
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </CardContent>
          </Card>

          {/* 4. Concurrency & Rate Limit */}
          <Card className="bg-canvas-soft border-hairline">
            <CardHeader className="p-5 pb-3">
              <div className="flex items-center space-x-2">
                <span className="w-5 h-5 rounded-full bg-primary/20 text-primary font-mono text-xs flex items-center justify-center font-bold" aria-hidden="true">4</span>
                <CardTitle className="text-sm font-semibold text-ink">Carrier Rate Throttling</CardTitle>
              </div>
              <CardDescription className="text-xs text-body">
                Prevent carrier spam blocks and manage concurrent Celery workers
              </CardDescription>
            </CardHeader>
            <CardContent className="p-5 pt-0 space-y-3">
              <div className="space-y-2">
                <div className="flex items-center justify-between text-xs">
                  <label id="throttle-slider-label" className="text-body font-medium">Max Calls Dispatched Per Minute</label>
                  <span className="font-mono text-live-pulse tabular-nums font-semibold">{throttleRate} calls/min</span>
                </div>
                <Slider 
                  aria-labelledby="throttle-slider-label"
                  value={[throttleRate]} 
                  onValueChange={(vals) => setThrottleRate(vals[0])}
                  min={5} 
                  max={60} 
                  step={5} 
                />
                <div className="text-[10px] text-mute font-mono">
                  Recommended: 20 calls/min to stay comfortably within Plivo channel limits.
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Right Column: Dynamic Dispatch Summary & Live Script Preview */}
        <div className="lg:col-span-5 space-y-5">
          {/* Dispatch Summary Card */}
          <Card className="bg-canvas-elevated border-hairline-strong shadow-xl">
            <CardHeader className="p-5 border-b border-hairline">
              <div className="flex items-center justify-between">
                <CardTitle className="text-sm font-semibold text-ink">Dispatch Summary</CardTitle>
                <Badge variant="live" className="text-[10px] font-mono">READY TO DIAL</Badge>
              </div>
            </CardHeader>
            <CardContent className="p-5 space-y-4">
              <div className="flex items-center justify-between p-3 rounded-md bg-canvas-soft border border-hairline">
                <div className="flex items-center space-x-2.5">
                  <Users className="w-4 h-4 text-primary" />
                  <div>
                    <div className="text-xs text-mute font-mono">IDENTIFIED RECIPIENTS</div>
                    <div className="text-xl font-semibold text-ink tabular-nums font-sans">
                      {estimatedStudents} Students
                    </div>
                  </div>
                </div>
                <Badge variant="mono" className="text-[10px]">ERP Filtered</Badge>
              </div>

              <div className="space-y-2.5 text-xs font-mono text-body pt-1">
                <div className="flex justify-between border-b border-hairline-subtle pb-1.5">
                  <span className="text-mute">Department:</span>
                  <span className="text-ink font-medium truncate max-w-[200px]">{selectedDept}</span>
                </div>
                <div className="flex justify-between border-b border-hairline-subtle pb-1.5">
                  <span className="text-mute">Semesters:</span>
                  <span className="text-ink font-medium">
                    {selectedSemesters.length > 0 ? selectedSemesters.map(s => `Sem ${s}`).join(', ') : 'None'}
                  </span>
                </div>
                <div className="flex justify-between border-b border-hairline-subtle pb-1.5">
                  <span className="text-mute">Target Language:</span>
                  <span className="text-primary font-bold uppercase">{selectedScript.language}</span>
                </div>
                <div className="flex justify-between border-b border-hairline-subtle pb-1.5">
                  <span className="text-mute">Estimated Batch Duration:</span>
                  <span className="text-ink font-medium tabular-nums">
                    ~{Math.ceil(estimatedStudents / throttleRate)} minutes
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-mute">Retry Policy:</span>
                  <span className="text-ink font-medium">Max 2 retries (45m delay)</span>
                </div>
              </div>

              <Button 
                variant="default" 
                size="lg"
                onClick={() => setIsConfirmOpen(true)}
                className="w-full text-xs font-semibold shadow-lg shadow-orange-950/40 mt-3"
              >
                <PhoneCall className="w-4 h-4 mr-2" />
                Launch Outbound Campaign
              </Button>
            </CardContent>
          </Card>

          {/* Script Preview Card */}
          <Card className="bg-canvas-soft border-hairline">
            <CardHeader className="p-5 pb-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <Volume2 className="w-4 h-4 text-telemetry-cyan" />
                  <CardTitle className="text-sm font-semibold text-ink">AI Speech Script Preview</CardTitle>
                </div>
                <Badge variant="cyan" className="font-mono text-[10px] uppercase">
                  {selectedScript.language} TTS
                </Badge>
              </div>
            </CardHeader>
            <CardContent className="p-5 pt-0 space-y-3">
              <div className="space-y-1">
                <div className="text-[11px] font-mono text-mute uppercase">Opening Synthesized Greeting:</div>
                <div className="p-3 rounded-md bg-canvas-elevated border border-hairline text-xs text-ink leading-relaxed">
                  "{selectedScript.opening_message}"
                </div>
              </div>

              <div className="space-y-1 pt-1">
                <div className="text-[11px] font-mono text-mute uppercase">System Persona Prompt (Qwen-14B):</div>
                <div className="p-3 rounded-md bg-canvas-elevated border border-hairline text-xs text-body font-mono leading-relaxed max-h-[140px] overflow-y-auto">
                  {selectedScript.system_prompt}
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Confirmation Dialog */}
      <Dialog open={isConfirmOpen} onOpenChange={setIsConfirmOpen}>
        <DialogContent className="sm:max-w-[480px]">
          <DialogHeader>
            <DialogTitle className="text-base text-ink">Confirm Campaign Dispatch</DialogTitle>
            <DialogDescription className="text-xs text-body">
              Are you sure you want to initiate PSTN automated phone calls to students?
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-3 py-2 text-xs font-mono">
            <div className="p-3 rounded bg-canvas-soft border border-hairline space-y-1.5">
              <div className="flex justify-between">
                <span className="text-mute">Campaign:</span>
                <span className="text-ink font-semibold">{campaignName}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-mute">Total Recipients:</span>
                <span className="text-primary font-bold tabular-nums">{estimatedStudents} Students</span>
              </div>
              <div className="flex justify-between">
                <span className="text-mute">Script:</span>
                <span className="text-ink">{selectedScript.name}</span>
              </div>
            </div>

            <div className="text-[11px] text-telemetry-amber flex items-start space-x-1.5">
              <ShieldAlert className="w-4 h-4 shrink-0 mt-0.5" />
              <span>Calls will be logged with full audio recordings and transcripts in the university repository.</span>
            </div>
          </div>

          <DialogFooter className="sm:justify-end space-x-2">
            <Button variant="outline" size="sm" onClick={() => setIsConfirmOpen(false)}>
              Cancel
            </Button>
            <Button variant="default" size="sm" onClick={handleLaunchCampaign}>
              Confirm & Launch
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
});

CampaignLauncherView.displayName = 'CampaignLauncherView';
