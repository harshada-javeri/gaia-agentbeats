#!/usr/bin/env python3
"""Database setup and migration script for GAIA leaderboard."""

import os
import sys
import logging
from sqlalchemy import text

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.agentbeats.database import engine, init_db, SessionLocal

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("db_setup")


def init_database():
    """Initialize database with tables and basic configuration."""
    try:
        logger.info("Initializing GAIA Leaderboard database...")
        
        # Create all tables
        init_db()
        
        logger.info("✅ Database initialized successfully")
        
        # Get database info
        with SessionLocal() as db:
            db_url = str(engine.url).split("://")[0]
            logger.info(f"Database type: {db_url}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error initializing database: {e}")
        return False


def check_database():
    """Check database connectivity and schema."""
    try:
        logger.info("Checking database connectivity...")
        
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            result.close()
            logger.info("✅ Database is accessible")
        
        # Check tables
        from src.agentbeats.database import Submission, LeaderboardEntry, WebhookEvent
        
        inspector_tables = []
        if hasattr(engine.inspector, 'get_table_names'):
            inspector_tables = engine.inspector.get_table_names()
        else:
            from sqlalchemy import inspect
            inspector_tables = inspect(engine).get_table_names()
        
        logger.info(f"Tables found: {inspector_tables}")
        
        expected_tables = ["submissions", "leaderboard", "webhook_events"]
        missing = set(expected_tables) - set(inspector_tables)
        
        if missing:
            logger.warning(f"⚠️  Missing tables: {missing}")
            return False
        
        logger.info("✅ All required tables exist")
        return True
        
    except Exception as e:
        logger.error(f"❌ Database check failed: {e}")
        return False


def show_stats():
    """Display database statistics."""
    try:
        from src.utils.leaderboard_queries import LeaderboardQueries
        
        db = SessionLocal()
        stats = LeaderboardQueries.get_stats(db)
        db.close()
        
        logger.info("📊 Database Statistics:")
        logger.info(f"  Total submissions: {stats['total_submissions']}")
        logger.info(f"  Unique teams: {stats['unique_teams']}")
        logger.info(f"  Unique agents: {stats['unique_agents']}")
        
        for level, data in stats.get('stats_by_level', {}).items():
            logger.info(f"  {level}:")
            logger.info(f"    Submissions: {data['submissions']}")
            logger.info(f"    Avg accuracy: {data['average_accuracy']:.1f}%")
            logger.info(f"    Best accuracy: {data['best_accuracy']:.1f}%")
        
    except Exception as e:
        logger.error(f"Error getting stats: {e}")


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="GAIA Leaderboard Database Setup")
    parser.add_argument(
        "command",
        choices=["init", "check", "stats"],
        help="Command to run"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force initialization (drop existing tables)"
    )
    
    args = parser.parse_args()
    
    if args.command == "init":
        if args.force:
            logger.warning("⚠️  Dropping existing tables...")
            from src.agentbeats.database import Base
            Base.metadata.drop_all(bind=engine)
        
        success = init_database()
        sys.exit(0 if success else 1)
    
    elif args.command == "check":
        success = check_database()
        sys.exit(0 if success else 1)
    
    elif args.command == "stats":
        show_stats()
        sys.exit(0)


if __name__ == "__main__":
    main()
