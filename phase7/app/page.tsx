"use client";

import { useState, useEffect, useRef } from 'react';
import {
  MessageSquare, BarChart2, ChevronLeft, ChevronRight,
  ExternalLink, Send, Wifi, WifiOff, RefreshCw, ShieldAlert, TrendingUp
} from 'lucide-react';

// ── Types ──────────────────────────────────────────────────────────────────
type Message = {
  role: 'user' | 'assistant';
  content: string;
  sources?: string[];
  isBlocked?: boolean;  // PII or advice refusal
};

type Fund = {
  name: string;
  url: string;
  category: string;
  risk: string;
};

// ── Static fund data ────────────────────────────────────────────────────────
const FUNDS: Fund[] = [
  { name: 'Groww Multicap Fund', url: 'https://groww.in/mutual-funds/groww-multicap-fund-direct-growth', category: 'Equity', risk: 'Very High' },
  { name: 'Groww Liquid Fund', url: 'https://groww.in/mutual-funds/groww-liquid-fund-direct-growth', category: 'Debt', risk: 'Low to Moderate' },
  { name: 'Groww Nifty EV & New Age Automotive ETF FoF Direct-Growth', url: 'https://groww.in/mutual-funds/groww-nifty-ev-new-age-automotive-etf-fof-direct-growth', category: 'Equity', risk: 'Very High' },
  { name: 'Groww Large Cap Fund', url: 'https://groww.in/mutual-funds/groww-large-cap-fund-direct-growth', category: 'Equity', risk: 'Very High' },
  { name: 'Groww Overnight Fund', url: 'https://groww.in/mutual-funds/groww-overnight-fund-direct-growth', category: 'Debt', risk: 'Low' },
];

// Fund display name helper (strip "Direct Growth/Direct-Growth")
const shortName = (name: string) => name.replace(/ Direct-Growth| Direct Growth/g, '');

// Key for chat history — "all" or fund name
const historyKey = (fund: Fund | null) => fund ? fund.name : '__all__';

// ── Main Component ──────────────────────────────────────────────────────────
export default function Home() {
  const [query, setQuery] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<'Chat' | 'Fund Info'>('Chat');
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [selectedFund, setSelectedFund] = useState<Fund | null>(null);
  const [lastRefreshed, setLastRefreshed] = useState<string>('');
  const [backendOnline, setBackendOnline] = useState<boolean | null>(null);

  // ── Per-fund chat history ─────────────────────────────────────────────
  // Record keyed by fund name (or '__all__' for "All Funds")
  const [chatHistories, setChatHistories] = useState<Record<string, Message[]>>({});

  const currentMessages: Message[] = chatHistories[historyKey(selectedFund)] ?? [];

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // ── Backend status on mount ────────────────────────────────────────────
  useEffect(() => {
    fetch('/api/status')
      .then(r => r.json())
      .then(d => {
        setBackendOnline(d.status !== 'offline');
        setLastRefreshed(d.last_refreshed || '');
      })
      .catch(() => setBackendOnline(false));
  }, []);

  // ── Auto-scroll on new messages ────────────────────────────────────────
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [currentMessages, isLoading]);

  // ── Focus input when fund changes ──────────────────────────────────────
  useEffect(() => {
    inputRef.current?.focus();
  }, [selectedFund]);

  // ── Append message to current fund's history ───────────────────────────
  const appendMessage = (fund: Fund | null, msg: Message) => {
    const key = historyKey(fund);
    setChatHistories(prev => ({
      ...prev,
      [key]: [...(prev[key] ?? []), msg],
    }));
  };

  // ── Send message ───────────────────────────────────────────────────────
  const handleSubmit = async (e?: React.FormEvent, overrideQuery?: string) => {
    if (e) e.preventDefault();
    const text = (overrideQuery ?? query).trim();
    if (!text || isLoading) return;

    const activeFund = selectedFund; // capture at submission time
    appendMessage(activeFund, { role: 'user', content: text });
    setQuery('');
    setIsLoading(true);
    setActiveTab('Chat');

    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: text,
          selected_fund: activeFund ? activeFund.name : null,
        }),
      });
      const data = await res.json();
      const isBlocked = data.status === 'blocked';
      const content = data.answer || data.error || 'Something went wrong.';
      const sources: string[] = data.sources || [];
      if (data.last_refreshed) setLastRefreshed(data.last_refreshed);
      appendMessage(activeFund, { role: 'assistant', content, sources, isBlocked });
    } catch {
      appendMessage(activeFund, { role: 'assistant', content: 'Failed to connect to the server.', isBlocked: false });
    } finally {
      setIsLoading(false);
    }
  };

  // ── Context-aware empty state content ─────────────────────────────────
  const emptyStateContent = selectedFund === null ? {
    icon: (
      <svg viewBox="0 0 120 120" className="w-10 h-10 shadow-sm" style={{ borderRadius: '50%' }}>
        <rect width="120" height="120" fill="#00D09C" />
        <path d="M0,70 L35,45 L65,75 L120,30 L120,0 L0,0 Z" fill="#5367FF" />
      </svg>
    ),
    iconBg: 'bg-slate-900 border-slate-800',
    tag: 'Groww AMC Overview',
    tagColor: 'bg-[#5367FF]/15 text-[#5367FF] border-[#5367FF]/30',
    headline: 'Ask facts about Groww Mutual Fund AMC',
    subtext: 'You\'re in general mode. Ask about the AMC at large — its AUM, number of schemes, investement approach, CEO, or how to invest with Groww.',
    chips: [
      'What is the total AUM of Groww AMC?',
      'Who is the CEO of Groww Mutual Fund?',
      'How many schemes does Groww AMC offer?',
      'How can I invest in Groww Mutual Fund?',
    ],
  } : {
    icon: <MessageSquare className="w-9 h-9 text-[#00D09C]" />,
    iconBg: 'bg-[#00D09C]/10 border-[#00D09C]/20',
    tag: shortName(selectedFund.name),
    tagColor: 'bg-[#00D09C]/15 text-[#00D09C] border-[#00D09C]/30',
    headline: `Enquire about ${shortName(selectedFund.name)}`,
    subtext: `You're now in fund-specific mode. Ask about the specifics of ${shortName(selectedFund.name)} — expense ratio, NAV, SIP minimum, exit load, top holdings, fund managers, or risk level.`,
    chips: [
      `What is the expense ratio of ${shortName(selectedFund.name)}?`,
      `Who manages ${shortName(selectedFund.name)}?`,
      `What is the exit load for ${shortName(selectedFund.name)}?`,
      `What are the top holdings of ${shortName(selectedFund.name)}?`,
    ],
  };

  return (
    <main className="flex flex-col h-screen w-full bg-slate-950 text-slate-100 overflow-hidden"
      style={{ fontFamily: "'Inter', system-ui, sans-serif" }}>

      {/* ── 1. Top Navbar ── */}
      <nav className="bg-slate-900 border-b border-slate-800 px-5 py-3 flex items-center justify-between shrink-0 z-20 shadow-md">
        <div className="flex items-center gap-4">
          {/* Custom Groww SVG Logo */}
          <div className="w-10 h-10 shrink-0 flex items-center justify-center">
            <svg viewBox="0 0 120 120" className="w-full h-full shadow-lg" style={{ borderRadius: '50%' }}>
              <rect width="120" height="120" fill="#00D09C" />
              <path d="M0,70 L35,45 L65,75 L120,30 L120,0 L0,0 Z" fill="#5367FF" />
            </svg>
          </div>
          <div className="flex flex-col leading-tight">
            <span className="font-bold text-[17px] text-slate-100 tracking-tight">Groww PureFact</span>
            <span className="text-[12px] text-slate-400 font-medium mt-0.5">Unbiased. Unopinionated. Purely factual fund insights.</span>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <div className={`flex items-center gap-2 border rounded-full px-3 py-1.5 text-[11px] font-bold shadow-sm transition-all ${backendOnline === null ? 'border-slate-700 text-slate-500 bg-slate-800/50' :
            backendOnline ? 'border-emerald-500/30 text-emerald-400 bg-emerald-900/20' :
              'border-red-500/30 text-red-400 bg-red-900/20'
            }`}>
            {backendOnline === null ? <RefreshCw className="w-3 h-3 animate-spin" /> :
              backendOnline ? <Wifi className="w-3 h-3" /> :
                <WifiOff className="w-3 h-3" />}
            {backendOnline === null ? 'Checking...' : backendOnline ? 'Backend Online' : 'Backend Offline'}
          </div>
        </div>
      </nav>

      {/* ── Sub-nav tabs ── */}
      <div className="bg-slate-900 border-b border-slate-800 px-5 flex shrink-0 z-10">
        {(['Chat', 'Fund Info'] as const).map(tab => (
          <button key={tab} onClick={() => setActiveTab(tab)}
            className={`flex items-center gap-2 px-5 py-3 text-sm font-semibold border-b-2 transition-all ${activeTab === tab
              ? 'border-indigo-500 text-indigo-400'
              : 'border-transparent text-slate-500 hover:text-slate-300 hover:border-slate-600'
              }`}>
            {tab === 'Chat' && <MessageSquare className="w-4 h-4" />}
            {tab === 'Fund Info' && <BarChart2 className="w-4 h-4" />}
            {tab}
          </button>
        ))}
      </div>

      {/* ── Body ── */}
      <div className="flex flex-1 overflow-hidden">

        {/* ── 2. Collapsible Left Sidebar ── */}
        <aside className={`flex flex-col bg-slate-900 border-r border-slate-800 shrink-0 transition-all duration-300 overflow-hidden ${sidebarOpen ? 'w-64' : 'w-12'}`}>
          {/* Header row with toggle */}
          <button onClick={() => setSidebarOpen(p => !p)}
            className="flex items-center justify-between px-3 py-3 border-b border-slate-800 hover:bg-slate-800/50 transition-colors text-slate-400 hover:text-slate-200 shrink-0">
            {sidebarOpen && <span className="text-[10px] font-bold uppercase tracking-widest text-slate-500">Fund Context</span>}
            {sidebarOpen ? <ChevronLeft className="w-4 h-4 ml-auto" /> : <ChevronRight className="w-4 h-4 mx-auto" />}
          </button>

          {sidebarOpen && (
            <div className="flex-1 overflow-y-auto custom-scrollbar p-3 space-y-1">
              {/* All Funds */}
              <button onClick={() => setSelectedFund(null)}
                className={`w-full text-left px-3 py-2.5 rounded-lg text-sm font-semibold transition-all flex items-center gap-2.5 ${selectedFund === null
                  ? 'bg-indigo-500/15 text-indigo-300 border border-indigo-500/20'
                  : 'text-slate-400 hover:bg-slate-800 hover:text-slate-200 border border-transparent'
                  }`}>
                <span className="w-5 h-5 rounded-full bg-slate-700 text-[10px] flex items-center justify-center font-bold shrink-0 text-slate-300">A</span>
                <span className="truncate">All Funds (AMC)</span>
              </button>

              <div className="border-t border-slate-800 my-2" />

              {/* Individual funds */}
              {FUNDS.map((fund, idx) => (
                <div key={idx}>
                  <button onClick={() => setSelectedFund(fund)}
                    className={`w-full text-left px-3 py-2.5 rounded-lg text-sm font-medium transition-all flex items-center gap-2.5 ${selectedFund?.name === fund.name
                      ? 'bg-emerald-500/15 text-emerald-300 border border-emerald-500/20'
                      : 'text-slate-400 hover:bg-slate-800 hover:text-slate-200 border border-transparent'
                      }`}>
                    <span className={`w-2 h-2 rounded-full shrink-0 ${fund.category === 'Equity' ? 'bg-blue-400' : 'bg-amber-400'}`} />
                    <span className="truncate leading-tight">{shortName(fund.name)}</span>
                  </button>

                  {/* View on Groww inline link when fund is active */}
                  {selectedFund?.name === fund.name && (
                    <a href={fund.url} target="_blank" rel="noopener noreferrer"
                      className="ml-3 mt-1 mb-1 flex items-center gap-1.5 text-[11px] font-bold text-emerald-500 hover:text-emerald-300 hover:underline transition-colors">
                      <ExternalLink className="w-3 h-3 shrink-0" /> View on Groww
                    </a>
                  )}
                </div>
              ))}
            </div>
          )}
        </aside>

        {/* ── 3. Main Content ── */}
        <div className="flex-1 flex flex-col min-w-0">

          {/* ── CHAT TAB ── */}
          {activeTab === 'Chat' && (
            <>
              {/* Sub-header: context bar */}
              <div className="border-b border-slate-800 px-5 py-3 bg-slate-900/40 shrink-0 flex flex-wrap items-center gap-2">
                <span className="text-sm font-bold text-slate-300">Groww PureFact</span>
                <span className="text-slate-700">·</span>
                <span className={`px-2.5 py-0.5 rounded-full text-[11px] font-bold border ${selectedFund === null ? 'bg-indigo-500/10 text-indigo-400 border-indigo-500/20' : 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                  }`}>
                  {selectedFund === null ? 'Groww AMC' : shortName(selectedFund.name)}
                </span>
                {lastRefreshed && (
                  <span className="bg-slate-800 text-slate-400 border border-slate-700 px-3 py-1 rounded-full text-[11px] font-medium flex items-center gap-1.5">
                    <RefreshCw className="w-3 h-3 text-slate-500" /> Data last updated on {lastRefreshed}
                  </span>
                )}
              </div>

              {/* Messages area */}
              <div className="flex-1 overflow-y-auto custom-scrollbar px-4 py-6 space-y-5 bg-slate-950">
                {currentMessages.length === 0 ? (
                  /* ── Context-aware Empty State ── */
                  <div className="flex flex-col items-center justify-center h-full text-center py-16 px-4 animate-in fade-in duration-500">
                    <div className={`w-16 h-16 border rounded-2xl flex items-center justify-center mb-5 ${emptyStateContent.iconBg}`}>
                      {emptyStateContent.icon}
                    </div>
                    <span className={`text-[11px] font-bold uppercase tracking-widest border rounded-full px-3 py-1 mb-4 ${emptyStateContent.tagColor}`}>
                      {emptyStateContent.tag}
                    </span>
                    <h2 className="text-xl font-bold text-slate-200 mb-3 max-w-sm">{emptyStateContent.headline}</h2>
                    <p className="max-w-md text-slate-500 text-sm leading-relaxed mb-8">{emptyStateContent.subtext}</p>

                    {/* Suggestion chips */}
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5 max-w-xl w-full">
                      {emptyStateContent.chips.map((chip, i) => (
                        <button key={i} onClick={() => handleSubmit(undefined, chip)}
                          className={`border hover:bg-slate-800 text-slate-400 hover:text-slate-200 text-[13px] font-medium px-4 py-3 rounded-xl text-left transition-all leading-snug ${selectedFund === null ? 'bg-slate-900 border-[#5367FF]/20 hover:border-[#5367FF]/50' : 'bg-slate-900 border-[#00D09C]/20 hover:border-[#00D09C]/50'
                            }`}>
                          {chip}
                        </button>
                      ))}
                    </div>
                  </div>
                ) : (
                  <>
                    {currentMessages.map((msg, i) => (
                      <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'} animate-in fade-in slide-in-from-bottom-2 duration-300`}>
                        <div className={`max-w-[82%] flex flex-col gap-2.5 ${msg.role === 'user' ? 'items-end' : 'items-start'}`}>
                          {/* Message bubble */}
                          <div className={`px-5 py-3.5 rounded-2xl text-[14.5px] leading-relaxed ${msg.role === 'user'
                            ? 'bg-indigo-600 text-white rounded-tr-sm font-medium shadow-md'
                            : msg.isBlocked
                              ? 'bg-red-950/40 border border-red-800/40 text-red-300 rounded-tl-sm'
                              : 'bg-slate-900 border border-slate-800 text-slate-200 rounded-tl-sm shadow-sm'
                            }`}>
                            {msg.isBlocked && <ShieldAlert className="w-4 h-4 mb-2 text-red-400 inline mr-2" />}
                            {msg.content}
                          </div>

                          {/* Source citation box */}
                          {msg.role === 'assistant' && !msg.isBlocked && msg.sources && msg.sources.length > 0 && (
                            <div className="w-full bg-blue-950/30 border border-blue-800/30 rounded-xl px-4 py-3">
                              <p className="text-[10px] font-bold text-blue-500 uppercase tracking-wider mb-2">Sources</p>
                              {msg.sources.map((src, si) => (
                                <a key={si} href={src} target="_blank" rel="noopener noreferrer"
                                  className="flex items-center gap-2 text-[13px] text-blue-400 hover:text-blue-300 font-medium hover:underline truncate">
                                  <ExternalLink className="w-3 h-3 shrink-0" />{src}
                                </a>
                              ))}
                            </div>
                          )}
                        </div>
                      </div>
                    ))}

                    {/* Typing indicator */}
                    {isLoading && (
                      <div className="flex justify-start">
                        <div className="bg-slate-900 border border-slate-800 rounded-2xl rounded-tl-sm px-5 py-4 flex items-center gap-2">
                          <span className="w-2 h-2 bg-slate-500 rounded-full animate-bounce" />
                          <span className="w-2 h-2 bg-slate-500 rounded-full animate-bounce [animation-delay:0.15s]" />
                          <span className="w-2 h-2 bg-slate-500 rounded-full animate-bounce [animation-delay:0.3s]" />
                        </div>
                      </div>
                    )}
                    <div ref={messagesEndRef} />
                  </>
                )}
              </div>

              {/* ── Sticky input bar ── */}
              <div className="border-t border-slate-800 bg-slate-900 px-5 py-4 shrink-0">
                <form onSubmit={handleSubmit} className="flex gap-3 max-w-4xl mx-auto">
                  <input ref={inputRef} type="text" value={query}
                    onChange={e => setQuery(e.target.value)}
                    placeholder={selectedFund
                      ? `Ask a fact about ${shortName(selectedFund.name)}...`
                      : 'Ask about Groww AMC — AUM, schemes, CEO, how to invest...'}
                    disabled={isLoading} data-testid="chat-input"
                    className="flex-1 bg-slate-800 border border-slate-700 focus:border-indigo-500 focus:ring-0 focus:outline-none rounded-xl px-5 py-3.5 text-[14.5px] text-slate-200 placeholder-slate-500 font-medium disabled:opacity-50 transition-colors"
                  />
                  <button type="submit" disabled={isLoading || !query.trim()} data-testid="chat-submit"
                    className="bg-[#5367FF] hover:bg-[#4355eb] active:bg-[#3342cc] disabled:opacity-40 disabled:cursor-not-allowed text-white px-7 py-3.5 rounded-xl font-bold flex items-center gap-2 transition-all shadow-lg shadow-[#5367FF]/20 min-w-[110px] justify-center">
                    {isLoading ? 'Wait...' : <><Send className="w-4 h-4" /> Ask</>}
                  </button>
                </form>
              </div>
            </>
          )}

          {/* ── FUND INFO TAB ── */}
          {activeTab === 'Fund Info' && (
            <div className="flex-1 overflow-y-auto custom-scrollbar px-6 py-8 bg-slate-950">
              <div className="max-w-3xl mx-auto">
                <h1 className="text-2xl font-bold text-slate-100 mb-1">Covered Mutual Funds</h1>
                <p className="text-sm text-slate-500 mb-8">All fund data is sourced exclusively from Groww official pages.</p>
                <div className="space-y-4">
                  {FUNDS.map((fund, i) => (
                    <div key={i} className="bg-slate-900 border border-slate-800 rounded-xl p-5 flex flex-col sm:flex-row justify-between sm:items-center gap-4 hover:border-slate-700 transition-all">
                      <div>
                        <h3 className="font-bold text-slate-200 text-base mb-2">{fund.name}</h3>
                        <div className="flex gap-2 flex-wrap">
                          <span className={`text-[11px] font-bold px-2.5 py-1 rounded-full border ${fund.category === 'Equity' ? 'bg-blue-500/10 text-blue-400 border-blue-500/20' : 'bg-amber-500/10 text-amber-400 border-amber-500/20'
                            }`}>{fund.category}</span>
                          <span className="text-[11px] font-bold px-2.5 py-1 rounded-full border bg-slate-800 text-slate-400 border-slate-700">{fund.risk} Risk</span>
                        </div>
                      </div>
                      <a href={fund.url} target="_blank" rel="noopener noreferrer"
                        className="flex items-center gap-2 text-sm font-bold text-indigo-400 hover:text-indigo-300 shrink-0 group transition-colors">
                        View on Groww <ExternalLink className="w-4 h-4 group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition-transform" />
                      </a>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      <style jsx global>{`
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');
        .custom-scrollbar::-webkit-scrollbar { width: 5px; }
        .custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
        .custom-scrollbar::-webkit-scrollbar-thumb { background-color: #334155; border-radius: 10px; }
        .custom-scrollbar::-webkit-scrollbar-thumb:hover { background-color: #475569; }
        @keyframes fade-in { from { opacity: 0; } to { opacity: 1; } }
        .animate-in { animation-fill-mode: both; }
        .fade-in { animation-name: fade-in; }
        .duration-300 { animation-duration: 0.3s; }
        .duration-500 { animation-duration: 0.5s; }
        @keyframes slide-in-from-bottom-2 { from { transform: translateY(8px); opacity: 0; } to { transform: translateY(0); opacity: 1; } }
        .slide-in-from-bottom-2 { animation-name: slide-in-from-bottom-2; }
      `}</style>
    </main>
  );
}
