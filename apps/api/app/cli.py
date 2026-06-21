import argparse
import asyncio
import sys

from app.core.security import hash_password
from app.db.session import get_session_factory
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
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "create-admin":
        return asyncio.run(create_admin(args.email, args.password, args.update_password))

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
