/**
 * Dispute Resolution Page
 * 
 * Allows contributors to dispute bounty rejections and submit evidence.
 * Admins can review and resolve disputes.
 * 
 * Issue #192: Dispute Resolution System
 */

import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';

const API_BASE = import.meta.env.VITE_API_URL ?? '';

interface EvidenceItem {
  type: string;
  url?: string;
  description: string;
}

interface DisputeHistory {
  id: string;
  action: string;
  previous_status?: string;
  new_status?: string;
  actor_id: string;
  notes?: string;
  created_at: string;
}

interface Dispute {
  id: string;
  bounty_id: string;
  submitter_id: string;
  reason: string;
  description: string;
  evidence_links: EvidenceItem[];
  status: string;
  outcome?: string;
  reviewer_id?: string;
  review_notes?: string;
  resolution_action?: string;
  created_at: string;
  updated_at: string;
  resolved_at?: string;
  history?: DisputeHistory[];
}

const STATUS_COLORS: Record<string, string> = {
  pending: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30',
  under_review: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
  resolved: 'bg-green-500/20 text-green-400 border-green-500/30',
  closed: 'bg-gray-500/20 text-gray-400 border-gray-500/30',
};

const OUTCOME_COLORS: Record<string, string> = {
  approved: 'text-green-400',
  rejected: 'text-red-400',
  cancelled: 'text-gray-400',
};

const REASON_LABELS: Record<string, string> = {
  incorrect_review: 'Incorrect Review',
  plagiarism: 'Plagiarism',
  rule_violation: 'Rule Violation',
  technical_issue: 'Technical Issue',
  unfair_competition: 'Unfair Competition',
  other: 'Other',
};

export default function DisputeResolutionPage() {
  const { id } = useParams<{ id?: string }>();
  const navigate = useNavigate();
  
  const [dispute, setDispute] = useState<Dispute | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Form state for creating new dispute
  const [bountyId, setBountyId] = useState('');
  const [reason, setReason] = useState('incorrect_review');
  const [description, setDescription] = useState('');
  const [evidenceUrl, setEvidenceUrl] = useState('');
  const [evidenceDesc, setEvidenceDesc] = useState('');
  const [evidenceList, setEvidenceList] = useState<EvidenceItem[]>([]);
  
  // Form state for resolution
  const [outcome, setOutcome] = useState('approved');
  const [reviewNotes, setReviewNotes] = useState('');
  const [resolutionAction, setResolutionAction] = useState('');

  // Fetch dispute if viewing specific one
  useEffect(() => {
    if (!id) {
      setLoading(false);
      return;
    }
    
    let cancelled = false;
    (async () => {
      try {
        const res = await fetch(`${API_BASE}/api/disputes/${id}`);
        if (!cancelled && res.ok) {
          setDispute(await res.json());
        } else if (!cancelled) {
          setError(`Dispute #${id} not found`);
        }
      } catch {
        if (!cancelled) setError('Failed to load dispute');
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => { cancelled = true; };
  }, [id]);

  const addEvidence = () => {
    if (!evidenceDesc.trim()) return;
    setEvidenceList([
      ...evidenceList,
      { type: 'link', url: evidenceUrl, description: evidenceDesc }
    ]);
    setEvidenceUrl('');
    setEvidenceDesc('');
  };

  const createDispute = async () => {
    if (!bountyId.trim() || !description.trim()) return;
    
    try {
      const res = await fetch(`${API_BASE}/api/disputes`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          bounty_id: bountyId,
          reason,
          description,
          evidence_links: evidenceList,
        }),
      });
      
      if (res.ok) {
        const newDispute = await res.json();
        navigate(`/disputes/${newDispute.id}`);
      } else {
        const err = await res.json();
        setError(err.detail || 'Failed to create dispute');
      }
    } catch {
      setError('Failed to create dispute');
    }
  };

  const submitEvidence = async () => {
    if (!dispute || !evidenceDesc.trim()) return;
    
    try {
      const res = await fetch(`${API_BASE}/api/disputes/${dispute.id}/evidence`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          evidence_links: [{ type: 'link', url: evidenceUrl, description: evidenceDesc }],
        }),
      });
      
      if (res.ok) {
        const updated = await res.json();
        setDispute(updated);
        setEvidenceUrl('');
        setEvidenceDesc('');
      }
    } catch {
      setError('Failed to submit evidence');
    }
  };

  const resolveDispute = async () => {
    if (!dispute || !reviewNotes.trim()) return;
    
    try {
      const res = await fetch(`${API_BASE}/api/disputes/${dispute.id}/resolve`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          outcome,
          review_notes: reviewNotes,
          resolution_action: resolutionAction || undefined,
        }),
      });
      
      if (res.ok) {
        const updated = await res.json();
        setDispute(updated);
      }
    } catch {
      setError('Failed to resolve dispute');
    }
  };

  const triggerAiMediation = async () => {
    if (!dispute) return;
    
    try {
      const res = await fetch(`${API_BASE}/api/disputes/${dispute.id}/ai-mediate`, {
        method: 'POST',
      });
      
      if (res.ok) {
        const updated = await res.json();
        setDispute(updated);
      }
    } catch {
      setError('AI mediation failed');
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="w-8 h-8 border-2 border-[#9945FF] border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  // Create new dispute view
  if (!id) {
    return (
      <div className="max-w-2xl mx-auto p-6">
        <h1 className="text-2xl font-bold text-white mb-6">Initiate Dispute</h1>
        
        {error && (
          <div className="mb-4 p-4 rounded-lg bg-red-500/20 text-red-400 border border-red-500/30">
            {error}
          </div>
        )}
        
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Bounty ID *
            </label>
            <input
              type="text"
              value={bountyId}
              onChange={(e) => setBountyId(e.target.value)}
              className="w-full px-4 py-2 rounded-lg bg-gray-800 border border-gray-700 text-white placeholder-gray-500 focus:border-[#9945FF] focus:outline-none"
              placeholder="Enter bounty ID"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Reason *
            </label>
            <select
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              className="w-full px-4 py-2 rounded-lg bg-gray-800 border border-gray-700 text-white focus:border-[#9945FF] focus:outline-none"
            >
              {Object.entries(REASON_LABELS).map(([value, label]) => (
                <option key={value} value={value}>{label}</option>
              ))}
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Description * (min 10 chars)
            </label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="w-full px-4 py-3 rounded-lg bg-gray-800 border border-gray-700 text-white placeholder-gray-500 focus:border-[#9945FF] focus:outline-none min-h-[120px]"
              placeholder="Explain why you believe the rejection was incorrect..."
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Evidence (optional)
            </label>
            <div className="space-y-2">
              <input
                type="text"
                value={evidenceUrl}
                onChange={(e) => setEvidenceUrl(e.target.value)}
                className="w-full px-4 py-2 rounded-lg bg-gray-800 border border-gray-700 text-white placeholder-gray-500 focus:border-[#9945FF] focus:outline-none"
                placeholder="Evidence URL (e.g., PR link, screenshot)"
              />
              <input
                type="text"
                value={evidenceDesc}
                onChange={(e) => setEvidenceDesc(e.target.value)}
                className="w-full px-4 py-2 rounded-lg bg-gray-800 border border-gray-700 text-white placeholder-gray-500 focus:border-[#9945FF] focus:outline-none"
                placeholder="Evidence description"
              />
              <button
                onClick={addEvidence}
                disabled={!evidenceDesc.trim()}
                className="px-4 py-2 rounded-lg bg-gray-700 text-gray-300 hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                + Add Evidence
              </button>
            </div>
            
            {evidenceList.length > 0 && (
              <div className="mt-3 space-y-2">
                {evidenceList.map((e, i) => (
                  <div key={i} className="p-3 rounded-lg bg-gray-800/50 border border-gray-700">
                    {e.url && (
                      <a href={e.url} target="_blank" rel="noopener noreferrer" className="text-[#14F195] hover:underline text-sm">
                        {e.url}
                      </a>
                    )}
                    <p className="text-gray-300 text-sm mt-1">{e.description}</p>
                  </div>
                ))}
              </div>
            )}
          </div>
          
          <button
            onClick={createDispute}
            disabled={!bountyId.trim() || description.length < 10}
            className="w-full py-3 rounded-lg bg-[#9945FF] text-white font-medium hover:bg-[#9945FF]/80 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            Submit Dispute
          </button>
        </div>
      </div>
    );
  }

  // View specific dispute
  if (error || !dispute) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] gap-4">
        <p className="text-gray-400 font-mono">{error ?? 'Dispute not found'}</p>
        <button
          onClick={() => navigate('/disputes')}
          className="px-4 py-2 rounded-lg bg-[#9945FF]/20 text-[#9945FF] hover:bg-[#9945FF]/30 transition-colors"
        >
          ← Back to Disputes
        </button>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-white">Dispute #{dispute.id.slice(0, 8)}</h1>
          <p className="text-gray-400 text-sm mt-1">Bounty: {dispute.bounty_id}</p>
        </div>
        <span className={`px-3 py-1 rounded-full text-sm font-medium border ${STATUS_COLORS[dispute.status] || 'bg-gray-500/20 text-gray-400'}`}>
          {dispute.status.replace('_', ' ').toUpperCase()}
        </span>
      </div>
      
      {error && (
        <div className="mb-4 p-4 rounded-lg bg-red-500/20 text-red-400 border border-red-500/30">
          {error}
        </div>
      )}
      
      {/* Main info */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
        <div className="p-4 rounded-lg bg-gray-800/50 border border-gray-700">
          <h2 className="text-lg font-semibold text-white mb-3">Details</h2>
          <div className="space-y-2 text-sm">
            <div>
              <span className="text-gray-400">Reason:</span>
              <span className="text-white ml-2">{REASON_LABELS[dispute.reason] || dispute.reason}</span>
            </div>
            <div>
              <span className="text-gray-400">Created:</span>
              <span className="text-white ml-2">{new Date(dispute.created_at).toLocaleString()}</span>
            </div>
            {dispute.resolved_at && (
              <div>
                <span className="text-gray-400">Resolved:</span>
                <span className="text-white ml-2">{new Date(dispute.resolved_at).toLocaleString()}</span>
              </div>
            )}
            {dispute.outcome && (
              <div>
                <span className="text-gray-400">Outcome:</span>
                <span className={`ml-2 font-medium ${OUTCOME_COLORS[dispute.outcome]}`}>
                  {dispute.outcome.toUpperCase()}
                </span>
              </div>
            )}
          </div>
        </div>
        
        <div className="p-4 rounded-lg bg-gray-800/50 border border-gray-700">
          <h2 className="text-lg font-semibold text-white mb-3">Description</h2>
          <p className="text-gray-300 text-sm whitespace-pre-wrap">{dispute.description}</p>
        </div>
      </div>
      
      {/* Evidence */}
      <div className="mb-6 p-4 rounded-lg bg-gray-800/50 border border-gray-700">
        <h2 className="text-lg font-semibold text-white mb-3">Evidence ({dispute.evidence_links?.length || 0})</h2>
        {dispute.evidence_links?.length > 0 ? (
          <div className="space-y-2">
            {dispute.evidence_links.map((e, i) => (
              <div key={i} className="p-3 rounded-lg bg-gray-900/50 border border-gray-700">
                {e.url && (
                  <a href={e.url} target="_blank" rel="noopener noreferrer" className="text-[#14F195] hover:underline text-sm">
                    {e.url}
                  </a>
                )}
                <p className="text-gray-300 text-sm mt-1">{e.description}</p>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-gray-500 text-sm">No evidence submitted yet.</p>
        )}
      </div>
      
      {/* Submit additional evidence */}
      {dispute.status !== 'resolved' && (
        <div className="mb-6 p-4 rounded-lg bg-gray-800/50 border border-gray-700">
          <h2 className="text-lg font-semibold text-white mb-3">Submit Additional Evidence</h2>
          <div className="space-y-2">
            <input
              type="text"
              value={evidenceUrl}
              onChange={(e) => setEvidenceUrl(e.target.value)}
              className="w-full px-4 py-2 rounded-lg bg-gray-800 border border-gray-700 text-white placeholder-gray-500 focus:border-[#9945FF] focus:outline-none"
              placeholder="Evidence URL (optional)"
            />
            <input
              type="text"
              value={evidenceDesc}
              onChange={(e) => setEvidenceDesc(e.target.value)}
              className="w-full px-4 py-2 rounded-lg bg-gray-800 border border-gray-700 text-white placeholder-gray-500 focus:border-[#9945FF] focus:outline-none"
              placeholder="Evidence description"
            />
            <button
              onClick={submitEvidence}
              disabled={!evidenceDesc.trim()}
              className="px-4 py-2 rounded-lg bg-gray-700 text-gray-300 hover:bg-gray-600 disabled:opacity-50"
            >
              Submit Evidence
            </button>
          </div>
        </div>
      )}
      
      {/* AI Mediation */}
      {dispute.status !== 'resolved' && (
        <div className="mb-6 p-4 rounded-lg bg-gray-800/50 border border-gray-700">
          <h2 className="text-lg font-semibold text-white mb-3">AI Mediation</h2>
          <p className="text-gray-400 text-sm mb-3">
            If AI score ≥ 7/10, dispute auto-resolves in contributor's favor.
          </p>
          <button
            onClick={triggerAiMediation}
            className="px-4 py-2 rounded-lg bg-[#14F195]/20 text-[#14F195] hover:bg-[#14F195]/30"
          >
            Run AI Mediation
          </button>
        </div>
      )}
      
      {/* Admin Resolution */}
      {dispute.status !== 'resolved' && (
        <div className="mb-6 p-4 rounded-lg bg-gray-800/50 border border-yellow-500/30">
          <h2 className="text-lg font-semibold text-white mb-3">Admin Resolution</h2>
          <div className="space-y-3">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Outcome</label>
              <select
                value={outcome}
                onChange={(e) => setOutcome(e.target.value)}
                className="w-full px-4 py-2 rounded-lg bg-gray-800 border border-gray-700 text-white"
              >
                <option value="approved">Approved (Contributor wins)</option>
                <option value="rejected">Rejected (Creator's decision stands)</option>
                <option value="cancelled">Cancelled</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Review Notes *</label>
              <textarea
                value={reviewNotes}
                onChange={(e) => setReviewNotes(e.target.value)}
                className="w-full px-4 py-3 rounded-lg bg-gray-800 border border-gray-700 text-white min-h-[80px]"
                placeholder="Explain the decision..."
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Resolution Action (optional)</label>
              <input
                type="text"
                value={resolutionAction}
                onChange={(e) => setResolutionAction(e.target.value)}
                className="w-full px-4 py-2 rounded-lg bg-gray-800 border border-gray-700 text-white"
                placeholder="e.g., Payout released, reputation updated"
              />
            </div>
            <button
              onClick={resolveDispute}
              disabled={!reviewNotes.trim()}
              className="px-4 py-2 rounded-lg bg-[#9945FF] text-white hover:bg-[#9945FF]/80 disabled:opacity-50"
            >
              Resolve Dispute
            </button>
          </div>
        </div>
      )}
      
      {/* Resolution Result */}
      {dispute.status === 'resolved' && dispute.review_notes && (
        <div className="mb-6 p-4 rounded-lg bg-gray-800/50 border border-green-500/30">
          <h2 className="text-lg font-semibold text-white mb-3">Resolution</h2>
          <p className="text-gray-300 text-sm mb-2">{dispute.review_notes}</p>
          {dispute.resolution_action && (
            <p className="text-gray-400 text-sm">Action: {dispute.resolution_action}</p>
          )}
        </div>
      )}
      
      {/* History */}
      {dispute.history && dispute.history.length > 0 && (
        <div className="p-4 rounded-lg bg-gray-800/50 border border-gray-700">
          <h2 className="text-lg font-semibold text-white mb-3">History</h2>
          <div className="space-y-2">
            {dispute.history.map((h) => (
              <div key={h.id} className="p-3 rounded-lg bg-gray-900/50 border border-gray-700">
                <div className="flex justify-between text-sm">
                  <span className="text-[#9945FF]">{h.action.replace(/_/g, ' ')}</span>
                  <span className="text-gray-500">{new Date(h.created_at).toLocaleString()}</span>
                </div>
                {h.notes && <p className="text-gray-400 text-sm mt-1">{h.notes}</p>}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}