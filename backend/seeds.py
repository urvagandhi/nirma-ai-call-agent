"""
Database Seeding Script — Initial Administrative User & Production Call Script Templates.

This script populates the database with:
1. Default system administrator credentials ('admin@nirmauni.ac.in').
2. The 6 standardized multilingual call script templates defined in the PRD:
   - Fee Reminder (Hindi)
   - Exam Notification (English)
   - Attendance Alert (Gujarati / Hindi)
   - Event Announcement (English)
   - Placement Notice (English)
   - General Inquiry (Multilingual)

Usage:
    python -m backend.seeds
"""

import asyncio
import logging
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import settings
from backend.database.models import Base, CallScript, StaffUser
from backend.database.session import async_engine, async_session_factory

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

INITIAL_TEMPLATES = [
    {
        "name": "Fee Reminder — Hindi",
        "category": "fee_reminder",
        "language": "hi",
        "opening_message": (
            "Namaste, main Nirma University se automated assistant bol raha hoon. "
            "Aapki semester fees ka payment abhi baaki hai. Kya aap iske baare mein baat kar sakte hain?"
        ),
        "system_prompt": (
            "You are a polite college fee reminder voice assistant of Nirma University speaking in Hindi. "
            "Your goal is to inform the student about their pending semester fee and inquire when they will pay. "
            "CRITICAL INSTRUCTIONS: "
            "1. Answer in maximum 2 short sentences (under 30 words). "
            "2. Never use bullet points, asterisks, formatting, or lists. This is a voice call. "
            "3. If the student confirms a payment date, acknowledge politely and conclude the call."
        ),
    },
    {
        "name": "Exam Schedule Notification — English",
        "category": "exam_notice",
        "language": "en",
        "opening_message": (
            "Hello, this is an automated notification from Nirma University Examination Cell. "
            "Your upcoming semester end examination timetable has been published on the student portal."
        ),
        "system_prompt": (
            "You are a professional examination coordinator voice assistant of Nirma University speaking in English. "
            "Your goal is to ensure the student is aware of their upcoming examination schedule and hall ticket availability. "
            "CRITICAL INSTRUCTIONS: "
            "1. Answer in maximum 2 short sentences (under 30 words). "
            "2. Never use bullet points, markdown, or lists. "
            "3. Answer basic questions about exam dates and portal downloads, then politely end the call."
        ),
    },
    {
        "name": "Attendance Alert — Gujarati",
        "category": "attendance_alert",
        "language": "gu",
        "opening_message": (
            "Namaste, hu Nirma University mathi automated call kari rahyo chhu. "
            "Aapni haajari current semester ma niyamit karta ochi chhe. Shu tame aa babate vat kari shako chho?"
        ),
        "system_prompt": (
            "You are an academic advisor voice assistant of Nirma University speaking in Gujarati. "
            "Your goal is to warn the student about their low attendance and inform them about university criteria. "
            "CRITICAL INSTRUCTIONS: "
            "1. Answer in maximum 2 short sentences (under 30 words) in clean Gujarati. "
            "2. Never use bullet points, markdown, or lists. "
            "3. Inquire politely about the reason for absence and advise meeting their faculty mentor."
        ),
    },
    {
        "name": "Event Announcement — English",
        "category": "event_announcement",
        "language": "en",
        "opening_message": (
            "Hello, this is an automated announcement from Nirma University. "
            "The annual technical symposium and cultural festival registration is now open."
        ),
        "system_prompt": (
            "You are an energetic event coordinator voice assistant of Nirma University speaking in English. "
            "Your goal is to inform students about campus fest registrations, key dates, and venue details. "
            "CRITICAL INSTRUCTIONS: "
            "1. Keep answers concise (max 2 short sentences, under 30 words). "
            "2. Never use bullet points or markdown symbols. "
            "3. Take confirmation if the student plans to participate."
        ),
    },
    {
        "name": "Campus Placement Drive — English",
        "category": "placement_notice",
        "language": "en",
        "opening_message": (
            "Hello, this is the Nirma University Corporate Relations and Placement Cell calling. "
            "An upcoming campus placement drive has been scheduled for eligible final year students."
        ),
        "system_prompt": (
            "You are a placement office voice assistant of Nirma University speaking in English. "
            "Your goal is to notify eligible students of company recruitment drives, eligibility, and reporting times. "
            "CRITICAL INSTRUCTIONS: "
            "1. Keep responses under 30 words (2 short sentences max). "
            "2. Avoid any markdown or symbols. "
            "3. Emphasize formal dress code and resume requirements."
        ),
    },
    {
        "name": "General Administrative Inquiry — Multilingual",
        "category": "general_inquiry",
        "language": "hi",
        "opening_message": (
            "Namaste, main Nirma University prashasan se automated assistant bol raha hoon. "
            "Main aapki sahayata ke liye uplabdh hoon. Aap kis vishay mein jaankari chahte hain?"
        ),
        "system_prompt": (
            "You are a helpful general administrative voice assistant of Nirma University capable of speaking in Hindi, Gujarati, or English. "
            "Answer student queries politely and concisely regarding university office hours, certificates, and student portal access. "
            "CRITICAL INSTRUCTIONS: "
            "1. Respond in the exact language the student uses (Hindi, Gujarati, or English). "
            "2. Maximum 2 short sentences per response (under 35 words). "
            "3. Never output markdown formatting or bullet points."
        ),
    },
]


async def seed_data(session: AsyncSession) -> None:
    """
    Seeds initial admin user and predefined call templates into the database.

    Args:
        session: Active asynchronous SQLAlchemy database session.
    """
    # 1. Seed Administrative User
    admin_email = "admin@nirmauni.ac.in"
    stmt = select(StaffUser).where(StaffUser.email == admin_email)
    result = await session.execute(stmt)
    existing_admin = result.scalar_one_or_none()

    if not existing_admin:
        admin_user = StaffUser(
            email=admin_email,
            name="Nirma System Administrator",
            role="admin",
            password_hash=pwd_context.hash("Admin@Nirma2026"),
            is_active=True,
        )
        session.add(admin_user)
        await session.flush()
        logger.info("Created default administrator: %s", admin_email)
        admin_id = admin_user.id
    else:
        logger.info("Administrator '%s' already exists.", admin_email)
        admin_id = existing_admin.id

    # 2. Seed Call Script Templates
    for template_data in INITIAL_TEMPLATES:
        stmt = select(CallScript).where(CallScript.name == template_data["name"])
        res = await session.execute(stmt)
        if not res.scalar_one_or_none():
            script = CallScript(
                name=template_data["name"],
                category=template_data["category"],
                language=template_data["language"],
                opening_message=template_data["opening_message"],
                system_prompt=template_data["system_prompt"],
                is_active=True,
                created_by=admin_id,
            )
            session.add(script)
            logger.info("Seeded template: %s", template_data["name"])

    await session.commit()
    logger.info("Database seeding completed successfully.")


async def main() -> None:
    """Entry point for database schema generation and initial seeding."""
    logger.info("Connecting to database: %s", settings.database_url)
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables verified/created.")

    async with async_session_factory() as session:
        await seed_data(session)


if __name__ == "__main__":
    asyncio.run(main())
