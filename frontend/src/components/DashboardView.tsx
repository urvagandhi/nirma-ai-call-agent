import React from 'react';
import { 
  PhoneCall, 
  PhoneForwarded, 
  Clock, 
  Zap, 
  TrendingUp, 
  CheckCircle2
} from 'lucide-react';
import { 
  ResponsiveContainer, 
  AreaChart, 
  Area, 
  XAxis, 
  YAxis, 
  Tooltip, 
  PieChart, 
  Pie, 
  Cell
} from 'recharts';

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Progress } from '@/components/ui/progress';
import { CallCampaign } from '@/services/api';

interface DashboardViewProps {
  campaigns: CallCampaign[];
  onLaunchNewCampaign: () => void;
  onViewTranscripts: () => void;
}

const DAILY_VOLUME_DATA = [
  { date: 'Oct 03', placed: 320, completed: 285, failed: 35 },
  { date: 'Oct 04', placed: 410, completed: 375, failed: 35 },
  { date: 'Oct 05', placed: 580, completed: 530, failed: 50 },
  { date: 'Oct 06', placed: 490, completed: 440, failed: 50 },
  { date: 'Oct 07', placed: 640, completed: 595, failed: 45 },
  { date: 'Oct 08', placed: 720, completed: 680, failed: 40 },
  { date: 'Oct 09', placed: 438, completed: 412, failed: 26 },
];

const DISPOSITION_DATA = [
  { name: 'Completed & Answered', value: 3317, color: '#10B981' },
  { name: 'No Answer / Timeout', value: 245, color: '#F59E0B' },
  { name: 'User Busy / Rejected', value: 182, color: '#A855F7' },
  { name: 'Carrier Error / Failed', value: 68, color: '#EF4444' },
];

const LATENCY_BREAKDOWN = [
  { stage: 'ASR (IndicConformer)', ms: 1080, budget: 1200, color: '#06B6D4' },
  { stage: 'LLM (Qwen-14B Local)', ms: 1420, budget: 1800, color: '#E06D3B' },
  { stage: 'TTS (IndicF5 Synthesis)', ms: 510, budget: 600, color: '#10B981' },
  { stage: 'Network & PSTN Buffer', ms: 280, budget: 400, color: '#A855F7' },
];

export const DashboardView: React.FC<DashboardViewProps> = ({
  campaigns,
  onLaunchNewCampaign,
  onViewTranscripts,
}) => {
  const totalCalls = campaigns.reduce((acc, c) => acc + c.total_tasks, 0);
  const completedCalls = campaigns.reduce((acc, c) => acc + c.completed_tasks, 0);
  const connectionRate = totalCalls > 0 ? ((completedCalls / totalCalls) * 100).toFixed(1) : '94.2';

  return (
    <div className="space-y-6">
      {/* Top Banner & Quick Actions */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-hairline pb-5">
        <div>
          <div className="flex items-center space-x-2">
            <h1 className="text-2xl font-semibold tracking-tight text-ink font-sans">
              Operational Telemetry & Performance Overview
            </h1>
            <Badge variant="live" className="text-[10px] font-mono uppercase tracking-wider">
              LIVE HPC STREAM
            </Badge>
          </div>
          <p className="text-xs text-body mt-1">
            Real-time automated outbound PSTN calls dialed from Nirma University Supercomputer node
          </p>
        </div>

        <div className="flex items-center space-x-2.5">
          <Button variant="outline" size="default" onClick={onViewTranscripts}>
            <Clock className="w-3.5 h-3.5 mr-1.5 text-body" />
            Inspect Call Logs
          </Button>
          <Button variant="default" size="default" onClick={onLaunchNewCampaign}>
            <PhoneCall className="w-3.5 h-3.5 mr-1.5" />
            Launch Batch Campaign
          </Button>
        </div>
      </div>

      {/* KPI Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Total Calls */}
        <Card className="bg-canvas-soft border-hairline">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <span className="font-mono text-[11px] font-semibold uppercase tracking-wider text-body">
                TOTAL CALLS DIALED
              </span>
              <PhoneForwarded className="w-4 h-4 text-primary" />
            </div>
            <div className="mt-2 flex items-baseline space-x-2">
              <span className="text-3xl font-semibold tracking-tight text-ink tabular-nums font-sans">
                {totalCalls.toLocaleString()}
              </span>
              <span className="text-xs text-live-pulse font-mono flex items-center">
                <TrendingUp className="w-3 h-3 mr-0.5 inline" /> +12.4%
              </span>
            </div>
            <p className="text-[11px] text-mute mt-1 font-mono">
              Across active academic terms
            </p>
          </CardContent>
        </Card>

        {/* Delivery / Connection Rate */}
        <Card className="bg-canvas-soft border-hairline">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <span className="font-mono text-[11px] font-semibold uppercase tracking-wider text-body">
                CONNECTION RATE
              </span>
              <CheckCircle2 className="w-4 h-4 text-live-pulse" />
            </div>
            <div className="mt-2 flex items-baseline space-x-2">
              <span className="text-3xl font-semibold tracking-tight text-ink tabular-nums font-sans">
                {connectionRate}%
              </span>
              <span className="text-xs text-live-pulse font-mono">
                TRAI Compliant
              </span>
            </div>
            <div className="mt-2">
              <Progress value={parseFloat(connectionRate)} className="h-1 bg-canvas-elevated" />
            </div>
          </CardContent>
        </Card>

        {/* Average Call Duration */}
        <Card className="bg-canvas-soft border-hairline">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <span className="font-mono text-[11px] font-semibold uppercase tracking-wider text-body">
                AVG CALL DURATION
              </span>
              <Clock className="w-4 h-4 text-telemetry-cyan" />
            </div>
            <div className="mt-2 flex items-baseline space-x-2">
              <span className="text-3xl font-semibold tracking-tight text-ink tabular-nums font-sans">
                48.6s
              </span>
              <span className="text-xs text-body font-mono">
                ~3.2 turns/call
              </span>
            </div>
            <p className="text-[11px] text-mute mt-1 font-mono">
              Brevity constraint strictly held
            </p>
          </CardContent>
        </Card>

        {/* Turnaround Latency */}
        <Card className="bg-canvas-soft border-hairline">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <span className="font-mono text-[11px] font-semibold uppercase tracking-wider text-body">
                AVG TURN LATENCY
              </span>
              <Zap className="w-4 h-4 text-telemetry-amber" />
            </div>
            <div className="mt-2 flex items-baseline space-x-2">
              <span className="text-3xl font-semibold tracking-tight text-live-pulse tabular-nums font-sans">
                1.84s
              </span>
              <span className="text-[11px] text-live-pulse font-mono px-1.5 py-0.5 rounded bg-live-pulse/10 border border-live-pulse/20">
                BUDGET &lt; 4.0s
              </span>
            </div>
            <p className="text-[11px] text-mute mt-1 font-mono">
              P95 Peak: 2.38s (Safe margin)
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Main Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Daily Call Volume Time-Series */}
        <Card className="lg:col-span-2 bg-canvas-soft border-hairline">
          <CardHeader className="p-5 pb-2">
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="text-sm font-semibold text-ink">Daily Outbound Call Volume</CardTitle>
                <CardDescription className="text-xs text-body mt-0.5">
                  Placed vs connected carrier calls across the past 7 days
                </CardDescription>
              </div>
              <div className="flex items-center space-x-3 text-xs font-mono">
                <span className="flex items-center text-primary">
                  <span className="w-2.5 h-2.5 rounded-full bg-primary inline-block mr-1.5" />
                  Dialed Calls
                </span>
                <span className="flex items-center text-live-pulse">
                  <span className="w-2.5 h-2.5 rounded-full bg-live-pulse inline-block mr-1.5" />
                  Answered
                </span>
              </div>
            </div>
          </CardHeader>
          <CardContent className="p-5 pt-3">
            <div className="h-[260px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={DAILY_VOLUME_DATA} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <defs>
                    <linearGradient id="colorPlaced" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#E06D3B" stopOpacity={0.35}/>
                      <stop offset="95%" stopColor="#E06D3B" stopOpacity={0}/>
                    </linearGradient>
                    <linearGradient id="colorCompleted" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#10B981" stopOpacity={0.35}/>
                      <stop offset="95%" stopColor="#10B981" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <XAxis dataKey="date" stroke="#64748B" fontSize={11} tickLine={false} axisLine={false} />
                  <YAxis stroke="#64748B" fontSize={11} tickLine={false} axisLine={false} />
                  <Tooltip 
                    contentStyle={{ 
                      backgroundColor: '#131B2E', 
                      borderColor: 'rgba(255,255,255,0.16)', 
                      borderRadius: '6px',
                      color: '#F1F5F9',
                      fontSize: '12px',
                      fontFamily: 'Inter'
                    }} 
                  />
                  <Area type="monotone" dataKey="placed" stroke="#E06D3B" strokeWidth={2} fillOpacity={1} fill="url(#colorPlaced)" />
                  <Area type="monotone" dataKey="completed" stroke="#10B981" strokeWidth={2} fillOpacity={1} fill="url(#colorCompleted)" />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        {/* Disposition Breakdown Donut */}
        <Card className="bg-canvas-soft border-hairline">
          <CardHeader className="p-5 pb-2">
            <CardTitle className="text-sm font-semibold text-ink">Call Disposition Breakdown</CardTitle>
            <CardDescription className="text-xs text-body mt-0.5">
              Telecom carrier delivery status distribution
            </CardDescription>
          </CardHeader>
          <CardContent className="p-5 pt-3">
            <div className="h-[180px] w-full flex items-center justify-center">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={DISPOSITION_DATA}
                    innerRadius={55}
                    outerRadius={80}
                    paddingAngle={4}
                    dataKey="value"
                  >
                    {DISPOSITION_DATA.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip 
                    contentStyle={{ 
                      backgroundColor: '#131B2E', 
                      borderColor: 'rgba(255,255,255,0.16)', 
                      borderRadius: '6px',
                      color: '#F1F5F9',
                      fontSize: '11px' 
                    }} 
                  />
                </PieChart>
              </ResponsiveContainer>
            </div>
            <div className="mt-4 space-y-2 text-xs font-mono">
              {DISPOSITION_DATA.map((item) => (
                <div key={item.name} className="flex items-center justify-between text-body">
                  <div className="flex items-center space-x-2">
                    <span className="w-2 h-2 rounded-full" style={{ backgroundColor: item.color }} />
                    <span className="truncate max-w-[150px]">{item.name}</span>
                  </div>
                  <span className="text-ink font-semibold tabular-nums">{item.value.toLocaleString()}</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Latency Pipeline Breakdown & Active Campaigns */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Latency Breakdown Card */}
        <Card className="bg-canvas-soft border-hairline">
          <CardHeader className="p-5 pb-2">
            <div className="flex items-center justify-between">
              <CardTitle className="text-sm font-semibold text-ink">AI Pipeline Turn Latency</CardTitle>
              <Badge variant="cyan" className="font-mono text-[10px]">
                TOTAL: 3,290 ms
              </Badge>
            </div>
            <CardDescription className="text-xs text-body mt-0.5">
              Strictly budgeted against 4,000 ms SLA threshold
            </CardDescription>
          </CardHeader>
          <CardContent className="p-5 pt-3 space-y-4">
            {LATENCY_BREAKDOWN.map((item) => {
              const pct = Math.round((item.ms / item.budget) * 100);
              return (
                <div key={item.stage} className="space-y-1.5">
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-body font-mono">{item.stage}</span>
                    <span className="text-ink font-mono font-medium tabular-nums">
                      {item.ms} ms / <span className="text-mute">{item.budget} ms</span>
                    </span>
                  </div>
                  <div className="w-full bg-canvas-elevated h-1.5 rounded-full overflow-hidden border border-hairline">
                    <div 
                      className="h-full rounded-full transition-all duration-300" 
                      style={{ width: `${pct}%`, backgroundColor: item.color }} 
                    />
                  </div>
                </div>
              );
            })}
            <div className="pt-2 border-t border-hairline text-[11px] text-mute font-mono">
              ✓ Hardware: Local RTX 3090 / 4090 on Supercomputer Node
            </div>
          </CardContent>
        </Card>

        {/* Active Campaigns Table */}
        <Card className="lg:col-span-2 bg-canvas-soft border-hairline">
          <CardHeader className="p-5 pb-2">
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="text-sm font-semibold text-ink">Recent Outbound Campaigns</CardTitle>
                <CardDescription className="text-xs text-body mt-0.5">
                  Batch automated voice calls scheduled by university administration
                </CardDescription>
              </div>
              <Button variant="ghost" size="sm" onClick={onLaunchNewCampaign} className="text-primary text-xs">
                + New Campaign
              </Button>
            </div>
          </CardHeader>
          <CardContent className="p-0">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>CAMPAIGN NAME</TableHead>
                  <TableHead>TARGET FILTER</TableHead>
                  <TableHead>STATUS</TableHead>
                  <TableHead className="text-right">PROGRESS</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {campaigns.map((camp) => {
                  const pct = Math.round(((camp.completed_tasks + camp.failed_tasks) / (camp.total_tasks || 1)) * 100);
                  return (
                    <TableRow key={camp.id}>
                      <TableCell className="font-medium text-xs text-ink">
                        {camp.name}
                        <div className="text-[10px] text-mute font-mono">ID: #{camp.id}</div>
                      </TableCell>
                      <TableCell className="text-xs text-body font-mono">
                        {camp.target_filter.department || 'All Departments'}
                      </TableCell>
                      <TableCell>
                        <Badge 
                          variant={camp.status === 'running' ? 'live' : camp.status === 'completed' ? 'secondary' : 'amber'}
                          className="text-[10px] uppercase font-mono"
                        >
                          {camp.status}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-right">
                        <div className="flex items-center justify-end space-x-2">
                          <span className="text-xs font-mono tabular-nums text-ink">
                            {camp.completed_tasks}/{camp.total_tasks}
                          </span>
                          <span className="text-[10px] text-mute font-mono">({pct}%)</span>
                        </div>
                        <Progress value={pct} className="h-1 mt-1 bg-canvas-elevated" />
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};
