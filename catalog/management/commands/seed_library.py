from datetime import timedelta
from pathlib import Path
from textwrap import wrap

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.utils.text import slugify
from PIL import Image, ImageDraw, ImageFont

from accounts.models import Profile
from catalog.models import Book
from circulation.models import BookRequest, BorrowRecord, Notification


BOOKS = [
    {
        "title": "The Midnight Archive",
        "author": "Elena Vale",
        "isbn": "9780000001001",
        "genre": Book.Genre.FICTION,
        "category": "M",
        "publisher": "Northstar Press",
        "publication_year": 2022,
        "total_stock": 6,
        "description": "A literary mystery about a city library that remembers every book ever lost.",
    },
    {
        "title": "Practical Django Systems",
        "author": "Ravi Sen",
        "isbn": "9780000001002",
        "genre": Book.Genre.TECHNOLOGY,
        "category": "P",
        "publisher": "Signal House",
        "publication_year": 2025,
        "total_stock": 4,
        "description": "Patterns for building maintainable Django applications with clean models and fast interfaces.",
        "ebook_url": "https://docs.djangoproject.com/",
        "ebook_provider_label": "Django Documentation",
    },
    {
        "title": "Cosmos in Color",
        "author": "Mira Okafor",
        "isbn": "9780000001003",
        "genre": Book.Genre.SCIENCE,
        "category": "C",
        "publisher": "Aurora Learning",
        "publication_year": 2021,
        "total_stock": 5,
        "description": "A visual journey through astronomy, spectroscopy, and the hidden colors of deep space.",
    },
    {
        "title": "The Silk Road Ledger",
        "author": "Hana Qureshi",
        "isbn": "9780000001004",
        "genre": Book.Genre.HISTORY,
        "category": "S",
        "publisher": "Meridian Books",
        "publication_year": 2019,
        "total_stock": 3,
        "description": "Trade routes, letters, spices, and the accounting habits that connected empires.",
    },
    {
        "title": "Quiet Algorithms",
        "author": "Theo Marin",
        "isbn": "9780000001005",
        "genre": Book.Genre.PHILOSOPHY,
        "category": "Q",
        "publisher": "Civic Mind",
        "publication_year": 2024,
        "total_stock": 2,
        "description": "Essays on computation, attention, and how technology changes public life.",
    },
    {
        "title": "Botany for Balcony Worlds",
        "author": "Iris Banerjee",
        "isbn": "9780000001006",
        "genre": Book.Genre.SCIENCE,
        "category": "B",
        "publisher": "Green Lantern",
        "publication_year": 2020,
        "total_stock": 7,
        "description": "A compact guide to small-space ecology, plant care, and edible balcony gardens.",
    },
    {
        "title": "Atlas of Lost Instruments",
        "author": "Jon Bell",
        "isbn": "9780000001007",
        "genre": Book.Genre.ART,
        "category": "A",
        "publisher": "Blue Note Studio",
        "publication_year": 2018,
        "total_stock": 3,
        "description": "Illustrated stories of rare instruments and the musicians who kept them alive.",
    },
    {
        "title": "Ada Lovelace: A Patterned Mind",
        "author": "Sofia Reed",
        "isbn": "9780000001008",
        "genre": Book.Genre.BIOGRAPHY,
        "category": "A",
        "publisher": "Longform Lives",
        "publication_year": 2023,
        "total_stock": 5,
        "description": "A biography of Ada Lovelace focused on imagination, mathematics, and early computing.",
    },
    {
        "title": "Children of the Moonlit Map",
        "author": "Nico Armas",
        "isbn": "9780000001009",
        "genre": Book.Genre.CHILDREN,
        "category": "C",
        "publisher": "Tiny Compass",
        "publication_year": 2022,
        "total_stock": 8,
        "description": "A playful adventure for young readers who enjoy puzzles, maps, and brave friendships.",
    },
    {
        "title": "Desk Reference for Curious Minds",
        "author": "Astra Editors",
        "isbn": "9780000001010",
        "genre": Book.Genre.REFERENCE,
        "category": "D",
        "publisher": "Astra Library",
        "publication_year": 2026,
        "total_stock": 4,
        "description": "A quick reference full of timelines, conversion tables, reading lists, and research prompts.",
    },
    {
        "title": "Future Cities Fieldbook",
        "author": "Lin Torres",
        "isbn": "9780000001011",
        "genre": Book.Genre.TECHNOLOGY,
        "category": "F",
        "publisher": "Urban Futures",
        "publication_year": 2024,
        "total_stock": 3,
        "description": "A practical fieldbook for transport, climate adaptation, housing, and civic data.",
    },
    {
        "title": "Letters from the Monsoon",
        "author": "Anaya Rao",
        "isbn": "9780000001012",
        "genre": Book.Genre.FICTION,
        "category": "L",
        "publisher": "Rainlight",
        "publication_year": 2020,
        "total_stock": 6,
        "description": "An intimate novel told through letters crossing coastlines, seasons, and generations.",
    },
]

PALETTES = [
    ("#1f6f5b", "#285f8f"),
    ("#b64b57", "#c47a28"),
    ("#423b77", "#1f6f5b"),
    ("#285f8f", "#6d6b3f"),
    ("#7a4b33", "#2f6a59"),
]


class Command(BaseCommand):
    help = "Seed sample users, books, covers, loans, requests, and notifications."

    def handle(self, *args, **options):
        users = self.create_users()
        books = self.create_books(users["librarian"])
        self.create_circulation(users, books)
        self.stdout.write(self.style.SUCCESS("Seed data ready."))
        self.stdout.write("Admin: admin / AdminPass123!")
        self.stdout.write("Librarian: librarian / LibraryPass123!")
        self.stdout.write("Member: maya / MemberPass123!")

    def create_users(self):
        User = get_user_model()
        definitions = [
            ("admin", "admin@astra.test", "Admin", "One", "AdminPass123!", Profile.Role.ADMIN, True, True),
            (
                "librarian",
                "librarian@astra.test",
                "Lina",
                "Stacks",
                "LibraryPass123!",
                Profile.Role.LIBRARIAN,
                True,
                False,
            ),
            ("maya", "maya@astra.test", "Maya", "Kapoor", "MemberPass123!", Profile.Role.MEMBER, False, False),
            ("noah", "noah@astra.test", "Noah", "Stone", "MemberPass123!", Profile.Role.MEMBER, False, False),
            ("li", "li@astra.test", "Li", "Chen", "MemberPass123!", Profile.Role.MEMBER, False, False),
        ]
        users = {}
        for username, email, first, last, password, role, is_staff, is_superuser in definitions:
            user, _ = User.objects.update_or_create(
                username=username,
                defaults={
                    "email": email,
                    "first_name": first,
                    "last_name": last,
                    "is_staff": is_staff,
                    "is_superuser": is_superuser,
                    "is_active": True,
                },
            )
            user.set_password(password)
            user.save()
            user.profile.role = role
            user.profile.save(update_fields=["role"])
            users[username] = user
        return users

    def create_books(self, creator):
        books = {}
        for index, book_data in enumerate(BOOKS):
            cover_name = self.make_cover(book_data["title"], book_data["author"], index)
            defaults = {
                "title": book_data["title"],
                "author": book_data["author"],
                "description": book_data["description"],
                "genre": book_data["genre"],
                "category": book_data["category"],
                "publisher": book_data["publisher"],
                "publication_year": book_data["publication_year"],
                "total_stock": book_data["total_stock"],
                "available_stock": book_data["total_stock"],
                "ebook_url": book_data.get("ebook_url", ""),
                "ebook_provider_label": book_data.get("ebook_provider_label", ""),
                "created_by": creator,
                "cover_image": cover_name,
            }
            book, _ = Book.objects.update_or_create(isbn=book_data["isbn"], defaults=defaults)
            books[book.isbn] = book
        return books

    def create_circulation(self, users, books):
        BorrowRecord.objects.filter(notes__startswith="Seed sample").delete()
        BookRequest.objects.filter(note__startswith="Seed sample").delete()
        Notification.objects.filter(message__startswith="Seed sample").delete()

        today = timezone.localdate()
        loans = [
            ("maya", "9780000001001", today - timedelta(days=4), today + timedelta(days=10), None),
            ("maya", "9780000001002", today - timedelta(days=18), today - timedelta(days=4), None),
            ("noah", "9780000001003", today - timedelta(days=8), today + timedelta(days=6), None),
            ("li", "9780000001004", today - timedelta(days=28), today - timedelta(days=14), today - timedelta(days=3)),
            ("li", "9780000001008", today - timedelta(days=11), today + timedelta(days=3), None),
        ]
        for username, isbn, issue_date, due_date, return_date in loans:
            BorrowRecord.objects.create(
                user=users[username],
                book=books[isbn],
                issued_by=users["librarian"],
                issue_date=issue_date,
                due_date=due_date,
                return_date=return_date,
                status=BorrowRecord.Status.RETURNED if return_date else BorrowRecord.Status.BORROWED,
                notes="Seed sample loan",
            )

        for book in books.values():
            active_count = BorrowRecord.objects.filter(
                book=book,
                status=BorrowRecord.Status.BORROWED,
                return_date__isnull=True,
            ).count()
            book.available_stock = max(book.total_stock - active_count, 0)
            book.save(update_fields=["available_stock", "updated_at"])

        BookRequest.objects.create(
            user=users["maya"],
            book=books["9780000001005"],
            requested_title=books["9780000001005"].title,
            requested_author=books["9780000001005"].author,
            genre=books["9780000001005"].genre,
            note="Seed sample request: please reserve the next copy.",
        )
        BookRequest.objects.create(
            user=users["noah"],
            requested_title="Designing Data-Driven Libraries",
            requested_author="Cam Ortiz",
            genre=Book.Genre.TECHNOLOGY,
            note="Seed sample request: suggested acquisition.",
            status=BookRequest.Status.APPROVED,
            reviewed_by=users["librarian"],
            reviewed_at=timezone.now(),
            admin_notes="Approved for the next acquisition round.",
        )
        Notification.objects.create(
            user=users["maya"],
            kind=Notification.Kind.FINE,
            message="Seed sample alert: Practical Django Systems is overdue.",
            link="/dashboard/me/",
        )

    def make_cover(self, title, author, index):
        covers_dir = Path(settings.MEDIA_ROOT) / "covers"
        covers_dir.mkdir(parents=True, exist_ok=True)
        filename = f"{slugify(title)}.png"
        path = covers_dir / filename
        if path.exists():
            return f"covers/{filename}"

        image = Image.new("RGB", (720, 1080), PALETTES[index % len(PALETTES)][0])
        draw = ImageDraw.Draw(image)
        base, accent = PALETTES[index % len(PALETTES)]
        for y in range(0, 1080, 18):
            ratio = y / 1080
            color = self.blend(base, accent, ratio)
            draw.rectangle((0, y, 720, y + 18), fill=color)

        draw.rectangle((56, 56, 664, 1024), outline="#fffdf7", width=6)
        draw.rectangle((86, 86, 634, 994), outline="#fffdf7", width=2)
        font_title = ImageFont.load_default(size=58)
        font_author = ImageFont.load_default(size=34)
        y = 250
        for line in wrap(title, 14):
            draw.text((110, y), line, fill="#fffdf7", font=font_title)
            y += 68
        draw.text((110, 850), author.upper(), fill="#fffdf7", font=font_author)
        draw.rectangle((110, 908, 390, 918), fill="#fffdf7")
        image.save(path)
        return f"covers/{filename}"

    def blend(self, start, end, ratio):
        start_rgb = tuple(int(start[i : i + 2], 16) for i in (1, 3, 5))
        end_rgb = tuple(int(end[i : i + 2], 16) for i in (1, 3, 5))
        mixed = tuple(int(a + (b - a) * ratio) for a, b in zip(start_rgb, end_rgb))
        return mixed
