import argparse
import asyncio
import sys

from app.db.session import get_session_factory
from app.services.demo_seed import (
    DEMO_ADMIN_EMAIL_DEFAULT,
    DEMO_ADMIN_PASSWORD_DEFAULT,
    run_demo_seed,
)
from app.services.users import create_user, get_user_by_email, update_user_password


async def create_admin(email: str, password: str, update_password: bool) -> int:
    session_factory = get_session_factory()
    async with session_factory() as session:
        existing_user = await get_user_by_email(session, email)

        if existing_user is not None and not update_password:
            print(f"Admin user already exists for {email}. Use --update-password to reset password.")
            return 1

        if existing_user is not None:
            await update_user_password(session, existing_user, password)
            print(f"Updated password for admin user {email}.")
            return 0

        await create_user(session, email, password)
        print(f"Created admin user {email}.")
        return 0


async def seed_demo(
    admin_email: str,
    admin_password: str,
    reset_demo_data: bool,
) -> int:
    session_factory = get_session_factory()
    async with session_factory() as session:
        result = await run_demo_seed(
            session,
            admin_email=admin_email,
            admin_password=admin_password,
            reset_demo_data=reset_demo_data,
        )

    print("Demo seed completed.")
    print(f"  Admin user: {result.admin_email}")
    print(f"  Profile items: {result.profile_items}")
    print(f"  Career records: {result.career_records}")
    print(f"  Documents: {result.documents}")
    print(f"  Document chunks: {result.document_chunks}")
    print(f"  Conversations: {result.conversations}")
    print(f"  Retrieval logs: {result.retrieval_logs}")
    print(f"  Unanswered prompts: {result.unanswered_prompts}")
    print(f"  Leads: {result.leads}")
    print(f"  Tool calls: {result.tool_calls}")
    print(f"  Settings: {result.settings}")
    if result.reset_applied:
        print("  Reset: demo data was cleared before seeding.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Interactive Career Profile API CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    create_admin_parser = subparsers.add_parser("create-admin", help="Create or update an admin user")
    create_admin_parser.add_argument("--email", required=True, help="Admin email address")
    create_admin_parser.add_argument("--password", required=True, help="Admin password")
    create_admin_parser.add_argument(
        "--update-password",
        action="store_true",
        help="Update password when the admin user already exists",
    )

    seed_demo_parser = subparsers.add_parser(
        "seed-demo",
        help="Seed idempotent demo data for local verification",
    )
    seed_demo_parser.add_argument(
        "--admin-email",
        default=DEMO_ADMIN_EMAIL_DEFAULT,
        help="Demo admin email address",
    )
    seed_demo_parser.add_argument(
        "--admin-password",
        default=DEMO_ADMIN_PASSWORD_DEFAULT,
        help="Demo admin password",
    )
    seed_demo_parser.add_argument(
        "--reset-demo-data",
        action="store_true",
        help="Clear previously seeded demo records before seeding again",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "create-admin":
        return asyncio.run(create_admin(args.email, args.password, args.update_password))

    if args.command == "seed-demo":
        return asyncio.run(
            seed_demo(
                args.admin_email,
                args.admin_password,
                args.reset_demo_data,
            )
        )

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
