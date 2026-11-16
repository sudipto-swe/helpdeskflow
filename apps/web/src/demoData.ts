export const DEMO_SAMPLE_TICKETS = [
  {
    "ticket_id": "TCK-10073",
    "customer_id": "CUST-1093",
    "customer_name": "Rifat Hossain",
    "text": "[Customer: CUST-1093] আমি ২০ মিনিট আগে বিকাশ দিয়ে বিল দিয়েছি কিন্তু এখনও লাইন বন্ধ আছে। TrxID 9K8L23NM।",
    "category": "billing",
    "priority": "medium",
    "status": "awaiting_approval",
    "confidence": 0.94,
    "draft_response": "Hello Rifat Hossain,\n\nWe have verified your payment for Customer ID CUST-1093 with TrxID 9K8L23NM via bKash. Your account status is currently being reactivated within our automated 5-10 minute gateway window. Our finance billing team has flagged this for immediate clearance.",
    "citations": ["KB-BIL-001", "KB-BIL-002"],
    "approval_required": true,
    "sentiment": "neutral",
    "language": "bn",
    "tool_calls": [
      { "tool": "search_kb", "citations": ["KB-BIL-001", "KB-BIL-002"] },
      { "tool": "get_billing_status", "result": { "status": "suspended", "balance_due": 1000.0, "package": "Family Stream 30Mbps" } }
    ],
    "trace_steps": [
      { "step": "intake", "timestamp": "2026-11-16T10:00:00Z", "details": { "ticket_id": "TCK-10073", "text_len": 94 } },
      { "step": "classify", "timestamp": "2026-11-16T10:00:00Z", "details": { "category": "billing", "priority": "medium", "language": "bn", "confidence": 0.94 } },
      { "step": "retrieve", "timestamp": "2026-11-16T10:00:01Z", "details": { "retrieved_count": 3, "citations": ["KB-BIL-001", "KB-BIL-002"] } },
      { "step": "tool_call", "timestamp": "2026-11-16T10:00:01Z", "details": { "tool": "get_billing_status", "customer_id": "CUST-1093" } },
      { "step": "draft", "timestamp": "2026-11-16T10:00:02Z", "details": { "confidence": 0.92, "citations": ["KB-BIL-002"] } },
      { "step": "approval_gate", "timestamp": "2026-11-16T10:00:02Z", "details": { "action": "paused_for_human", "reason": "Requires supervisor review due to billing category or transaction confirmation." } }
    ]
  },
  {
    "ticket_id": "TCK-10024",
    "customer_id": "CUST-1015",
    "customer_name": "Tanvir Rahman",
    "text": "speed khub kharap, 30mbps package neoar por o 5mbps pawa jacche na. youtube buffer kore.",
    "category": "technical",
    "priority": "medium",
    "status": "resolved",
    "confidence": 0.92,
    "draft_response": "Hello Tanvir,\n\nThank you for reaching out to BengalNet & Bazar support. For slow throughput issues on your 30 Mbps line, please perform the following checks:\n1. Connect directly to the router LAN port using a Cat6 cable rather than 2.4 GHz Wi-Fi, which often suffers from local interference in crowded apartments.\n2. Ensure no torrents or background updates are running.\n3. Change your DNS resolver to BengalNet local DNS (103.145.110.2) or Cloudflare (1.1.1.1).\n\nIf the issue persists, our field team will initiate an optical line SNR audit.",
    "citations": ["KB-TEC-003", "KB-TEC-006"],
    "approval_required": false,
    "sentiment": "negative",
    "language": "banglish",
    "tool_calls": [
      { "tool": "search_kb", "citations": ["KB-TEC-003", "KB-TEC-006"] }
    ],
    "trace_steps": [
      { "step": "intake", "timestamp": "2026-11-16T10:01:00Z", "details": { "ticket_id": "TCK-10024", "text_len": 87 } },
      { "step": "classify", "timestamp": "2026-11-16T10:01:00Z", "details": { "category": "technical", "priority": "medium", "language": "banglish", "confidence": 0.92 } },
      { "step": "retrieve", "timestamp": "2026-11-16T10:01:01Z", "details": { "retrieved_count": 3, "citations": ["KB-TEC-003", "KB-TEC-006"] } },
      { "step": "draft", "timestamp": "2026-11-16T10:01:01Z", "details": { "citations": ["KB-TEC-003"] } },
      { "step": "send_notification", "timestamp": "2026-11-16T10:01:02Z", "details": { "to": "tanvir.rahman15@example.com", "status": "delivered" } }
    ]
  },
  {
    "ticket_id": "TCK-10001",
    "customer_id": "CUST-1002",
    "customer_name": "Sadia Chowdhury",
    "text": "আমার ইন্টারনেট কাজ করছে না। ONU তে লাল বাতি জ্বলছে নিভছে (LOS)। অনুগ্রহ করে দ্রুত ঠিক করুন।",
    "category": "technical",
    "priority": "high",
    "status": "resolved",
    "confidence": 0.95,
    "draft_response": "সালাম সাদিয়া চৌধুরী,\n\nআপনার ONU ডিভাইসে লাল LOS (Loss of Signal) বাতি জ্বললে বুঝতে হবে মূল অপটিক্যাল ফাইবার তারে কোনো সংযোগ বিচ্ছিন্ন বা ভাঁজ হয়েছে।\nঅনুগ্রহ করে নীল প্যাচ কর্ডটি আলতোভাবে চেক করুন কিন্তু ফাইবার টিপ খালি হাতে স্পর্শ করবেন না।\nআমাদের ধানমন্ডি স্থানীয় জরুরি ফাইবার মেরামতের দল আপনার এলাকায় ইতিমধ্যেই সতর্ক অবস্থায় রয়েছে (SLA: ৪ ঘণ্টার মধ্যে সমাধান)।",
    "citations": ["KB-TEC-001", "KB-TEC-005"],
    "approval_required": false,
    "sentiment": "negative",
    "language": "bn",
    "tool_calls": [
      { "tool": "search_kb", "citations": ["KB-TEC-001", "KB-TEC-005"] }
    ],
    "trace_steps": [
      { "step": "intake", "timestamp": "2026-11-16T10:02:00Z", "details": { "ticket_id": "TCK-10001", "text_len": 96 } },
      { "step": "classify", "timestamp": "2026-11-16T10:02:00Z", "details": { "category": "technical", "priority": "high", "language": "bn", "confidence": 0.95 } },
      { "step": "retrieve", "timestamp": "2026-11-16T10:02:01Z", "details": { "retrieved_count": 3, "citations": ["KB-TEC-001", "KB-TEC-005"] } },
      { "step": "draft", "timestamp": "2026-11-16T10:02:01Z", "details": { "citations": ["KB-TEC-001"] } },
      { "step": "send_notification", "timestamp": "2026-11-16T10:02:02Z", "details": { "to": "sadia.chowdhury02@example.com", "status": "delivered" } }
    ]
  },
  {
    "ticket_id": "TCK-10099",
    "customer_id": "CUST-1040",
    "customer_name": "Arif Uddin",
    "text": "Your company is fraudulent! Overcharging me every month. I will report to BTRC and take legal action!",
    "category": "escalation",
    "priority": "urgent",
    "status": "escalated",
    "confidence": 0.97,
    "draft_response": "Your case has been logged under priority escalation and immediately transferred to a Senior Human Support Operations Manager for audit.",
    "citations": ["KB-SEC-002"],
    "approval_required": true,
    "sentiment": "hostile",
    "language": "en",
    "tool_calls": [
      { "tool": "escalate_to_human", "result": { "queue": "tier_2_human_supervisors", "priority": "urgent" } }
    ],
    "trace_steps": [
      { "step": "intake", "timestamp": "2026-11-16T10:03:00Z", "details": { "ticket_id": "TCK-10099", "text_len": 99 } },
      { "step": "classify", "timestamp": "2026-11-16T10:03:00Z", "details": { "category": "escalation", "priority": "urgent", "sentiment": "hostile", "confidence": 0.97 } },
      { "step": "escalate", "timestamp": "2026-11-16T10:03:01Z", "details": { "reason": "High severity or sensitive category (escalation)", "target": "tier_2_supervisors" } }
    ]
  },
  {
    "ticket_id": "TCK-10045",
    "customer_id": "CUST-1033",
    "customer_name": "Fatima Begum",
    "text": "I was offline for 6 hours yesterday. I want a 100% full cash refund right now to my bKash account.",
    "category": "policy",
    "priority": "high",
    "status": "awaiting_approval",
    "confidence": 0.91,
    "draft_response": "Hello Fatima,\n\nUnder BengalNet & Bazar Policy Section 2.1, subscription fees are non-refundable in cash. Prorated credit note adjustments apply when verified core ISP downtime exceeds 72 consecutive hours. Your reported outage was 6 hours. We are forwarding this to a supervisor for bill adjustment evaluation.",
    "citations": ["KB-POL-001"],
    "approval_required": true,
    "sentiment": "negative",
    "language": "en",
    "tool_calls": [
      { "tool": "check_refund_policy", "result": { "eligible": false, "reason": "Outage must exceed 72 consecutive hours (reported: 6 hrs)", "requires_approval": true } }
    ],
    "trace_steps": [
      { "step": "intake", "timestamp": "2026-11-16T10:04:00Z", "details": { "ticket_id": "TCK-10045", "text_len": 95 } },
      { "step": "classify", "timestamp": "2026-11-16T10:04:00Z", "details": { "category": "policy", "priority": "high", "confidence": 0.91 } },
      { "step": "policy_check", "timestamp": "2026-11-16T10:04:01Z", "details": { "eligible": false, "refund_type": "none" } },
      { "step": "draft", "timestamp": "2026-11-16T10:04:01Z", "details": { "citations": ["KB-POL-001"] } },
      { "step": "approval_gate", "timestamp": "2026-11-16T10:04:02Z", "details": { "action": "paused_for_human", "reason": "Policy rejection on cash refund request." } }
    ]
  }
];
