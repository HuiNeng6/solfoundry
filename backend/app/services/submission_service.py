"""Bounty submission service for handling PR submissions and auto-matching.

This service manages the complete submission workflow:
1. PR submission with automatic bounty matching
2. Status tracking through review process
3. Submission history and statistics
"""

import re
import logging
from typing import Optional, List, Tuple
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_

from app.models.submission import (
    SubmissionDB,
    SubmissionStatus,
    MatchConfidence,
    SubmissionCreate,
    SubmissionUpdate,
    SubmissionResponse,
    SubmissionListItem,
    SubmissionListResponse,
    SubmissionSearchParams,
    SubmissionStats,
    MatchResult,
)
from app.models.bounty import BountyDB, BountyStatus

logger = logging.getLogger(__name__)


class SubmissionService:
    """Service for managing bounty submissions."""
    
    PR_URL_PATTERN = re.compile(
        r'https?://github\.com/([^/]+)/([^/]+)/pull/(\d+)'
    )
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_submission(
        self,
        contributor_id: str,
        data: SubmissionCreate,
    ) -> Tuple[SubmissionDB, Optional[MatchResult]]:
        """Create a new submission with automatic bounty matching."""
        pr_info = self._parse_pr_url(data.pr_url)
        
        submission = SubmissionDB(
            contributor_id=contributor_id,
            contributor_wallet=data.contributor_wallet,
            pr_url=data.pr_url,
            pr_number=pr_info.get('pr_number'),
            pr_repo=pr_info.get('repo'),
            description=data.description,
            evidence=data.evidence,
            status=SubmissionStatus.PENDING.value,
        )
        
        if data.bounty_id:
            submission.bounty_id = data.bounty_id
            submission.match_confidence = MatchConfidence.HIGH.value
            submission.match_score = 1.0
            submission.match_reasons = ["Contributor specified bounty"]
            submission.status = SubmissionStatus.MATCHED.value
            
            bounty = await self._get_bounty(data.bounty_id)
            if bounty:
                submission.reward_amount = bounty.reward_amount
                submission.reward_token = bounty.reward_token
        else:
            match_result = await self._auto_match_bounty(submission)
            if match_result:
                submission.bounty_id = match_result.bounty_id
                submission.match_confidence = match_result.confidence
                submission.match_score = match_result.match_score
                submission.match_reasons = match_result.reasons
                submission.status = SubmissionStatus.MATCHED.value
                
                bounty = await self._get_bounty(match_result.bounty_id)
                if bounty:
                    submission.reward_amount = bounty.reward_amount
                    submission.reward_token = bounty.reward_token
        
        self.db.add(submission)
        await self.db.commit()
        await self.db.refresh(submission)
        
        match_result = None
        if submission.bounty_id:
            bounty = await self._get_bounty(str(submission.bounty_id))
            if bounty:
                match_result = MatchResult(
                    bounty_id=str(submission.bounty_id),
                    bounty_title=bounty.title,
                    match_score=submission.match_score or 0.0,
                    confidence=submission.match_confidence or MatchConfidence.LOW.value,
                    reasons=submission.match_reasons,
                    github_issue_url=bounty.github_issue_url,
                )
        
        return submission, match_result
    
    async def update_submission(
        self,
        submission_id: str,
        data: SubmissionUpdate,
        reviewer_id: Optional[str] = None,
    ) -> Optional[SubmissionDB]:
        """Update a submission's status."""
        submission = await self._get_submission(submission_id)
        if not submission:
            return None
        
        if data.status:
            submission.status = data.status
            if reviewer_id:
                submission.reviewer_id = reviewer_id
                submission.reviewed_at = datetime.now(timezone.utc)
        
        if data.review_notes is not None:
            submission.review_notes = data.review_notes
        
        if data.bounty_id:
            submission.bounty_id = data.bounty_id
            bounty = await self._get_bounty(data.bounty_id)
            if bounty:
                submission.reward_amount = bounty.reward_amount
                submission.reward_token = bounty.reward_token
        
        await self.db.commit()
        await self.db.refresh(submission)
        
        return submission
    
    async def get_submission(self, submission_id: str) -> Optional[SubmissionDB]:
        """Get a submission by ID."""
        return await self._get_submission(submission_id)
    
    async def list_submissions(
        self,
        params: SubmissionSearchParams,
    ) -> SubmissionListResponse:
        """List submissions with filtering and pagination."""
        query = select(SubmissionDB)
        count_query = select(func.count(SubmissionDB.id))
        
        conditions = []
        
        if params.contributor_id:
            conditions.append(SubmissionDB.contributor_id == params.contributor_id)
        
        if params.bounty_id:
            conditions.append(SubmissionDB.bounty_id == params.bounty_id)
        
        if params.status:
            conditions.append(SubmissionDB.status == params.status)
        
        if params.wallet:
            conditions.append(SubmissionDB.contributor_wallet == params.wallet)
        
        if conditions:
            query = query.where(and_(*conditions))
            count_query = count_query.where(and_(*conditions))
        
        sort_column = self._get_sort_column(params.sort)
        if params.sort in ('oldest',):
            query = query.order_by(sort_column.asc())
        else:
            query = query.order_by(sort_column.desc())
        
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0
        
        query = query.offset(params.skip).limit(params.limit)
        
        result = await self.db.execute(query)
        submissions = result.scalars().all()
        
        return SubmissionListResponse(
            items=[SubmissionListItem.model_validate(s) for s in submissions],
            total=total,
            skip=params.skip,
            limit=params.limit,
        )
    
    async def get_contributor_stats(
        self,
        contributor_id: str,
    ) -> SubmissionStats:
        """Get submission statistics for a contributor."""
        total_query = select(func.count(SubmissionDB.id)).where(
            SubmissionDB.contributor_id == contributor_id
        )
        total_result = await self.db.execute(total_query)
        total = total_result.scalar() or 0
        
        status_counts = {}
        for status in SubmissionStatus:
            count_query = select(func.count(SubmissionDB.id)).where(
                and_(
                    SubmissionDB.contributor_id == contributor_id,
                    SubmissionDB.status == status.value,
                )
            )
            count_result = await self.db.execute(count_query)
            status_counts[status.value] = count_result.scalar() or 0
        
        earnings_query = select(func.sum(SubmissionDB.reward_amount)).where(
            and_(
                SubmissionDB.contributor_id == contributor_id,
                SubmissionDB.status == SubmissionStatus.PAID.value,
            )
        )
        earnings_result = await self.db.execute(earnings_query)
        total_earnings = float(earnings_result.scalar() or 0)
        
        approved_or_rejected = status_counts.get(SubmissionStatus.APPROVED.value, 0) + \
                               status_counts.get(SubmissionStatus.REJECTED.value, 0) + \
                               status_counts.get(SubmissionStatus.PAID.value, 0)
        approval_rate = 0.0
        if approved_or_rejected > 0:
            approved = status_counts.get(SubmissionStatus.APPROVED.value, 0) + \
                       status_counts.get(SubmissionStatus.PAID.value, 0)
            approval_rate = approved / approved_or_rejected
        
        return SubmissionStats(
            total_submissions=total,
            pending=status_counts.get(SubmissionStatus.PENDING.value, 0) +
                    status_counts.get(SubmissionStatus.MATCHED.value, 0) +
                    status_counts.get(SubmissionStatus.REVIEWING.value, 0),
            approved=status_counts.get(SubmissionStatus.APPROVED.value, 0),
            rejected=status_counts.get(SubmissionStatus.REJECTED.value, 0),
            paid=status_counts.get(SubmissionStatus.PAID.value, 0),
            total_earnings=total_earnings,
            approval_rate=round(approval_rate, 3),
        )
    
    async def get_bounty_submissions(
        self,
        bounty_id: str,
    ) -> List[SubmissionDB]:
        """Get all submissions for a specific bounty."""
        query = select(SubmissionDB).where(
            SubmissionDB.bounty_id == bounty_id
        ).order_by(SubmissionDB.created_at.desc())
        
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    def _parse_pr_url(self, url: str) -> dict:
        """Parse GitHub PR URL to extract repository and PR number."""
        match = self.PR_URL_PATTERN.match(url)
        if match:
            owner, repo, pr_number = match.groups()
            return {
                'owner': owner,
                'repo': f"{owner}/{repo}",
                'pr_number': int(pr_number),
            }
        return {}
    
    async def _get_bounty(self, bounty_id: str) -> Optional[BountyDB]:
        """Get a bounty by ID."""
        query = select(BountyDB).where(BountyDB.id == bounty_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def _get_submission(self, submission_id: str) -> Optional[SubmissionDB]:
        """Get a submission by ID."""
        query = select(SubmissionDB).where(SubmissionDB.id == submission_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def _auto_match_bounty(
        self,
        submission: SubmissionDB,
    ) -> Optional[MatchResult]:
        """Automatically match a submission to a bounty."""
        if not submission.pr_repo or not submission.pr_number:
            return None
        
        query = select(BountyDB).where(
            BountyDB.status.in_([BountyStatus.OPEN.value, BountyStatus.CLAIMED.value])
        )
        result = await self.db.execute(query)
        bounties = result.scalars().all()
        
        best_match: Optional[MatchResult] = None
        best_score = 0.0
        
        for bounty in bounties:
            score, reasons = self._calculate_match_score(submission, bounty)
            
            if score > best_score:
                best_score = score
                confidence = self._get_confidence(score)
                best_match = MatchResult(
                    bounty_id=str(bounty.id),
                    bounty_title=bounty.title,
                    match_score=score,
                    confidence=confidence,
                    reasons=reasons,
                    github_issue_url=bounty.github_issue_url,
                )
        
        if best_match and best_score >= 0.5:
            return best_match
        
        return None
    
    def _calculate_match_score(
        self,
        submission: SubmissionDB,
        bounty: BountyDB,
    ) -> Tuple[float, List[str]]:
        """Calculate match score between submission and bounty."""
        score = 0.0
        reasons = []
        
        if bounty.github_repo and submission.pr_repo:
            if bounty.github_repo.lower() == submission.pr_repo.lower():
                score += 0.7
                reasons.append(f"PR targets the same repository ({submission.pr_repo})")
        
        if bounty.github_issue_url:
            issue_match = re.search(r'/issues/(\d+)', bounty.github_issue_url)
            if issue_match:
                issue_num = int(issue_match.group(1))
                reasons.append(f"Bounty linked to issue #{issue_num}")
        
        return min(score, 1.0), reasons
    
    def _get_confidence(self, score: float) -> str:
        """Determine confidence level from score."""
        if score >= 0.9:
            return MatchConfidence.HIGH.value
        elif score >= 0.7:
            return MatchConfidence.MEDIUM.value
        else:
            return MatchConfidence.LOW.value
    
    def _get_sort_column(self, sort: str):
        """Get the sort column for a given sort parameter."""
        sort_map = {
            'newest': SubmissionDB.created_at,
            'oldest': SubmissionDB.created_at,
            'status': SubmissionDB.status,
            'reward': SubmissionDB.reward_amount,
        }
        return sort_map.get(sort, SubmissionDB.created_at)
