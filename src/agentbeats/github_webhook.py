"""GitHub webhook handler for submission integration."""

import hashlib
import hmac
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from src.agentbeats.database import Submission, WebhookEvent

logger = logging.getLogger("github_webhook")


class GitHubWebhookHandler:
    """Handles GitHub webhook events for benchmark submissions."""

    def __init__(self, webhook_secret: Optional[str] = None):
        """Initialize webhook handler.
        
        Args:
            webhook_secret: Secret key for webhook verification
        """
        self.webhook_secret = webhook_secret

    def verify_signature(self, payload: bytes, signature: str) -> bool:
        """Verify GitHub webhook signature.
        
        Args:
            payload: Raw request body
            signature: X-Hub-Signature-256 header value
            
        Returns:
            True if signature is valid
        """
        if not self.webhook_secret:
            logger.warning("Webhook secret not configured, skipping signature verification")
            return True

        try:
            # GitHub sends signature as sha256=<hash>
            if not signature.startswith("sha256="):
                return False

            expected_hash = signature[7:]
            computed_hash = hmac.new(
                self.webhook_secret.encode(),
                payload,
                hashlib.sha256
            ).hexdigest()

            return hmac.compare_digest(computed_hash, expected_hash)
        except Exception as e:
            logger.error(f"Signature verification error: {e}")
            return False

    def extract_gaia_config(self, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract GAIA configuration from commit message or PR.
        
        Looks for JSON in commit message or PR body with format:
        ```json
        {"gaia_submission": {...}}
        ```
        
        Args:
            payload: GitHub webhook payload
            
        Returns:
            GAIA configuration dict or None
        """
        # Try to extract from commit message (push event)
        if "head_commit" in payload and payload["head_commit"]:
            message = payload["head_commit"].get("message", "")
            return self._parse_gaia_config(message)

        # Try to extract from PR body (pull_request event)
        if "pull_request" in payload:
            body = payload["pull_request"].get("body", "")
            return self._parse_gaia_config(body)

        return None

    @staticmethod
    def _parse_gaia_config(text: str) -> Optional[Dict[str, Any]]:
        """Parse GAIA configuration from text.
        
        Args:
            text: Text containing JSON configuration
            
        Returns:
            Configuration dict or None
        """
        try:
            # Look for JSON block
            start = text.find("{")
            end = text.rfind("}") + 1
            if start >= 0 and end > start:
                json_str = text[start:end]
                config = json.loads(json_str)
                return config.get("gaia_submission")
        except Exception as e:
            logger.debug(f"Failed to parse GAIA config: {e}")
        return None

    def process_push_event(
        self,
        db: Session,
        payload: Dict[str, Any],
    ) -> Optional[Submission]:
        """Process GitHub push event.
        
        Args:
            db: Database session
            payload: Push event payload
            
        Returns:
            Created submission or None
        """
        try:
            repo_full_name = payload["repository"]["full_name"]
            commit_hash = payload["head_commit"]["id"]
            branch = payload["ref"].split("/")[-1]
            
            # Extract GAIA config
            gaia_config = self.extract_gaia_config(payload)
            if not gaia_config:
                logger.info(f"No GAIA config found in push to {repo_full_name}")
                return None

            # Create submission from config
            submission = self._create_submission_from_config(
                gaia_config,
                github_repo=repo_full_name,
                github_commit_hash=commit_hash,
                github_branch=branch,
            )

            if submission:
                db.add(submission)
                db.commit()
                db.refresh(submission)
                logger.info(f"Created submission {submission.submission_id}")
                return submission

        except Exception as e:
            logger.error(f"Error processing push event: {e}")
        
        return None

    def process_pull_request_event(
        self,
        db: Session,
        payload: Dict[str, Any],
    ) -> Optional[Submission]:
        """Process GitHub pull request event.
        
        Args:
            db: Database session
            payload: Pull request event payload
            
        Returns:
            Created submission or None
        """
        try:
            action = payload.get("action")
            if action not in ["opened", "synchronize"]:
                logger.info(f"Skipping PR action: {action}")
                return None

            repo_full_name = payload["repository"]["full_name"]
            pr_number = payload["pull_request"]["number"]
            branch = payload["pull_request"]["head"]["ref"]
            commit_hash = payload["pull_request"]["head"]["sha"]
            
            # Extract GAIA config
            gaia_config = self.extract_gaia_config(payload)
            if not gaia_config:
                logger.info(f"No GAIA config found in PR #{pr_number}")
                return None

            # Create submission
            submission = self._create_submission_from_config(
                gaia_config,
                github_repo=repo_full_name,
                github_commit_hash=commit_hash,
                github_branch=branch,
                github_pr_number=pr_number,
            )

            if submission:
                db.add(submission)
                db.commit()
                db.refresh(submission)
                logger.info(f"Created submission {submission.submission_id} from PR #{pr_number}")
                return submission

        except Exception as e:
            logger.error(f"Error processing PR event: {e}")
        
        return None

    @staticmethod
    def _create_submission_from_config(
        config: Dict[str, Any],
        github_repo: str = None,
        github_commit_hash: str = None,
        github_branch: str = None,
        github_pr_number: int = None,
    ) -> Optional[Submission]:
        """Create submission from configuration.
        
        Expected config format:
        {
            "agent_name": "my-agent",
            "agent_version": "1.0.0",
            "team_name": "my-team",
            "level": 1,
            "split": "validation",
            "accuracy": 50.0,
            "correct_tasks": 15,
            "total_tasks": 30,
            "average_time_per_task": 2.5,
            "total_time_seconds": 75.0,
            "model_used": "gpt-4o",
            "environment": "docker"
        }
        
        Args:
            config: Configuration dictionary
            github_repo: Repository full name
            github_commit_hash: Commit hash
            github_branch: Branch name
            github_pr_number: PR number
            
        Returns:
            Submission object or None if validation fails
        """
        try:
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
                if field not in config:
                    logger.error(f"Missing required field in config: {field}")
                    return None

            # Generate submission ID
            import uuid
            submission_id = f"github-{uuid.uuid4().hex[:12]}"

            submission = Submission(
                submission_id=submission_id,
                agent_name=config["agent_name"],
                agent_version=config["agent_version"],
                team_name=config.get("team_name"),
                level=config["level"],
                split=config["split"],
                accuracy=float(config["accuracy"]),
                correct_tasks=int(config["correct_tasks"]),
                total_tasks=int(config["total_tasks"]),
                average_time_per_task=float(config["average_time_per_task"]),
                total_time_seconds=float(config["total_time_seconds"]),
                errors=int(config.get("errors", 0)),
                model_used=config.get("model_used"),
                environment=config.get("environment", "github-webhook"),
                task_results=config.get("task_results"),
                github_repo=github_repo,
                github_commit_hash=github_commit_hash,
                github_branch=github_branch,
                github_pr_number=github_pr_number,
                timestamp=datetime.utcnow(),
            )

            return submission

        except Exception as e:
            logger.error(f"Error creating submission from config: {e}")
        
        return None

    def store_webhook_event(
        self,
        db: Session,
        event_type: str,
        event_id: str,
        payload: Dict[str, Any],
        repository: str,
        branch: str = None,
        commit_hash: str = None,
    ) -> WebhookEvent:
        """Store webhook event for audit and retry logic.
        
        Args:
            db: Database session
            event_type: Type of event (push, pull_request, etc)
            event_id: GitHub event ID
            payload: Complete event payload
            repository: Repository name
            branch: Branch name
            commit_hash: Commit hash
            
        Returns:
            Created WebhookEvent object
        """
        event = WebhookEvent(
            event_type=event_type,
            event_id=event_id,
            payload=payload,
            repository=repository,
            branch=branch,
            commit_hash=commit_hash,
            timestamp=datetime.utcnow(),
        )
        
        db.add(event)
        db.commit()
        db.refresh(event)
        
        return event
