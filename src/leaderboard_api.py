"""FastAPI endpoints for leaderboard API."""

import logging
import os
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Depends, Request, Header
from sqlalchemy.orm import Session

from src.agentbeats.database import init_db, get_db, Submission, engine
from src.agentbeats.github_webhook import GitHubWebhookHandler
from src.utils.leaderboard_queries import LeaderboardQueries

logger = logging.getLogger("leaderboard_api")

# Initialize database
init_db()

# Create FastAPI app
app = FastAPI(
    title="GAIA Leaderboard API",
    description="Leaderboard and submission management for GAIA Benchmark on AgentBeats",
    version="1.0.0"
)

# Initialize webhook handler
webhook_secret = os.getenv("GITHUB_WEBHOOK_SECRET")
webhook_handler = GitHubWebhookHandler(webhook_secret=webhook_secret)


# ============================================================================
# Leaderboard Endpoints
# ============================================================================

@app.get("/leaderboard")
async def get_leaderboard(
    level: int = 1,
    split: str = "validation",
    limit: int = 100,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Get leaderboard for a specific level and split.
    
    Args:
        level: GAIA difficulty level (1, 2, 3)
        split: Dataset split (validation or test)
        limit: Maximum number of results
        
    Returns:
        Leaderboard entries
    """
    if level not in [1, 2, 3]:
        raise HTTPException(status_code=400, detail="Level must be 1, 2, or 3")
    if split not in ["validation", "test"]:
        raise HTTPException(status_code=400, detail="Split must be 'validation' or 'test'")

    entries = LeaderboardQueries.get_leaderboard(db, level, split, limit)
    
    return {
        "level": level,
        "split": split,
        "count": len(entries),
        "limit": limit,
        "entries": entries,
    }


@app.get("/leaderboard/teams")
async def get_team_leaderboard(
    level: int = 1,
    split: str = "validation",
    limit: int = 100,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Get leaderboard grouped by teams.
    
    Args:
        level: GAIA difficulty level (1, 2, 3)
        split: Dataset split (validation or test)
        limit: Maximum number of teams
        
    Returns:
        Team leaderboard entries
    """
    if level not in [1, 2, 3]:
        raise HTTPException(status_code=400, detail="Level must be 1, 2, or 3")

    entries = LeaderboardQueries.get_team_leaderboard(db, level, split, limit)
    
    return {
        "level": level,
        "split": split,
        "team_count": len(entries),
        "teams": entries,
    }


@app.get("/submissions/{submission_id}")
async def get_submission(
    submission_id: str,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Get detailed submission information.
    
    Args:
        submission_id: Submission ID
        
    Returns:
        Submission details
    """
    submission = LeaderboardQueries.get_submission_by_id(db, submission_id)
    
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
    
    return submission


# ============================================================================
# Agent/Team History Endpoints
# ============================================================================

@app.get("/agents/{agent_name}/history")
async def get_agent_history(
    agent_name: str,
    limit: int = 10,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Get submission history for an agent.
    
    Args:
        agent_name: Agent name
        limit: Maximum number of submissions
        
    Returns:
        List of submissions
    """
    submissions = LeaderboardQueries.get_agent_history(db, agent_name, limit)
    
    return {
        "agent_name": agent_name,
        "submission_count": len(submissions),
        "submissions": submissions,
    }


@app.get("/teams/{team_name}/history")
async def get_team_history(
    team_name: str,
    limit: int = 20,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Get submission history for a team.
    
    Args:
        team_name: Team name
        limit: Maximum number of submissions
        
    Returns:
        List of team submissions
    """
    submissions = LeaderboardQueries.get_team_history(db, team_name, limit)
    
    return {
        "team_name": team_name,
        "submission_count": len(submissions),
        "submissions": submissions,
    }


@app.get("/recent")
async def get_recent_submissions(
    days: int = 7,
    limit: int = 50,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Get recent submissions from the last N days.
    
    Args:
        days: Number of days to look back
        limit: Maximum number of submissions
        
    Returns:
        List of recent submissions
    """
    submissions = LeaderboardQueries.get_recent_submissions(db, days, limit)
    
    return {
        "days": days,
        "submission_count": len(submissions),
        "submissions": submissions,
    }


# ============================================================================
# Stats Endpoint
# ============================================================================

@app.get("/stats")
async def get_stats(
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Get overall leaderboard statistics.
    
    Returns:
        Statistics about submissions and teams
    """
    stats = LeaderboardQueries.get_stats(db)
    return stats


# ============================================================================
# Direct Submission Endpoint
# ============================================================================

@app.post("/submissions")
async def create_submission(
    submission_data: Dict[str, Any],
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Create a new submission directly.
    
    Expected format:
    {
        "agent_name": "string",
        "agent_version": "string",
        "team_name": "string (optional)",
        "level": 1|2|3,
        "split": "validation"|"test",
        "accuracy": float,
        "correct_tasks": int,
        "total_tasks": int,
        "average_time_per_task": float,
        "total_time_seconds": float,
        "model_used": "string (optional)",
        "task_results": dict (optional)
    }
    
    Args:
        submission_data: Submission data
        
    Returns:
        Created submission
    """
    try:
        import uuid
        from datetime import datetime

        # Validate required fields
        required = [
            "agent_name",
            "agent_version",
            "level",
            "split",
            "accuracy",
            "correct_tasks",
            "total_tasks",
            "average_time_per_task",
            "total_time_seconds",
        ]

        for field in required:
            if field not in submission_data:
                raise HTTPException(
                    status_code=400,
                    detail=f"Missing required field: {field}"
                )

        submission_id = f"direct-{uuid.uuid4().hex[:12]}"

        submission = Submission(
            submission_id=submission_id,
            agent_name=submission_data["agent_name"],
            agent_version=submission_data["agent_version"],
            team_name=submission_data.get("team_name"),
            level=int(submission_data["level"]),
            split=submission_data["split"],
            accuracy=float(submission_data["accuracy"]),
            correct_tasks=int(submission_data["correct_tasks"]),
            total_tasks=int(submission_data["total_tasks"]),
            average_time_per_task=float(submission_data["average_time_per_task"]),
            total_time_seconds=float(submission_data["total_time_seconds"]),
            errors=int(submission_data.get("errors", 0)),
            model_used=submission_data.get("model_used"),
            task_results=submission_data.get("task_results"),
            timestamp=datetime.utcnow(),
        )

        db.add(submission)
        db.commit()
        db.refresh(submission)

        logger.info(f"Created submission {submission_id}")

        return {
            "status": "created",
            "submission_id": submission_id,
            "agent_name": submission.agent_name,
            "accuracy": submission.accuracy,
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating submission: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# GitHub Webhook Endpoint
# ============================================================================

@app.post("/webhooks/github")
async def github_webhook(
    request: Request,
    x_github_event: str = Header(None),
    x_github_delivery: str = Header(None),
    x_hub_signature_256: str = Header(None),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """GitHub webhook endpoint for automated submissions.
    
    Expected in commit message or PR body:
    ```json
    {
        "gaia_submission": {
            "agent_name": "my-agent",
            "agent_version": "1.0.0",
            "team_name": "my-team",
            "level": 1,
            "split": "validation",
            "accuracy": 50.0,
            "correct_tasks": 15,
            "total_tasks": 30,
            "average_time_per_task": 2.5,
            "total_time_seconds": 75.0
        }
    }
    ```
    
    Args:
        request: HTTP request
        x_github_event: GitHub event type
        x_github_delivery: GitHub delivery ID
        x_hub_signature_256: Webhook signature
        
    Returns:
        Webhook processing result
    """
    try:
        # Get raw body for signature verification
        body = await request.body()
        
        # Verify signature
        if x_hub_signature_256 and not webhook_handler.verify_signature(body, x_hub_signature_256):
            logger.warning(f"Invalid webhook signature for delivery {x_github_delivery}")
            raise HTTPException(status_code=401, detail="Invalid signature")

        # Parse payload
        payload = await request.json()

        # Extract repository info
        repo_name = payload.get("repository", {}).get("full_name", "unknown")
        
        # Store webhook event for audit
        webhook_handler.store_webhook_event(
            db,
            event_type=x_github_event,
            event_id=x_github_delivery,
            payload=payload,
            repository=repo_name,
            branch=payload.get("ref", "").split("/")[-1] if "ref" in payload else None,
            commit_hash=payload.get("head_commit", {}).get("id") if "head_commit" in payload else payload.get("pull_request", {}).get("head", {}).get("sha"),
        )

        # Process based on event type
        submission = None
        
        if x_github_event == "push":
            submission = webhook_handler.process_push_event(db, payload)
        elif x_github_event == "pull_request":
            submission = webhook_handler.process_pull_request_event(db, payload)
        else:
            logger.info(f"Ignoring event type: {x_github_event}")

        if submission:
            # Refresh leaderboard
            LeaderboardQueries.refresh_leaderboard(db)
            
            return {
                "status": "created",
                "submission_id": submission.submission_id,
                "agent_name": submission.agent_name,
                "accuracy": submission.accuracy,
            }
        else:
            return {
                "status": "no_submission",
                "message": "No GAIA config found in event",
            }

    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Admin Endpoints
# ============================================================================

@app.post("/admin/refresh-leaderboard")
async def refresh_leaderboard(
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Refresh leaderboard rankings.
    
    This should be called periodically to update rankings.
    
    Returns:
        Refresh result
    """
    try:
        count = LeaderboardQueries.refresh_leaderboard(db)
        logger.info(f"Refreshed leaderboard with {count} entries")
        
        return {
            "status": "success",
            "entries_updated": count,
        }
    except Exception as e:
        logger.error(f"Error refreshing leaderboard: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check() -> Dict[str, str]:
    """Health check endpoint.
    
    Returns:
        Health status
    """
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("LEADERBOARD_API_PORT", 8000))
    host = os.getenv("LEADERBOARD_API_HOST", "0.0.0.0")
    
    uvicorn.run(app, host=host, port=port)
