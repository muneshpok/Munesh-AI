"""CLI commands for Munesh AI system management."""

import argparse
import sys
import uvicorn


def main() -> None:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Munesh AI - WhatsApp Business Automation Platform"
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Start command
    start_parser = subparsers.add_parser("start", help="Start the Munesh AI server")
    start_parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    start_parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    start_parser.add_argument("--reload", action="store_true", help="Enable auto-reload")

    # Leads command
    subparsers.add_parser("leads", help="Show all leads")

    # Broadcast command
    broadcast_parser = subparsers.add_parser("broadcast", help="Broadcast a message")
    broadcast_parser.add_argument("message", help="Message to broadcast")
    broadcast_parser.add_argument("--status", help="Filter leads by status")

    args = parser.parse_args()

    if args.command == "start":
        print(f"🚀 Starting Munesh AI on {args.host}:{args.port}")
        uvicorn.run(
            "app.main:app",
            host=args.host,
            port=args.port,
            reload=args.reload,
        )
    elif args.command == "leads":
        _show_leads()
    elif args.command == "broadcast":
        _broadcast(args.message, args.status)
    else:
        parser.print_help()


def _show_leads() -> None:
    """Display all leads from the database."""
    from app.core.database import SessionLocal
    from app.services.crm import crm_service

    db = SessionLocal()
    try:
        leads = crm_service.get_all_leads(db)
        if not leads:
            print("No leads found.")
            return

        print(f"\n{'Phone':<20} {'Name':<20} {'Status':<15} {'Source':<10} {'Created'}")
        print("-" * 85)
        for lead in leads:
            print(
                f"{lead.phone:<20} "
                f"{(lead.name or 'N/A'):<20} "
                f"{lead.status.value:<15} "
                f"{lead.source:<10} "
                f"{lead.created_at}"
            )
        print(f"\nTotal: {len(leads)} leads")
    finally:
        db.close()


def _broadcast(message: str, status_filter: str | None) -> None:
    """Broadcast a message to leads."""
    import asyncio
    from app.core.database import SessionLocal
    from app.services.crm import crm_service
    from app.services.whatsapp import whatsapp_service

    db = SessionLocal()
    try:
        leads = crm_service.get_all_leads(db, status=status_filter)
        if not leads:
            print("No leads to broadcast to.")
            return

        print(f"Broadcasting to {len(leads)} leads...")

        async def send_all() -> None:
            for lead in leads:
                result = await whatsapp_service.send_text_message(lead.phone, message)
                status = "sent" if result.get("status") != "error" else "failed"
                print(f"  {lead.phone}: {status}")

        asyncio.run(send_all())
        print("Broadcast complete.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
