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
from catalog.models import Book, BookReview
from circulation.models import BookRequest, BorrowRecord, Notification, PaymentTransaction


BOOKS = [
    {
        "title": "Pride and Prejudice",
        "author": "Jane Austen",
        "isbn": "PG-1342",
        "genre": Book.Genre.FICTION,
        "category": "P",
        "publisher": "T. Egerton / Project Gutenberg",
        "publication_year": 1813,
        "total_stock": 6,
        "description": "A classic English novel about Elizabeth Bennet, first impressions, social pressure, and the slow correction of judgment.",
        "ebook_url": "https://www.gutenberg.org/ebooks/1342.html.images",
        "ebook_provider_label": "Project Gutenberg",
        "source_url": "https://www.gutenberg.org/ebooks/1342",
        "digital_copy_format": "HTML / EPUB",
        "external_cover_url": "https://www.gutenberg.org/cache/epub/1342/pg1342.cover.medium.jpg",
    },
    {
        "title": "Frankenstein; Or, The Modern Prometheus",
        "author": "Mary Wollstonecraft Shelley",
        "isbn": "PG-84",
        "genre": Book.Genre.SCI_FI,
        "category": "F",
        "publisher": "Lackington, Hughes, Harding, Mavor & Jones / Project Gutenberg",
        "publication_year": 1818,
        "total_stock": 4,
        "description": "A foundational Gothic science-fiction novel about creation, responsibility, alienation, and ambition.",
        "ebook_url": "https://www.gutenberg.org/ebooks/84.html.images",
        "ebook_provider_label": "Project Gutenberg",
        "source_url": "https://www.gutenberg.org/ebooks/84",
        "digital_copy_format": "HTML / EPUB",
        "external_cover_url": "https://www.gutenberg.org/cache/epub/84/pg84.cover.medium.jpg",
    },
    {
        "title": "Alice's Adventures in Wonderland",
        "author": "Lewis Carroll",
        "isbn": "PG-928",
        "genre": Book.Genre.CHILDREN,
        "category": "A",
        "publisher": "Macmillan / Project Gutenberg",
        "publication_year": 1865,
        "total_stock": 5,
        "description": "A landmark work of children's fantasy following Alice through a surreal world of logic games and impossible characters.",
        "ebook_url": "https://www.gutenberg.org/ebooks/928.html.images",
        "ebook_provider_label": "Project Gutenberg",
        "source_url": "https://www.gutenberg.org/ebooks/928",
        "digital_copy_format": "HTML / EPUB",
        "external_cover_url": "https://www.gutenberg.org/cache/epub/928/pg928.cover.medium.jpg",
    },
    {
        "title": "Dracula",
        "author": "Bram Stoker",
        "isbn": "PG-345",
        "genre": Book.Genre.FICTION,
        "category": "D",
        "publisher": "Archibald Constable and Company / Project Gutenberg",
        "publication_year": 1897,
        "total_stock": 3,
        "description": "An epistolary Gothic novel that helped define the modern vampire myth through diaries, letters, and newspaper fragments.",
        "ebook_url": "https://www.gutenberg.org/ebooks/345.html.images",
        "ebook_provider_label": "Project Gutenberg",
        "source_url": "https://www.gutenberg.org/ebooks/345",
        "digital_copy_format": "HTML / EPUB",
        "external_cover_url": "https://www.gutenberg.org/cache/epub/345/pg345.cover.medium.jpg",
    },
    {
        "title": "The War of the Worlds",
        "author": "H. G. Wells",
        "isbn": "PG-36",
        "genre": Book.Genre.SCI_FI,
        "category": "W",
        "publisher": "William Heinemann / Project Gutenberg",
        "publication_year": 1898,
        "total_stock": 2,
        "description": "A science-fiction invasion novel that imagines Martian technology overwhelming Victorian England.",
        "ebook_url": "https://www.gutenberg.org/ebooks/36.html.images",
        "ebook_provider_label": "Project Gutenberg",
        "source_url": "https://www.gutenberg.org/ebooks/36",
        "digital_copy_format": "HTML / EPUB",
        "external_cover_url": "https://www.gutenberg.org/cache/epub/36/pg36.cover.medium.jpg",
    },
    {
        "title": "A Princess of Mars",
        "author": "Edgar Rice Burroughs",
        "isbn": "PG-62",
        "genre": Book.Genre.SCI_FI,
        "category": "P",
        "publisher": "A. C. McClurg / Project Gutenberg",
        "publication_year": 1912,
        "total_stock": 7,
        "description": "The first Barsoom novel, sending John Carter to Mars for planetary adventure, politics, and romance.",
        "ebook_url": "https://www.gutenberg.org/ebooks/62.html.images",
        "ebook_provider_label": "Project Gutenberg",
        "source_url": "https://www.gutenberg.org/ebooks/62",
        "digital_copy_format": "HTML / EPUB",
        "external_cover_url": "https://www.gutenberg.org/cache/epub/62/pg62.cover.medium.jpg",
    },
    {
        "title": "Moby-Dick; Or, The Whale",
        "author": "Herman Melville",
        "isbn": "PG-2701",
        "genre": Book.Genre.FICTION,
        "category": "M",
        "publisher": "Harper & Brothers / Project Gutenberg",
        "publication_year": 1851,
        "total_stock": 3,
        "description": "A sprawling American novel about obsession, whaling, language, and Captain Ahab's pursuit of the white whale.",
        "ebook_url": "https://www.gutenberg.org/ebooks/2701.html.images",
        "ebook_provider_label": "Project Gutenberg",
        "source_url": "https://www.gutenberg.org/ebooks/2701",
        "digital_copy_format": "HTML / EPUB",
        "external_cover_url": "https://www.gutenberg.org/cache/epub/2701/pg2701.cover.medium.jpg",
    },
    {
        "title": "The Adventures of Sherlock Holmes",
        "author": "Arthur Conan Doyle",
        "isbn": "PG-1661",
        "genre": Book.Genre.FICTION,
        "category": "S",
        "publisher": "George Newnes / Project Gutenberg",
        "publication_year": 1892,
        "total_stock": 5,
        "description": "A short-story collection introducing many of Sherlock Holmes's best-known cases and deductive methods.",
        "ebook_url": "https://www.gutenberg.org/ebooks/1661.html.images",
        "ebook_provider_label": "Project Gutenberg",
        "source_url": "https://www.gutenberg.org/ebooks/1661",
        "digital_copy_format": "HTML / EPUB",
        "external_cover_url": "https://www.gutenberg.org/cache/epub/1661/pg1661.cover.medium.jpg",
    },
    {
        "title": "Structure and Interpretation of Computer Programs",
        "author": "Harold Abelson, Gerald Jay Sussman, and Julie Sussman",
        "isbn": "9780262510875",
        "genre": Book.Genre.COMPUTER_SCIENCE,
        "category": "S",
        "publisher": "MIT Press",
        "publication_year": 1996,
        "total_stock": 8,
        "description": "A classic computer science text on abstraction, interpreters, symbolic data, streams, and program structure.",
        "ebook_url": "https://mitpress.mit.edu/9780262510875/structure-and-interpretation-of-computer-programs/",
        "ebook_provider_label": "MIT Press",
        "pdf_url": "https://web.mit.edu/6.001/6.037/sicp.pdf",
        "source_url": "https://mitpress.mit.edu/9780262510875/structure-and-interpretation-of-computer-programs/",
        "digital_copy_format": "PDF / Open Access",
        "external_cover_url": "https://covers.openlibrary.org/b/isbn/9780262510875-L.jpg",
    },
    {
        "title": "Think Python: How to Think Like a Computer Scientist",
        "author": "Allen B. Downey",
        "isbn": "9781491939369",
        "genre": Book.Genre.COMPUTER_SCIENCE,
        "category": "T",
        "publisher": "Green Tea Press",
        "publication_year": 2012,
        "total_stock": 4,
        "description": "A beginner-friendly programming book that introduces Python through core concepts, functions, recursion, and objects.",
        "ebook_url": "https://greenteapress.com/wp/think-python-2e/",
        "ebook_provider_label": "Green Tea Press",
        "pdf_url": "https://greenteapress.com/thinkpython2/thinkpython2.pdf",
        "source_url": "https://greenteapress.com/wp/think-python-2e/",
        "digital_copy_format": "PDF / HTML",
        "external_cover_url": "https://covers.openlibrary.org/b/isbn/9781491939369-L.jpg",
    },
    {
        "title": "Think Complexity",
        "author": "Allen B. Downey",
        "isbn": "9781492040200",
        "genre": Book.Genre.COMPUTER_SCIENCE,
        "category": "T",
        "publisher": "Green Tea Press",
        "publication_year": 2018,
        "total_stock": 3,
        "description": "An applied introduction to complexity science using Python, networks, cellular automata, fractals, and agent-based models.",
        "ebook_url": "https://greenteapress.com/wp/think-complexity-2e/",
        "ebook_provider_label": "Green Tea Press",
        "pdf_url": "https://greenteapress.com/complexity2/thinkcomplexity2.pdf",
        "source_url": "https://greenteapress.com/wp/think-complexity-2e/",
        "digital_copy_format": "PDF / HTML",
        "external_cover_url": "https://covers.openlibrary.org/b/isbn/9781492040200-L.jpg",
    },
    {
        "title": "Introduction to Python Programming",
        "author": "Udayan Das, Aubrey Lawson, Chris Mayfield, and Narges Norouzi",
        "isbn": "9781961584457",
        "genre": Book.Genre.COMPUTER_SCIENCE,
        "category": "I",
        "publisher": "OpenStax",
        "publication_year": 2024,
        "total_stock": 6,
        "description": "An OpenStax programming textbook covering Python fundamentals, data structures, modules, classes, and data science foundations.",
        "ebook_url": "https://openstax.org/books/introduction-python-programming/pages/1-introduction",
        "ebook_provider_label": "OpenStax",
        "source_url": "https://openstax.org/books/introduction-python-programming/pages/1-introduction",
        "digital_copy_format": "Web / PDF via OpenStax",
        "external_cover_url": "https://covers.openlibrary.org/b/isbn/9781961584457-L.jpg",
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
        self.cleanup_seed_data()
        books = self.create_books(users["librarian"])
        self.create_circulation(users, books)
        self.create_reviews(users, books)
        self.stdout.write(self.style.SUCCESS("Seed data ready."))
        self.stdout.write("Admin: admin / AdminPass123!")
        self.stdout.write("Librarian: librarian / LibraryPass123!")
        self.stdout.write("Member: maya / MemberPass123!")

    def cleanup_seed_data(self):
        PaymentTransaction.objects.filter(note__startswith="Seed sample").delete()
        BorrowRecord.objects.filter(notes__startswith="Seed sample").delete()
        BookRequest.objects.filter(note__startswith="Seed sample").delete()
        Notification.objects.filter(message__startswith="Seed sample").delete()
        BookReview.objects.filter(body__startswith="Seed sample").delete()
        Book.objects.filter(isbn__startswith="978000000").delete()

    def create_users(self):
        User = get_user_model()
        definitions = [
            ("admin", "admin@bookly.test", "Admin", "One", "AdminPass123!", Profile.Role.ADMIN, True, True),
            (
                "librarian",
                "librarian@bookly.test",
                "Lina",
                "Stacks",
                "LibraryPass123!",
                Profile.Role.LIBRARIAN,
                True,
                False,
            ),
            ("maya", "maya@bookly.test", "Maya", "Kapoor", "MemberPass123!", Profile.Role.MEMBER, False, False),
            ("noah", "noah@bookly.test", "Noah", "Stone", "MemberPass123!", Profile.Role.MEMBER, False, False),
            ("li", "li@bookly.test", "Li", "Chen", "MemberPass123!", Profile.Role.MEMBER, False, False),
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
            cover_name = "" if book_data.get("external_cover_url") else self.make_cover(
                book_data["title"],
                book_data["author"],
                index,
            )
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
                "pdf_url": book_data.get("pdf_url", ""),
                "source_url": book_data.get("source_url", ""),
                "digital_copy_format": book_data.get("digital_copy_format", "Web"),
                "external_cover_url": book_data.get("external_cover_url", ""),
                "created_by": creator,
                "cover_image": cover_name,
            }
            book, _ = Book.objects.update_or_create(isbn=book_data["isbn"], defaults=defaults)
            books[book.isbn] = book
        return books

    def create_circulation(self, users, books):
        today = timezone.localdate()
        loans = [
            ("maya", "PG-1342", today - timedelta(days=4), today + timedelta(days=10), None),
            ("maya", "9781491939369", today - timedelta(days=18), today - timedelta(days=4), None),
            ("noah", "PG-84", today - timedelta(days=8), today + timedelta(days=6), None),
            ("li", "9780262510875", today - timedelta(days=28), today - timedelta(days=14), today - timedelta(days=3)),
            ("li", "PG-1661", today - timedelta(days=11), today + timedelta(days=3), None),
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
            book=books["PG-36"],
            requested_title=books["PG-36"].title,
            requested_author=books["PG-36"].author,
            genre=books["PG-36"].genre,
            note="Seed sample request: please reserve the next copy.",
        )
        BookRequest.objects.create(
            user=users["noah"],
            requested_title="Clean Code",
            requested_author="Robert C. Martin",
            genre=Book.Genre.COMPUTER_SCIENCE,
            note="Seed sample request: suggested acquisition.",
            status=BookRequest.Status.APPROVED,
            reviewed_by=users["librarian"],
            reviewed_at=timezone.now(),
            admin_notes="Approved for the next acquisition round.",
        )
        Notification.objects.create(
            user=users["maya"],
            kind=Notification.Kind.FINE,
            message="Seed sample alert: Think Python is overdue.",
            link="/dashboard/me/",
        )
        overdue_record = BorrowRecord.objects.filter(user=users["maya"], book=books["9781491939369"]).first()
        if overdue_record:
            PaymentTransaction.objects.create(
                user=users["maya"],
                borrow_record=overdue_record,
                amount=overdue_record.fine_due,
                reference="BKLY-SEED-001",
                note="Seed sample QR dues payment",
            )

    def create_reviews(self, users, books):
        reviews = [
            ("maya", "PG-1342", 5, "Still sharp", "Seed sample review: witty, social, and much funnier than expected."),
            ("noah", "PG-84", 5, "Essential sci-fi roots", "Seed sample review: the ethical questions still feel modern."),
            ("li", "9780262510875", 5, "Hard but worth it", "Seed sample review: dense, elegant, and excellent for abstraction."),
            ("maya", "9781491939369", 4, "Great first Python book", "Seed sample review: very approachable for beginners."),
            ("noah", "PG-36", 4, "Classic invasion story", "Seed sample review: fast, tense, and historically important."),
        ]
        for username, isbn, rating, title, body in reviews:
            BookReview.objects.update_or_create(
                user=users[username],
                book=books[isbn],
                defaults={"rating": rating, "title": title, "body": body, "is_public": True},
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
