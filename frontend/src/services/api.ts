/**
 * API Service Client & Telemetry Data Contracts Module.
 *
 * This module defines the complete TypeScript interfaces, data transfer objects (DTOs),
 * and client-side initial seed fixtures for the Nirma University AI Call Agent Web Portal.
 * It serves as the single source of truth for all telemetry metrics, campaign scheduling,
 * conversational transcript logging, and carrier task statuses consumed by the dashboard.
 *
 * Architectural Role:
 *     - Establishes strict data schemas mirroring backend Pydantic models (backend/database/models.py).
 *     - Provides resilient offline data fixtures for UI development and fallback when backend is disconnected.
 *     - Coordinates WebSocket telemetry contracts (/ws/calls) and REST endpoints (/api/v1/*).
 *
 * Upstream dependencies:
 *     - Backend FastAPI REST & WebSocket server (backend/main.py)
 * Downstream dependencies:
 *     - frontend/src/App.tsx
 *     - frontend/src/components/DashboardView.tsx
 *     - frontend/src/components/LiveTelemetryView.tsx
 *     - frontend/src/components/CampaignLauncherView.tsx
 *     - frontend/src/components/TranscriptView.tsx
 *
 * @packageDocumentation
 */

// ==============================================================================
// 1. Staff & Identity Schemas
// ==============================================================================

/**
 * Represents an authenticated Nirma University staff member or portal administrator.
 *
 * Roles determine authorization boundaries:
 *  - 'admin': Full clearance to launch, cancel campaigns, edit prompts, and trigger manual retries.
 *  - 'operator': Operational access to monitor live streaming calls and review historical transcripts.
 */
export interface StaffUser {
  /** Unique primary surrogate identifier from backend database. */
  id: number;
  /** Verified institutional email address (e.g., 'operator@nirmauni.ac.in'). */
  email: string;
  /** Full human name of the staff operator. */
  name: string;
  /** Role-based access control level. */
  role: 'admin' | 'operator';
}

// ==============================================================================
// 2. Call Script & Prompt Engineering Schemas
// ==============================================================================

/**
 * Predefined and verified telephony conversation template.
 *
 * Scripts encapsulate the opening spoken greeting and the system persona prompt
 * sent to the local LLM (Qwen-14B) or cloud fallback (Groq LLaMA-3.3-70B).
 */
export interface CallScript {
  /** Unique database identifier. */
  id: number;
  /** Human-readable script name (e.g., 'Semester Fee Payment Reminder (Hindi)'). */
  name: string;
  /** Categorical classification: 'fee_reminder', 'attendance_alert', 'exam_notice'. */
  category: string;
  /** ISO 639-1 language code ('hi' for Hindi, 'gu' for Gujarati, 'en' for English). */
  language: string;
  /**
   * System persona instructions injected into the LLM conversational context.
   * Mandates polite tone, institutional affiliation, and brevity (<35 words).
   */
  system_prompt: string;
  /**
   * First spoken greeting synthesized via TTS and played immediately upon recipient answer.
   * TRAI telecom compliance requires self-identification as an automated AI system in this turn.
   */
  opening_message: string;
}

// ==============================================================================
// 3. Campaign & Task Execution Schemas
// ==============================================================================

/**
 * Outbound batch campaign scheduled by university administrators.
 *
 * Represents an orchestrated sequence of phone calls generated against
 * a targeted student cohort filter (e.g., department, semester, attendance threshold).
 */
export interface CallCampaign {
  /** Unique campaign identifier. */
  id: number;
  /** Campaign title displayed across dashboard and reports. */
  name: string;
  /** Foreign key pointing to the active CallScript template. */
  script_id: number;
  /** JSON criteria used by the Celery dispatcher to select eligible student recipients. */
  target_filter: Record<string, any>;
  /** Target UTC timestamp when the Celery dispatcher begins placing carrier calls. */
  scheduled_at: string;
  /** Maximum number of retry attempts for unanswered or busy calls (default: 2). */
  max_retries: number;
  /** Waiting interval in minutes before triggering an unanswered call retry (default: 45m). */
  retry_delay_min: number;
  /** Real-time execution status of the campaign batch. */
  status: 'pending' | 'running' | 'completed' | 'cancelled';
  /** Total number of student phone calls scheduled in this batch. */
  total_tasks: number;
  /** Number of calls successfully completed and answered. */
  completed_tasks: number;
  /** Number of calls that failed or exhausted retry limits. */
  failed_tasks: number;
}

/**
 * Discrete outbound PSTN phone call placed to an individual student or guardian.
 *
 * Tracks carrier request UUIDs, real-time call states, timing milestones, and live turn snippets.
 */
export interface CallTask {
  /** Unique database task identifier. */
  id: number;
  /** Foreign key referencing the parent CallCampaign batch. */
  campaign_id: number;
  /** Foreign key referencing the student recipient profile. */
  student_id: number;
  /** Full student name from university ERP. */
  student_name: string;
  /** Unique university enrollment roll number (e.g., '22BCE045'). */
  student_roll: string;
  /** Target recipient phone number in E.164 international format (+91...). */
  student_phone: string;
  /** Script template identifier utilized for this call session. */
  script_id: number;
  /**
   * Real-time telephony state:
   *  - 'pending': Queued in Redis awaiting Celery rate limiter dispatch.
   *  - 'ringing': Carrier signaled outbound ringing on Indian PSTN network.
   *  - 'in_progress': Call answered; audio stream and turn processing active.
   *  - 'completed': Call terminated normally after conversation resolution.
   *  - 'failed': Call rejected, carrier timeout, or busy without answer.
   */
  status: 'pending' | 'ringing' | 'in_progress' | 'completed' | 'failed';
  /** Unique carrier request UUID assigned by Plivo telephony gateway. */
  plivo_uuid?: string;
  /** Current retry attempt count for this specific recipient. */
  retry_count: number;
  /** Total connected conversational duration in seconds. */
  duration_sec?: number;
  /** Final carrier disposition: 'completed', 'no_answer', 'busy', 'failed'. */
  outcome?: string;
  /** Human-readable relative timestamp indicating when the call was dialed. */
  placed_at?: string;
  /** Real-time conversational turn snippet streaming over WebSocket for active monitoring. */
  current_turn?: string;
  /** Turn turnaround latency in milliseconds for the latest exchange (<4,000ms SLA target). */
  turn_latency_ms?: number;
}

// ==============================================================================
// 4. Conversation Transcript & Telemetry Schemas
// ==============================================================================

/**
 * Individual conversational dialogue turn between the AI agent and the human recipient.
 */
export interface TranscriptTurn {
  /** Turn speaker attribution: 'assistant' (AI agent) or 'user' (student/parent). */
  role: 'assistant' | 'user' | 'system';
  /** Clean textual transcript of the speech utterance. */
  text: string;
  /** Time of day when the utterance was logged (HH:MM:SS format). */
  timestamp?: string;
  /** Latency in milliseconds taken to process and synthesize this specific turn. */
  latency_ms?: number;
}

/**
 * Comprehensive historical audit record of a completed or failed phone call.
 *
 * Stores the full multi-turn transcript array, provider attribution tags,
 * turn turnaround latency metrics, and persistent MinIO/S3 audio recording URL.
 */
export interface CallLog {
  /** Unique database identifier. */
  id: number;
  /** Foreign key linking back to the originating CallTask. */
  task_id: number;
  /** Chronological array of conversational turns. */
  transcript: TranscriptTurn[];
  /** Name of speech recognition engine utilized ('IndicConformer (0.6B)' | 'Sarvam AI'). */
  stt_provider: string;
  /** Name of language model engine utilized ('Qwen-14B (Ollama Q4)' | 'Groq Cloud'). */
  llm_provider: string;
  /** Name of speech synthesis engine utilized ('IndicF5 (Local)' | 'Google Cloud TTS'). */
  tts_provider: string;
  /** Mean turnaround latency across all turns in milliseconds. */
  avg_latency_ms: number;
  /** Peak turnaround latency observed in milliseconds. */
  max_latency_ms: number;
  /** Fully qualified HTTPS URL to the recorded carrier audio WAV file. */
  audio_url?: string;
}

// ==============================================================================
// 5. Analytical Dashboard KPI Schemas
// ==============================================================================

/**
 * Executive KPI summary metrics displayed on the primary mission control dashboard.
 */
export interface DashboardSummary {
  /** Cumulative count of all campaigns created. */
  total_campaigns: number;
  /** Count of campaigns currently in 'running' or 'pending' state. */
  active_campaigns: number;
  /** Total calls dialed across the system lifetime. */
  total_calls: number;
  /** Number of calls successfully connected and answered. */
  completed_calls: number;
  /** Number of calls that failed, timed out, or encountered carrier errors. */
  failed_calls: number;
  /** Percentage of dialed calls that connected successfully (e.g., 94.2%). */
  connection_rate_pct: number;
  /** Average duration in seconds of answered phone calls. */
  avg_duration_sec: number;
  /** Average end-to-end turn turnaround latency across all AI pipeline engines. */
  avg_turn_latency_ms: number;
}

/**
 * Time-series data point representing call volume grouped by calendar day.
 */
export interface DailyVolume {
  /** Formatted calendar date label (e.g., 'Oct 08'). */
  date: string;
  /** Total calls dialed on this date. */
  total_calls: number;
  /** Connected and answered calls on this date. */
  completed_calls: number;
  /** Unanswered or failed calls on this date. */
  failed_calls: number;
}

/**
 * Distribution breakdown of final carrier call outcomes.
 */
export interface OutcomeDistribution {
  /** Mapping of disposition keys ('completed', 'no_answer', 'busy', 'failed') to counts. */
  outcome_counts: Record<string, number>;
}

/**
 * Technical latency and provider distribution telemetry for engineering monitoring.
 */
export interface LatencyMetric {
  /** Turn counts grouped by speech recognition engine. */
  stt_provider_counts: Record<string, number>;
  /** Turn counts grouped by language model engine. */
  llm_provider_counts: Record<string, number>;
  /** Turn counts grouped by speech synthesis engine. */
  tts_provider_counts: Record<string, number>;
  /** System-wide average turn latency in milliseconds. */
  avg_latency_ms: number;
  /** System-wide peak turnaround latency logged in milliseconds. */
  max_latency_ms: number;
}

// ==============================================================================
// 6. Seed & Offline Fallback Fixtures
// ==============================================================================

/**
 * Verified call script templates pre-approved by the Nirma University Academic Cell.
 * Mirrors initial database seeds from backend/seeds.py for offline UI resilience.
 */
export const INITIAL_SCRIPTS: CallScript[] = [
  {
    id: 1,
    name: "Semester Fee Payment Reminder (Hindi)",
    category: "fee_reminder",
    language: "hi",
    system_prompt: "You are an automated caller from Nirma University Finance Office. Inquire politely if the student or parent has cleared the semester fee deadline of October 15th. Limit replies to under 30 words. Speak respectful Hindi.",
    opening_message: "नमस्ते, मैं निरमा यूनिवर्सिटी के अकाउंट ऑफिस से एक ऑटोमेटेड AI असिस्टेंट बोल रहा हूँ। यह कॉल सेमेस्टर फीस के संबंध में है।"
  },
  {
    id: 2,
    name: "Semester Fee Payment Reminder (Gujarati)",
    category: "fee_reminder",
    language: "gu",
    system_prompt: "You are an automated voice assistant from Nirma University Finance Office. Remind regarding the fee due date. Limit response to 30 words. Speak polite Gujarati.",
    opening_message: "નમસ્તે, હું નિરમા યુનિવર્સિટીના હિસાબ વિભાગમાંથી ઓટોમેટેડ AI સહાયક બોલી રહ્યો છું. આ કોલ સેમેસ્ટર ફી સંદર્ભે છે."
  },
  {
    id: 3,
    name: "Semester Fee Payment Reminder (English)",
    category: "fee_reminder",
    language: "en",
    system_prompt: "You are an automated voice assistant from Nirma University. Inform student that the semester payment deadline is October 15th. Answer concisely under 35 words.",
    opening_message: "Hello, this is an automated AI calling assistant from Nirma University Finance Office regarding semester tuition fees."
  },
  {
    id: 4,
    name: "Low Attendance Warning Notice (Hindi)",
    category: "attendance_alert",
    language: "hi",
    system_prompt: "You are Nirma University Academic Dean office calling assistant. Inform that current attendance is below 75% required threshold for final examinations. Stay polite and under 30 words.",
    opening_message: "नमस्ते, यह निरमा यूनिवर्सिटी के एकेडमिक डीन ऑफिस से ऑटोमेटेड कॉल है। आपकी अटेंडेंस 75 प्रतिशत से कम दर्ज की गई है।"
  },
  {
    id: 5,
    name: "End-Semester Examination Schedule (English)",
    category: "exam_notice",
    language: "en",
    system_prompt: "You are Nirma University Examination Cell assistant. Announce that admit cards and hall tickets for winter end-semester exams are available online. Keep responses under 35 words.",
    opening_message: "Greetings, this is an automated announcement from Nirma University Examination Section regarding winter semester exams."
  }
];

/**
 * Initial sample campaigns populated on portal boot to provide immediate operational context.
 */
export const INITIAL_CAMPAIGNS: CallCampaign[] = [
  {
    id: 101,
    name: "BTech CSE Semester 5 — Fee Final Notice",
    script_id: 1,
    target_filter: { department: "Computer Science & Engineering", semester: 5 },
    scheduled_at: "2026-10-10T10:00:00Z",
    max_retries: 2,
    retry_delay_min: 60,
    status: "running",
    total_tasks: 240,
    completed_tasks: 182,
    failed_tasks: 14
  },
  {
    id: 102,
    name: "Mechanical Engg Semester 7 — Attendance Alert",
    script_id: 4,
    target_filter: { department: "Mechanical Engineering", attendance_lt: 75 },
    scheduled_at: "2026-10-09T14:30:00Z",
    max_retries: 3,
    retry_delay_min: 45,
    status: "running",
    total_tasks: 78,
    completed_tasks: 45,
    failed_tasks: 6
  },
  {
    id: 103,
    name: "MCA Semester 3 — Winter Exam Hall Ticket Dispatch",
    script_id: 5,
    target_filter: { department: "Computer Applications", semester: 3 },
    scheduled_at: "2026-10-08T09:00:00Z",
    max_retries: 2,
    retry_delay_min: 60,
    status: "completed",
    total_tasks: 120,
    completed_tasks: 115,
    failed_tasks: 5
  }
];

/**
 * Initial sample call tasks actively monitored on the live telemetry console.
 */
export const INITIAL_TASKS: CallTask[] = [
  {
    id: 501,
    campaign_id: 101,
    student_id: 2001,
    student_name: "Aarav Sharma",
    student_roll: "22BCE045",
    student_phone: "+91 98765 43210",
    script_id: 1,
    status: "in_progress",
    plivo_uuid: "plv_88f921a4-c24d",
    retry_count: 0,
    duration_sec: 42,
    placed_at: "Just now",
    current_turn: "Student: 'जी, क्या मैं ऑनलाइन पोर्टल से UPI द्वारा पेमेंट कर सकता हूँ?'",
    turn_latency_ms: 1840
  },
  {
    id: 502,
    campaign_id: 101,
    student_id: 2002,
    student_name: "Pooja Patel",
    student_roll: "22BCE089",
    student_phone: "+91 98251 77342",
    script_id: 1,
    status: "ringing",
    plivo_uuid: "plv_99e11b33-e18a",
    retry_count: 0,
    placed_at: "10s ago",
    current_turn: "Ringing on Indian PSTN Network (+9198251...)",
    turn_latency_ms: 0
  },
  {
    id: 503,
    campaign_id: 102,
    student_id: 2003,
    student_name: "Devang Joshi",
    student_roll: "21BME012",
    student_phone: "+91 94280 61129",
    script_id: 4,
    status: "in_progress",
    plivo_uuid: "plv_44c88210-b991",
    retry_count: 1,
    duration_sec: 28,
    placed_at: "24s ago",
    current_turn: "AI: 'जी, आप कल सुबह 11 बजे अपने फैकल्टी एडवाइजर से मिल सकते हैं।'",
    turn_latency_ms: 2150
  },
  {
    id: 504,
    campaign_id: 101,
    student_id: 2004,
    student_name: "Ananya Mehta",
    student_roll: "22BCE114",
    student_phone: "+91 99099 24501",
    script_id: 1,
    status: "completed",
    plivo_uuid: "plv_12d45678-a001",
    retry_count: 0,
    duration_sec: 68,
    outcome: "completed",
    placed_at: "3m ago",
    turn_latency_ms: 1650
  },
  {
    id: 505,
    campaign_id: 101,
    student_id: 2005,
    student_name: "Rohan Varma",
    student_roll: "22BCE019",
    student_phone: "+91 97123 45678",
    script_id: 1,
    status: "failed",
    plivo_uuid: "plv_33b87910-c441",
    retry_count: 2,
    duration_sec: 0,
    outcome: "no_answer",
    placed_at: "12m ago",
    turn_latency_ms: 0
  }
];

/**
 * Historical conversation transcripts and turn turnaround latencies for completed calls.
 */
export const INITIAL_TRANSCRIPTS: Record<number, CallLog> = {
  501: {
    id: 901,
    task_id: 501,
    stt_provider: "IndicConformer (0.6B)",
    llm_provider: "Qwen-14B (Ollama Q4)",
    tts_provider: "IndicF5 (Local)",
    avg_latency_ms: 1840,
    max_latency_ms: 2420,
    audio_url: "https://calls.nirmauni.ac.in/static/audio/sample_501.wav",
    transcript: [
      {
        role: "assistant",
        text: "नमस्ते, मैं निरमा यूनिवर्सिटी के अकाउंट ऑफिस से एक ऑटोमेटेड AI असिस्टेंट बोल रहा हूँ। यह कॉल सेमेस्टर फीस के संबंध में है। क्या आप आरव शर्मा के अभिभावक बात कर रहे हैं?",
        timestamp: "12:40:02",
        latency_ms: 450
      },
      {
        role: "user",
        text: "हाँ, मैं आरव बात कर रहा हूँ। बताइए क्या बात है?",
        timestamp: "12:40:08",
        latency_ms: 1100
      },
      {
        role: "assistant",
        text: "आरव जी, सेमेस्टर 5 की फीस जमा करने की अंतिम तिथि 15 अक्टूबर है। कृपया सुनिश्चित करें कि समय पर भुगतान हो जाए।",
        timestamp: "12:40:12",
        latency_ms: 1720
      },
      {
        role: "user",
        text: "जी, क्या मैं ऑनलाइन पोर्टल से UPI द्वारा पेमेंट कर सकता हूँ?",
        timestamp: "12:40:19",
        latency_ms: 980
      },
      {
        role: "assistant",
        text: "हाँ, आप निरमा स्टूडेंट पोर्टल पर जाकर नेटबैंकिंग, कार्ड या UPI द्वारा तुरंत भुगतान कर सकते हैं।",
        timestamp: "12:40:24",
        latency_ms: 1840
      }
    ]
  },
  504: {
    id: 904,
    task_id: 504,
    stt_provider: "Sarvam AI (saaras:v4)",
    llm_provider: "Qwen-14B (Ollama Q4)",
    tts_provider: "IndicF5 (Local)",
    avg_latency_ms: 1650,
    max_latency_ms: 2100,
    audio_url: "https://calls.nirmauni.ac.in/static/audio/sample_504.wav",
    transcript: [
      {
        role: "assistant",
        text: "नमस्ते, मैं निरमा यूनिवर्सिटी के अकाउंट ऑफिस से एक ऑटोमेटेड AI असिस्टेंट बोल रहा हूँ। यह कॉल सेमेस्टर फीस के संबंध में है।",
        timestamp: "12:35:10",
        latency_ms: 480
      },
      {
        role: "user",
        text: "हाँ, हमने कल शाम को ही ऑनलाइन फीस जमा करवा दी थी।",
        timestamp: "12:35:16",
        latency_ms: 850
      },
      {
        role: "assistant",
        text: "धन्यवाद। बैंक से रसीद अपडेट होने में 24 घंटे का समय लग सकता है। आपकी पुष्टि के लिए बहुत-बहुत धन्यवाद। आपका दिन शुभ हो।",
        timestamp: "12:35:22",
        latency_ms: 1650
      }
    ]
  }
};
