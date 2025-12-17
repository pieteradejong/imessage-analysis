#!/usr/bin/env python3
"""
Main entry point for iMessage Analysis.

Provides a command-line interface for database analysis.
"""
from typing import List, Optional
import argparse
import sys
import logging
from pathlib import Path

from imessage_analysis.config import get_config
from imessage_analysis.database import DatabaseConnection
from imessage_analysis.analysis import (
    get_database_summary,
    get_latest_messages_data,
    get_message_statistics_by_chat,
)
from imessage_analysis.logger_config import setup_logging
from imessage_analysis.snapshot import create_timestamped_snapshot
from imessage_analysis.utils import Colors

# Setup logging
setup_logging(level=logging.INFO)


def print_section(title: str) -> None:
    """Print a formatted section title."""
    print(f"\n{Colors.BOLD}{Colors.HEADER}{'=' * 60}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.HEADER}{title}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.HEADER}{'=' * 60}{Colors.ENDC}\n")


def _parse_args(argv: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Analyze iMessage chat.db locally (read-only).")
    parser.add_argument(
        "--db-path",
        default=None,
        help="Path to chat.db (defaults to ./chat.db or ~/Library/Messages/chat.db).",
    )
    parser.add_argument(
        "--snapshot",
        action="store_true",
        help="Create a timestamped snapshot of the DB and analyze the snapshot instead.",
    )
    parser.add_argument(
        "--snapshot-dir",
        default="snapshots",
        help="Directory to write snapshots into (default: ./snapshots).",
    )
    parser.add_argument(
        "--use-memory",
        action="store_true",
        help="Load the DB into RAM (SQLite :memory:) before running analysis.",
    )
    parser.add_argument(
        "--latest-limit",
        type=int,
        default=10,
        help="How many latest messages to print (default: 10).",
    )
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None):
    """Main function."""
    if argv is None:
        argv = sys.argv[1:]
    args = _parse_args(argv)

    # Get configuration
    config = get_config(db_path=args.db_path)
    
    if not config.validate():
        print(f"{Colors.FAIL}Error: Database file not found or not readable.{Colors.ENDC}")
        print(f"Please ensure chat.db exists in the current directory or at:")
        print(f"  {config.DEFAULT_MESSAGES_PATH / config.DEFAULT_DB_NAME}")
        sys.exit(1)

    if args.snapshot:
        result = create_timestamped_snapshot(
            Path(config.db_path_str),
            Path(args.snapshot_dir),
        )
        config = get_config(db_path=str(result.snapshot_path))
        print(
            f"{Colors.OKGREEN}Snapshot created: {result.snapshot_path}{Colors.ENDC}"
        )
    
    print(f"{Colors.OKGREEN}Using database: {config.db_path_str}{Colors.ENDC}")
    
    try:
        with DatabaseConnection(config, use_memory=args.use_memory) as db:
            # Database Summary
            print_section("Database Summary")
            summary = get_database_summary(db)
            print(f"Total tables: {summary['table_count']}")
            print(f"Total messages: {summary['total_messages']:,}")
            print(f"Total chats: {summary['total_chats']:,}")
            
            # Table names and row counts
            print_section("Table Information")
            table_names = db.get_table_names()
            row_counts = db.get_row_counts_by_table(table_names)
            
            print(f"\n{Colors.BOLD}Table names:{Colors.ENDC}")
            for table_name in table_names:
                print(f"  - {table_name}")
            
            print(f"\n{Colors.BOLD}Row counts by table:{Colors.ENDC}")
            for table_name, count in row_counts:
                print(f"  {table_name:30s}: {count:>10,}")
            
            # Latest messages
            print_section(f"Latest Messages ({args.latest_limit})")
            latest_messages = get_latest_messages_data(db, limit=args.latest_limit)
            for i, msg in enumerate(latest_messages, 1):
                direction = "You" if msg['is_from_me'] else "Them"
                print(f"{i:2d}. [{msg['date']}] {direction}: {msg['text'][:60]}...")
            
            # Message statistics by chat
            print_section("Top Chats by Message Count")
            chat_stats = get_message_statistics_by_chat(db)
            for i, stat in enumerate(chat_stats[:10], 1):
                print(f"{i:2d}. {stat['chat_identifier']:30s}: {stat['message_count']:>6,} messages")
            
            # Column information for message table
            print_section("Message Table Columns")
            columns = db.get_columns_for_table('message')
            print(f"Total columns: {len(columns)}")
            print(f"\nFirst 10 columns:")
            for col in columns[:10]:
                print(f"  - {col[1]} ({col[2]})")
            
    except Exception as e:
        print(f"{Colors.FAIL}Error: {e}{Colors.ENDC}")
        logging.exception("Error during execution")
        sys.exit(1)


if __name__ == '__main__':
    main()


