import React from 'react';
import { PhoneCall, Activity, Radio, Cpu, Clock, ShieldCheck } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';

interface HeaderProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  activeCallCount: number;
}

export const Header: React.FC<HeaderProps> = ({ activeTab, setActiveTab, activeCallCount }) => {
  return (
    <header className="border-b border-hairline bg-canvas-subtle/95 backdrop-blur-md sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* University Brand & Logo */}
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-md bg-gradient-to-br from-primary to-primary-deep flex items-center justify-center shadow-lg shadow-orange-950/40 border border-orange-400/20">
              <PhoneCall className="w-5 h-5 text-white" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="font-semibold text-base tracking-tight text-ink font-sans">NIRMA UNIVERSITY</span>
                <Badge variant="mono" className="text-[10px] text-primary border-hairline-terracotta bg-primary/10">
                  HPC MISSION CONTROL
                </Badge>
              </div>
              <p className="text-xs text-mute font-mono">Automated Voice Agent System • v1.0 Production</p>
            </div>
          </div>

          {/* Telemetry Status Bar */}
          <div className="hidden lg:flex items-center space-x-5 text-xs font-mono text-body bg-canvas-soft px-3.5 py-1.5 rounded-full border border-hairline">
            <div className="flex items-center space-x-2">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-live-pulse opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-live-pulse"></span>
              </span>
              <span>PSTN Gateway: <strong className="text-live-pulse">Plivo Active</strong></span>
            </div>
            <div className="h-3 w-px bg-hairline" />
            <div className="flex items-center space-x-1.5">
              <Cpu className="w-3.5 h-3.5 text-telemetry-cyan" />
              <span>Ollama GPU: <strong className="text-telemetry-cyan-soft">Qwen-14B (4-bit)</strong></span>
            </div>
            <div className="h-3 w-px bg-hairline" />
            <div className="flex items-center space-x-1.5">
              <Clock className="w-3.5 h-3.5 text-telemetry-amber" />
              <span>TRAI Window: <strong className="text-ink">09:00 - 21:00 IST</strong></span>
            </div>
          </div>

          {/* Staff Profile & Status */}
          <div className="flex items-center space-x-3">
            <div className="text-right hidden sm:block">
              <div className="text-xs font-medium text-ink">Urva Gandhi</div>
              <div className="text-[10px] font-mono text-live-pulse flex items-center justify-end space-x-1">
                <ShieldCheck className="w-3 h-3 inline" />
                <span>Super Administrator</span>
              </div>
            </div>
            <Avatar className="h-8 w-8 border border-hairline">
              <AvatarFallback className="bg-gradient-to-tr from-telemetry-cyan to-primary-deep text-white text-xs">
                UG
              </AvatarFallback>
            </Avatar>
          </div>
        </div>

        {/* Tab Navigation */}
        <nav className="flex space-x-1 overflow-x-auto py-2 -mb-px">
          {[
            { id: 'dashboard', label: 'Analytics & KPIs', icon: Activity },
            { id: 'telemetry', label: 'Live Telemetry', icon: Radio, badge: activeCallCount },
            { id: 'campaigns', label: 'Campaign Launcher', icon: PhoneCall },
            { id: 'transcripts', label: 'Transcripts & Call Logs', icon: Clock },
          ].map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <Button
                key={tab.id}
                variant={isActive ? "default" : "ghost"}
                size="sm"
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center space-x-2 text-xs font-medium whitespace-nowrap rounded ${
                  isActive
                    ? 'bg-primary text-white shadow-sm'
                    : 'text-body hover:text-ink hover:bg-canvas-elevated'
                }`}
              >
                <Icon className={`w-3.5 h-3.5 ${isActive ? 'text-white' : 'text-body'}`} />
                <span>{tab.label}</span>
                {tab.badge !== undefined && tab.badge > 0 && (
                  <Badge
                    variant={isActive ? "secondary" : "live"}
                    className="ml-1 px-1.5 py-0 text-[10px] font-mono tabular-nums"
                  >
                    {tab.badge}
                  </Badge>
                )}
              </Button>
            );
          })}
        </nav>
      </div>
    </header>
  );
};
