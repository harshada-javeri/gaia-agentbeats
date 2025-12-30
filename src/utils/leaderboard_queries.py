"""SQL queries and utilities for leaderboard operations."""

from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_

from src.agentbeats.database import Submission, LeaderboardEntry


class LeaderboardQueries:
    """Database queries for leaderboard operations."""

    @staticmethod
    def get_leaderboard(
        db: Session,
        level: int = 1,
        split: str = "validation",
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Get top agents for a specific level and split.
        
        Args:
            db: Database session
            level: GAIA level (1, 2, or 3)
            split: Dataset split (validation or test)
            limit: Maximum number of results
            
        Returns:
            List of leaderboard entries sorted by accuracy (descending)
        """
        query = db.query(LeaderboardEntry).filter(
            and_(
                LeaderboardEntry.level == level,
                LeaderboardEntry.split == split,
            )
        ).order_by(
            desc(LeaderboardEntry.accuracy),
            LeaderboardEntry.average_time_per_task
        ).limit(limit)
        
        results = []
        for idx, entry in enumerate(query, 1):
            results.append({
                "rank": idx,
                "agent_name": entry.agent_name,
                "team_name": entry.team_name,
                "agent_version": entry.agent_version,
                "accuracy": entry.accuracy,
                "correct_tasks": entry.correct_tasks,
                "total_tasks": entry.total_tasks,
                "average_time_per_task": round(entry.average_time_per_task, 2),
                "submission_timestamp": entry.submission_timestamp.isoformat(),
                "github_repo": entry.github_repo,
            })
        
        return results

    @staticmethod
    def get_team_leaderboard(
        db: Session,
        level: int = 1,
        split: str = "validation",
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Get leaderboard grouped by team with best agent per team.
        
        Args:
            db: Database session
            level: GAIA level (1, 2, or 3)
            split: Dataset split (validation or test)
            limit: Maximum number of results
            
        Returns:
            List of team entries sorted by best agent accuracy
        """
        # Subquery to get best submission per team
        best_submissions = db.query(
            Submission.team_name,
            func.max(Submission.accuracy).label("best_accuracy"),
        ).filter(
            and_(
                Submission.level == level,
                Submission.split == split,
            )
        ).group_by(Submission.team_name).subquery()

        # Main query to get full submission details
        query = db.query(Submission).join(
            best_submissions,
            and_(
                Submission.team_name == best_submissions.c.team_name,
                Submission.accuracy == best_submissions.c.best_accuracy,
                Submission.level == level,
                Submission.split == split,
            )
        ).order_by(
            desc(Submission.accuracy),
            Submission.average_time_per_task
        ).limit(limit)

        results = []
        for idx, sub in enumerate(query, 1):
            results.append({
                "rank": idx,
                "team_name": sub.team_name or "Anonymous",
                "agent_name": sub.agent_name,
                "accuracy": sub.accuracy,
                "correct_tasks": sub.correct_tasks,
                "total_tasks": sub.total_tasks,
                "average_time_per_task": round(sub.average_time_per_task, 2),
                "submission_timestamp": sub.timestamp.isoformat(),
                "submission_id": sub.submission_id,
            })
        
        return results

    @staticmethod
    def get_agent_history(
        db: Session,
        agent_name: str,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """Get submission history for a specific agent.
        
        Args:
            db: Database session
            agent_name: Name of the agent
            limit: Maximum number of results
            
        Returns:
            List of submissions for the agent
        """
        submissions = db.query(Submission).filter(
            Submission.agent_name == agent_name
        ).order_by(
            desc(Submission.timestamp)
        ).limit(limit).all()

        return [
            {
                "submission_id": sub.submission_id,
                "agent_version": sub.agent_version,
                "level": sub.level,
                "split": sub.split,
                "accuracy": sub.accuracy,
                "correct_tasks": sub.correct_tasks,
                "total_tasks": sub.total_tasks,
                "timestamp": sub.timestamp.isoformat(),
                "github_branch": sub.github_branch,
            }
            for sub in submissions
        ]

    @staticmethod
    def get_team_history(
        db: Session,
        team_name: str,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """Get submission history for a team.
        
        Args:
            db: Database session
            team_name: Name of the team
            limit: Maximum number of results
            
        Returns:
            List of team submissions
        """
        submissions = db.query(Submission).filter(
            Submission.team_name == team_name
        ).order_by(
            desc(Submission.timestamp)
        ).limit(limit).all()

        return [
            {
                "submission_id": sub.submission_id,
                "agent_name": sub.agent_name,
                "agent_version": sub.agent_version,
                "level": sub.level,
                "split": sub.split,
                "accuracy": sub.accuracy,
                "timestamp": sub.timestamp.isoformat(),
            }
            for sub in submissions
        ]

    @staticmethod
    def get_submission_by_id(
        db: Session,
        submission_id: str,
    ) -> Optional[Dict[str, Any]]:
        """Get detailed submission information.
        
        Args:
            db: Database session
            submission_id: Submission ID
            
        Returns:
            Submission details or None
        """
        submission = db.query(Submission).filter(
            Submission.submission_id == submission_id
        ).first()

        if not submission:
            return None

        return {
            "submission_id": submission.submission_id,
            "agent_name": submission.agent_name,
            "agent_version": submission.agent_version,
            "team_name": submission.team_name,
            "level": submission.level,
            "split": submission.split,
            "accuracy": submission.accuracy,
            "correct_tasks": submission.correct_tasks,
            "total_tasks": submission.total_tasks,
            "average_time_per_task": round(submission.average_time_per_task, 2),
            "total_time_seconds": round(submission.total_time_seconds, 2),
            "errors": submission.errors,
            "github_repo": submission.github_repo,
            "github_commit_hash": submission.github_commit_hash,
            "github_branch": submission.github_branch,
            "timestamp": submission.timestamp.isoformat(),
            "is_verified": submission.is_verified,
            "task_results": submission.task_results,
        }

    @staticmethod
    def get_recent_submissions(
        db: Session,
        days: int = 7,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """Get recent submissions from the last N days.
        
        Args:
            db: Database session
            days: Number of days to look back
            limit: Maximum number of results
            
        Returns:
            List of recent submissions
        """
        cutoff_time = datetime.utcnow() - timedelta(days=days)
        
        submissions = db.query(Submission).filter(
            Submission.timestamp >= cutoff_time
        ).order_by(
            desc(Submission.timestamp)
        ).limit(limit).all()

        return [
            {
                "submission_id": sub.submission_id,
                "agent_name": sub.agent_name,
                "team_name": sub.team_name,
                "level": sub.level,
                "accuracy": sub.accuracy,
                "timestamp": sub.timestamp.isoformat(),
            }
            for sub in submissions
        ]

    @staticmethod
    def get_stats(db: Session) -> Dict[str, Any]:
        """Get overall leaderboard statistics.
        
        Args:
            db: Database session
            
        Returns:
            Statistics about submissions
        """
        total_submissions = db.query(func.count(Submission.id)).scalar()
        unique_teams = db.query(func.count(func.distinct(Submission.team_name))).scalar()
        unique_agents = db.query(func.count(func.distinct(Submission.agent_name))).scalar()
        
        stats_by_level = {}
        for level in [1, 2, 3]:
            level_subs = db.query(Submission).filter(
                Submission.level == level
            ).all()
            if level_subs:
                avg_accuracy = sum(s.accuracy for s in level_subs) / len(level_subs)
                stats_by_level[f"level_{level}"] = {
                    "submissions": len(level_subs),
                    "average_accuracy": round(avg_accuracy, 2),
                    "best_accuracy": max(s.accuracy for s in level_subs),
                }

        return {
            "total_submissions": total_submissions,
            "unique_teams": unique_teams,
            "unique_agents": unique_agents,
            "stats_by_level": stats_by_level,
        }

    @staticmethod
    def refresh_leaderboard(db: Session) -> int:
        """Refresh leaderboard rankings from recent submissions.
        
        This materializes the best submissions for display.
        
        Args:
            db: Database session
            
        Returns:
            Number of leaderboard entries refreshed
        """
        # Clear existing leaderboard
        db.query(LeaderboardEntry).delete()
        
        # Get best submission per team per level/split combination
        for level in [1, 2, 3]:
            for split in ["validation", "test"]:
                best_per_team = db.query(
                    Submission.team_name,
                    func.max(Submission.accuracy).label("max_accuracy"),
                ).filter(
                    and_(
                        Submission.level == level,
                        Submission.split == split,
                    )
                ).group_by(Submission.team_name).all()

                for team_name, max_accuracy in best_per_team:
                    submission = db.query(Submission).filter(
                        and_(
                            Submission.team_name == team_name,
                            Submission.level == level,
                            Submission.split == split,
                            Submission.accuracy == max_accuracy,
                        )
                    ).order_by(
                        desc(Submission.timestamp)
                    ).first()

                    if submission:
                        # Get rank for this submission
                        rank = db.query(func.count(Submission.id)).filter(
                            and_(
                                Submission.level == level,
                                Submission.split == split,
                                Submission.accuracy > max_accuracy,
                            )
                        ).scalar() + 1

                        entry = LeaderboardEntry(
                            rank=rank,
                            level=level,
                            split=split,
                            agent_name=submission.agent_name,
                            team_name=team_name,
                            agent_version=submission.agent_version,
                            accuracy=submission.accuracy,
                            correct_tasks=submission.correct_tasks,
                            total_tasks=submission.total_tasks,
                            average_time_per_task=submission.average_time_per_task,
                            best_submission_id=submission.submission_id,
                            submission_timestamp=submission.timestamp,
                            github_repo=submission.github_repo,
                            github_commit_hash=submission.github_commit_hash,
                        )
                        db.add(entry)

        db.commit()
        count = db.query(func.count(LeaderboardEntry.id)).scalar()
        return count
