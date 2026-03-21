/**
 * NotFoundPage — 404 error page for SolFoundry
 * A friendly, dark-themed error page with Solana branding
 * @module NotFoundPage
 */
import { Link } from 'react-router-dom';

export default function NotFoundPage() {
  return (
    <div className="min-h-[80vh] flex items-center justify-center px-4">
      <div className="text-center max-w-md">
        {/* 404 Number with gradient */}
        <div className="relative">
          <h1 
            className="text-[120px] sm:text-[160px] font-bold leading-none select-none"
            style={{
              background: 'linear-gradient(135deg, #9945FF 0%, #14F195 100%)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              backgroundClip: 'text',
            }}
          >
            404
          </h1>
          {/* Decorative glow */}
          <div 
            className="absolute inset-0 blur-3xl opacity-20 -z-10"
            style={{
              background: 'linear-gradient(135deg, #9945FF 0%, #14F195 100%)',
            }}
          />
        </div>

        {/* Error message */}
        <h2 className="text-2xl sm:text-3xl font-bold text-white mt-4 mb-3">
          Page Not Found
        </h2>
        <p className="text-gray-400 text-sm sm:text-base mb-8 font-mono">
          Oops! The page you're looking for seems to have wandered off into the Solana void.
          <br className="hidden sm:block" />
          Let's get you back on track.
        </p>

        {/* Action buttons */}
        <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
          {/* Primary: Return to Bounties */}
          <Link
            to="/bounties"
            className="flex items-center gap-2 px-6 py-3 rounded-lg bg-gradient-to-r from-[#9945FF] to-[#14F195]
                     text-white font-medium hover:opacity-90 transition-opacity shadow-lg shadow-[#9945FF]/20"
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 12l8.954-8.955c.44-.439 1.152-.439 1.591 0L21.75 12M4.5 9.75v10.125c0 .621.504 1.125 1.125 1.125H9.75v-4.875c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125V21h4.125c.621 0 1.125-.504 1.125-1.125V9.75M8.25 21h8.25" />
            </svg>
            <span>Back to Home</span>
          </Link>

          {/* Secondary: Browse Bounties */}
          <Link
            to="/bounties"
            className="flex items-center gap-2 px-6 py-3 rounded-lg border border-[#9945FF]/30 text-[#9945FF]
                     font-medium hover:bg-[#9945FF]/10 transition-colors"
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
            </svg>
            <span>Browse Bounties</span>
          </Link>
        </div>

        {/* Helpful links */}
        <div className="mt-12 pt-8 border-t border-white/10">
          <p className="text-xs text-gray-500 mb-3">Looking for something specific?</p>
          <div className="flex flex-wrap items-center justify-center gap-4 text-sm">
            <Link to="/leaderboard" className="text-gray-400 hover:text-[#14F195] transition-colors">
              Leaderboard
            </Link>
            <span className="text-gray-600">•</span>
            <Link to="/agents" className="text-gray-400 hover:text-[#14F195] transition-colors">
              Agents
            </Link>
            <span className="text-gray-600">•</span>
            <a 
              href="https://github.com/SolFoundry/solfoundry#readme" 
              target="_blank" 
              rel="noopener noreferrer"
              className="text-gray-400 hover:text-[#14F195] transition-colors"
            >
              Docs
            </a>
          </div>
        </div>
      </div>
    </div>
  );
}