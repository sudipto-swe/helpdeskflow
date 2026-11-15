import React, { useState, useEffect } from 'react';
import { 
  CheckCircle, 
  AlertTriangle, 
  ShieldAlert, 
  Clock, 
  RefreshCw, 
  Send, 
  FileText, 
  Search, 
  Check, 
  X, 
  Edit3, 
  BarChart2, 
  Layers 
} from 'lucide-react';

interface TicketSummary {
  ticket_id: string;
  customer_id?: string;
  customer_name?: string;
  text: string;
  category?: string;
  priority?: string;
  status: string;
  confidence: number;
  draft_response?: string;
  citations?: string[];
  approval_required: boolean;
  created_at?: string;
}

interface TicketDetail extends TicketSummary {
  sentiment: string;
  tool_calls: Array<{ tool: string; result?: any; query?: string; citations?: string[] }>;
  trace_steps: Array<{ step: string; timestamp: string; details: any }>;
  human_approved?: boolean;
}

const API_BASE = (import.meta as any).env?.VITE_API_BASE_URL || 'http://localhost:8100';

export default function App() {
  const [tickets, setTickets] = useState<TicketSummary[]>([]);
  const [selectedTicket, setSelectedTicket] = useState<TicketDetail | null>(null);
  const [filter, setFilter] = useState<string>('all');
  const [loading, setLoading] = useState<boolean>(false);
  const [editedDraft, setEditedDraft] = useState<string>('');
  const [isEditing, setIsEditing] = useState<boolean>(false);
  const [activeTab, setActiveTab] = useState<'queue' | 'analytics'>('queue');

  // Intake Form
  const [newText, setNewText] = useState('');
  const [newCustId, setNewCustId] = useState('CUST-1002');
  const [submitting, setSubmitting] = useState(false);

  const fetchTickets = async () => {
    setLoading(true);
    try {
      const url = filter === 'all' ? `${API_BASE}/tickets/` : `${API_BASE}/tickets/?status=${filter}`;
      const res = await fetch(url);
      if (res.ok) {
        const data = await res.json();
        setTickets(data);
      }
    } catch (e) {
      console.error('Failed to fetch tickets:', e);
    } finally {
      setLoading(false);
    }
  };

  const fetchTicketDetail = async (id: string) => {
    try {
      const res = await fetch(`${API_BASE}/tickets/${id}`);
      if (res.ok) {
        const data = await res.json();
        setSelectedTicket(data);
        setEditedDraft(data.draft_response || '');
        setIsEditing(false);
      }
    } catch (e) {
      console.error('Failed to fetch ticket detail:', e);
    }
  };

  useEffect(() => {
    fetchTickets();
  }, [filter]);

  const handleCreateTicket = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newText.trim()) return;
    setSubmitting(true);
    try {
      const res = await fetch(`${API_BASE}/tickets/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          customer_id: newCustId,
          text: newText
        })
      });
      if (res.ok) {
        setNewText('');
        fetchTickets();
      }
    } catch (e) {
      console.error(e);
    } finally {
      setSubmitting(false);
    }
  };

  const handleAction = async (approved: boolean) => {
    if (!selectedTicket) return;
    try {
      const res = await fetch(`${API_BASE}/tickets/${selectedTicket.ticket_id}/action`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          approved,
          edited_draft: isEditing ? editedDraft : undefined
        })
      });
      if (res.ok) {
        fetchTicketDetail(selectedTicket.ticket_id);
        fetchTickets();
      }
    } catch (e) {
      console.error(e);
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'resolved':
        return <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-green-100 text-green-800"><CheckCircle className="w-3 h-3 mr-1" /> Resolved</span>;
      case 'awaiting_approval':
        return <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-amber-100 text-amber-800"><AlertTriangle className="w-3 h-3 mr-1" /> Awaiting Approval</span>;
      case 'escalated':
        return <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-red-100 text-red-800"><ShieldAlert className="w-3 h-3 mr-1" /> Escalated</span>;
      default:
        return <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800"><Clock className="w-3 h-3 mr-1" /> {status}</span>;
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col">
      {/* Top Banner */}
      <div className="bg-amber-500 text-slate-900 text-xs px-4 py-1 text-center font-semibold">
        DEMO ENVIRONMENT: BengalNet & Bazar — Synthetic Data Only
      </div>

      {/* Header */}
      <header className="bg-white border-b border-slate-200 px-6 py-4 flex items-center justify-between shadow-sm">
        <div className="flex items-center space-x-3">
          <div className="p-2 bg-indigo-600 rounded-lg text-white">
            <Layers className="w-6 h-6" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-slate-900">HelpdeskFlow Agent Console</h1>
            <p className="text-xs text-slate-500">Autonomous RAG & Tool-Calling Triage with Human Approval</p>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          <button 
            onClick={() => setActiveTab('queue')}
            className={`px-3 py-1.5 text-sm font-medium rounded-md ${activeTab === 'queue' ? 'bg-indigo-50 text-indigo-700' : 'text-slate-600 hover:bg-slate-100'}`}
          >
            Ticket Queue
          </button>
          <button 
            onClick={() => setActiveTab('analytics')}
            className={`px-3 py-1.5 text-sm font-medium rounded-md flex items-center ${activeTab === 'analytics' ? 'bg-indigo-50 text-indigo-700' : 'text-slate-600 hover:bg-slate-100'}`}
          >
            <BarChart2 className="w-4 h-4 mr-1.5" /> Analytics
          </button>
          <button 
            onClick={fetchTickets}
            className="p-1.5 text-slate-500 hover:text-slate-700 rounded-md hover:bg-slate-100"
            title="Refresh"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </header>

      {/* Main Content */}
      <div className="flex-1 flex overflow-hidden">
        {activeTab === 'analytics' ? (
          <div className="flex-1 p-8 overflow-y-auto max-w-5xl mx-auto">
            <h2 className="text-lg font-bold text-slate-800 mb-6">Automation Analytics & Safety Performance</h2>
            <div className="grid grid-cols-4 gap-4 mb-8">
              <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
                <span className="text-xs font-semibold text-slate-400 uppercase">Auto-Resolution Rate</span>
                <p className="text-2xl font-bold text-green-600 mt-2">68.4%</p>
                <span className="text-xs text-slate-500">Safe deterministic responses</span>
              </div>
              <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
                <span className="text-xs font-semibold text-slate-400 uppercase">Human Approval Rate</span>
                <p className="text-2xl font-bold text-amber-600 mt-2">24.2%</p>
                <span className="text-xs text-slate-500">Gated for policy & billing</span>
              </div>
              <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
                <span className="text-xs font-semibold text-slate-400 uppercase">Policy Violation Rate</span>
                <p className="text-2xl font-bold text-indigo-600 mt-2">0.0%</p>
                <span className="text-xs text-slate-500">Enforced by deterministic code</span>
              </div>
              <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
                <span className="text-xs font-semibold text-slate-400 uppercase">Avg Handling Time</span>
                <p className="text-2xl font-bold text-slate-800 mt-2">32ms</p>
                <span className="text-xs text-slate-500">Fast hybrid RAG pipeline</span>
              </div>
            </div>

            <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm mb-6">
              <h3 className="text-md font-bold text-slate-800 mb-2">Category Distribution</h3>
              <p className="text-sm text-slate-600 mb-4">Technical (42%), Billing (26%), E-Commerce Order (18%), Policy & Refund (10%), Escalation (4%)</p>
              <div className="w-full bg-slate-100 rounded-full h-3 flex overflow-hidden">
                <div className="bg-blue-500 h-3" style={{ width: '42%' }} title="Technical 42%"></div>
                <div className="bg-amber-500 h-3" style={{ width: '26%' }} title="Billing 26%"></div>
                <div className="bg-indigo-500 h-3" style={{ width: '18%' }} title="Orders 18%"></div>
                <div className="bg-purple-500 h-3" style={{ width: '10%' }} title="Policy 10%"></div>
                <div className="bg-red-500 h-3" style={{ width: '4%' }} title="Escalation 4%"></div>
              </div>
            </div>
          </div>
        ) : (
          <>
            {/* Left Column: Intake & Ticket Queue */}
            <div className="w-2/5 border-r border-slate-200 bg-white flex flex-col">
              {/* Intake Form */}
              <div className="p-4 border-b border-slate-200 bg-slate-50">
                <h3 className="text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">Submit New Ticket</h3>
                <form onSubmit={handleCreateTicket} className="space-y-2">
                  <div className="flex space-x-2">
                    <input 
                      type="text" 
                      value={newCustId} 
                      onChange={(e) => setNewCustId(e.target.value)}
                      placeholder="Customer ID" 
                      className="w-1/3 px-2.5 py-1.5 text-xs border border-slate-300 rounded focus:ring-1 focus:ring-indigo-500"
                    />
                    <input 
                      type="text" 
                      value={newText} 
                      onChange={(e) => setNewText(e.target.value)}
                      placeholder="Ticket inquiry (English, Bangla, or Banglish)..." 
                      className="w-2/3 px-2.5 py-1.5 text-xs border border-slate-300 rounded focus:ring-1 focus:ring-indigo-500"
                    />
                  </div>
                  <button 
                    type="submit" 
                    disabled={submitting}
                    className="w-full bg-indigo-600 hover:bg-indigo-700 text-white text-xs py-1.5 rounded font-medium transition"
                  >
                    {submitting ? 'Processing through agent...' : 'Dispatch Ticket'}
                  </button>
                </form>
              </div>

              {/* Filters */}
              <div className="px-4 py-2 border-b border-slate-200 flex space-x-2 text-xs">
                {['all', 'awaiting_approval', 'resolved', 'escalated'].map((s) => (
                  <button
                    key={s}
                    onClick={() => setFilter(s)}
                    className={`px-2 py-1 rounded capitalize ${filter === s ? 'bg-indigo-100 text-indigo-700 font-semibold' : 'text-slate-600 hover:bg-slate-100'}`}
                  >
                    {s.replace('_', ' ')}
                  </button>
                ))}
              </div>

              {/* Ticket List */}
              <div className="flex-1 overflow-y-auto divide-y divide-slate-100">
                {tickets.length === 0 ? (
                  <div className="p-8 text-center text-slate-400 text-sm">No tickets found</div>
                ) : (
                  tickets.map((t) => (
                    <div 
                      key={t.ticket_id}
                      onClick={() => fetchTicketDetail(t.ticket_id)}
                      className={`p-4 cursor-pointer hover:bg-slate-50 transition ${selectedTicket?.ticket_id === t.ticket_id ? 'bg-indigo-50/50 border-l-4 border-indigo-600' : ''}`}
                    >
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-xs font-mono font-semibold text-slate-700">{t.ticket_id}</span>
                        {getStatusBadge(t.status)}
                      </div>
                      <p className="text-sm font-medium text-slate-800 line-clamp-2">{t.text}</p>
                      <div className="flex items-center space-x-2 mt-2 text-xs text-slate-400">
                        <span>{t.category || 'unclassified'}</span>
                        <span>•</span>
                        <span>{t.customer_id || 'guest'}</span>
                        <span>•</span>
                        <span>Conf: {(t.confidence * 100).toFixed(0)}%</span>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>

            {/* Right Column: Ticket Detail & Trace */}
            <div className="flex-1 bg-slate-50 p-6 overflow-y-auto">
              {!selectedTicket ? (
                <div className="h-full flex flex-col items-center justify-center text-slate-400">
                  <FileText className="w-12 h-12 mb-3 text-slate-300" />
                  <p className="text-sm">Select a ticket from the queue to inspect agent workflow trace</p>
                </div>
              ) : (
                <div className="max-w-3xl mx-auto space-y-6">
                  {/* Header Card */}
                  <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="flex items-center space-x-2">
                          <h2 className="text-lg font-bold text-slate-900">{selectedTicket.ticket_id}</h2>
                          {getStatusBadge(selectedTicket.status)}
                        </div>
                        <p className="text-xs text-slate-500 mt-1">Customer: {selectedTicket.customer_id || 'Anonymous'}</p>
                      </div>
                      <div className="text-right">
                        <span className="text-xs text-slate-400 uppercase font-semibold">Triage Category</span>
                        <p className="text-sm font-bold text-slate-700 capitalize">{selectedTicket.category || 'General'}</p>
                      </div>
                    </div>

                    <div className="mt-4 p-3 bg-slate-50 rounded-lg border border-slate-100 text-sm text-slate-800">
                      <span className="text-xs font-semibold text-slate-400 block mb-1">Inquiry:</span>
                      "{selectedTicket.text}"
                    </div>
                  </div>

                  {/* Draft & Human Approval Card */}
                  <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
                    <div className="flex items-center justify-between mb-3">
                      <h3 className="text-sm font-bold text-slate-800 flex items-center">
                        <Send className="w-4 h-4 mr-2 text-indigo-600" /> Grounded Agent Draft
                      </h3>
                      {!isEditing ? (
                        <button 
                          onClick={() => setIsEditing(true)} 
                          className="text-xs text-indigo-600 hover:text-indigo-800 font-medium flex items-center"
                        >
                          <Edit3 className="w-3.5 h-3.5 mr-1" /> Edit Draft
                        </button>
                      ) : (
                        <button 
                          onClick={() => setIsEditing(false)} 
                          className="text-xs text-slate-500 hover:text-slate-700"
                        >
                          Cancel Edit
                        </button>
                      )}
                    </div>

                    {isEditing ? (
                      <textarea 
                        value={editedDraft}
                        onChange={(e) => setEditedDraft(e.target.value)}
                        className="w-full h-32 p-3 text-sm border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
                      />
                    ) : (
                      <div className="p-4 bg-indigo-50/40 rounded-lg border border-indigo-100 text-sm text-slate-800 whitespace-pre-line">
                        {selectedTicket.draft_response || 'No draft generated.'}
                      </div>
                    )}

                    {/* Citations */}
                    {selectedTicket.citations && selectedTicket.citations.length > 0 && (
                      <div className="mt-3 flex items-center space-x-2">
                        <span className="text-xs font-semibold text-slate-500">Citations:</span>
                        {selectedTicket.citations.map((c) => (
                          <span key={c} className="text-xs px-2 py-0.5 bg-slate-100 text-slate-700 rounded border border-slate-200 font-mono">
                            {c}
                          </span>
                        ))}
                      </div>
                    )}

                    {/* Approval Controls */}
                    {selectedTicket.status === 'awaiting_approval' && (
                      <div className="mt-6 pt-4 border-t border-slate-100 flex items-center justify-end space-x-3">
                        <button 
                          onClick={() => handleAction(false)}
                          className="px-4 py-2 border border-red-300 text-red-700 hover:bg-red-50 text-xs font-semibold rounded-lg flex items-center"
                        >
                          <X className="w-4 h-4 mr-1.5" /> Reject & Escalate
                        </button>
                        <button 
                          onClick={() => handleAction(true)}
                          className="px-5 py-2 bg-green-600 hover:bg-green-700 text-white text-xs font-semibold rounded-lg flex items-center shadow-sm"
                        >
                          <Check className="w-4 h-4 mr-1.5" /> Approve & Dispatch Email
                        </button>
                      </div>
                    )}
                  </div>

                  {/* Workflow Trace & Tool Execution */}
                  <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
                    <h3 className="text-sm font-bold text-slate-800 mb-4 flex items-center">
                      <Clock className="w-4 h-4 mr-2 text-slate-600" /> Execution Trace & Tool Calls
                    </h3>
                    <div className="space-y-4">
                      {selectedTicket.trace_steps?.map((step, idx) => (
                        <div key={idx} className="flex items-start space-x-3 text-xs">
                          <div className="w-2 h-2 mt-1.5 rounded-full bg-indigo-600 flex-shrink-0" />
                          <div className="flex-1">
                            <span className="font-semibold text-slate-700 uppercase tracking-wide">{step.step}</span>
                            <pre className="mt-1 p-2 bg-slate-50 rounded border border-slate-100 text-slate-600 overflow-x-auto font-mono text-[11px]">
                              {JSON.stringify(step.details, null, 2)}
                            </pre>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </div>
          </>
        )}
      </div>
    </div>
  );
}
