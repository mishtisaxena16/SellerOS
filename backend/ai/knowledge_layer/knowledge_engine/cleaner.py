# """
# SellerOS Knowledge Engine - Document Cleaner

# Responsible for preprocessing raw markdown documents before
# chunking and metadata generation.

# Pipeline:

# Raw Markdown
#     ↓
# Unicode Normalization
#     ↓
# OCR Cleanup
#     ↓
# Navigation Removal
#     ↓
# Heading Normalization
#     ↓
# Table Normalization
#     ↓
# Markdown Normalization
#     ↓
# Clean Markdown

# Author: SellerOS
# Version: 1.0
# """

# from __future__ import annotations

# import re
# import unicodedata
# from dataclasses import dataclass
# from typing import Dict


# @dataclass(slots=True)
# class CleaningReport:
#     """
#     Stores cleaning statistics for a document.
#     """

#     original_characters: int
#     cleaned_characters: int

#     unicode_normalizations: int = 0
#     navigation_blocks_removed: int = 0
#     headings_normalized: int = 0
#     tables_normalized: int = 0
#     ocr_fixes_applied: int = 0

#     @property
#     def characters_removed(self) -> int:
#         return self.original_characters - self.cleaned_characters

#     def to_dict(self) -> Dict[str, int]:
#         return {
#             "original_characters": self.original_characters,
#             "cleaned_characters": self.cleaned_characters,
#             "characters_removed": self.characters_removed,
#             "unicode_normalizations": self.unicode_normalizations,
#             "navigation_blocks_removed": self.navigation_blocks_removed,
#             "headings_normalized": self.headings_normalized,
#             "tables_normalized": self.tables_normalized,
#             "ocr_fixes_applied": self.ocr_fixes_applied,
#         }


# class MarkdownCleaner:
#     """
#     Main markdown cleaning service.
#     """

#     NAVIGATION_PATTERNS = [
#         r"(?im)^home\s*$",
#         r"(?im)^back\s*$",
#         r"(?im)^next\s*$",
#         r"(?im)^previous\s*$",
#         r"(?im)^contents\s*$",
#         r"(?im)^table of contents\s*$",
#     ]

#     OCR_REPLACEMENTS = {
#         "ﬁ": "fi",
#         "ﬂ": "fl",
#         "—": "-",
#         "–": "-",
#         "\u00a0": " ",
#     }

#     def clean(
#         self,
#         markdown_text: str,
#     ) -> tuple[str, CleaningReport]:
#         """
#         Execute complete cleaning pipeline.

#         Parameters
#         ----------
#         markdown_text : str
#             Raw markdown document.

#         Returns
#         -------
#         tuple[str, CleaningReport]
#             Cleaned markdown and cleaning report.
#         """

#         report = CleaningReport(
#             original_characters=len(markdown_text),
#             cleaned_characters=0,
#         )

#         text = markdown_text

#         text = self._normalize_unicode(text, report)
#         text = self._clean_ocr_artifacts(text, report)
#         text = self._remove_navigation(text, report)
#         text = self._normalize_headings(text, report)
#         text = self._normalize_tables(text, report)
#         text = self._normalize_markdown(text)

#         report.cleaned_characters = len(text)

#         return text, report

#     def _normalize_unicode(
#         self,
#         text: str,
#         report: CleaningReport,
#     ) -> str:
#         """
#         Normalize unicode representation.
#         """

#         normalized = unicodedata.normalize("NFKC", text)

#         if normalized != text:
#             report.unicode_normalizations += 1

#         return normalized

#     def _clean_ocr_artifacts(
#         self,
#         text: str,
#         report: CleaningReport,
#     ) -> str:
#         """
#         Fix common OCR extraction artifacts.
#         """

#         for source, target in self.OCR_REPLACEMENTS.items():
#             occurrences = text.count(source)

#             if occurrences:
#                 report.ocr_fixes_applied += occurrences

#             text = text.replace(source, target)

#         return text

#     def _remove_navigation(
#         self,
#         text: str,
#         report: CleaningReport,
#     ) -> str:
#         """
#         Remove common navigation/menu elements.
#         """

#         for pattern in self.NAVIGATION_PATTERNS:
#             matches = re.findall(pattern, text)

#             if matches:
#                 report.navigation_blocks_removed += len(matches)

#             text = re.sub(pattern, "", text)

#         return text

#     def _normalize_headings(
#         self,
#         text: str,
#         report: CleaningReport,
#     ) -> str:
#         """
#         Normalize markdown headings.

#         Examples:
#             ####Title
#             becomes
#             #### Title
#         """

#         heading_pattern = re.compile(
#             r"^(#{1,6})([^\s#].*)$",
#             flags=re.MULTILINE,
#         )

#         matches = heading_pattern.findall(text)

#         if matches:
#             report.headings_normalized += len(matches)

#         return heading_pattern.sub(r"\1 \2", text)

#     def _normalize_tables(
#         self,
#         text: str,
#         report: CleaningReport,
#     ) -> str:
#         """
#         Normalize markdown table spacing.
#         """

#         lines = []

#         for line in text.splitlines():

#             if "|" in line:
#                 report.tables_normalized += 1

#                 cells = [cell.strip() for cell in line.split("|")]
#                 line = " | ".join(cells)

#             lines.append(line)

#         return "\n".join(lines)

#     @staticmethod
#     def _normalize_markdown(text: str) -> str:
#         """
#         Final markdown cleanup.
#         """

#         text = re.sub(r"\n{3,}", "\n\n", text)
#         text = re.sub(r"[ \t]+$", "", text, flags=re.MULTILINE)
#         text = re.sub(r"[ \t]{2,}", " ", text)

#         return text.strip()


"""
SellerOS Knowledge Engine - Document Cleaner

Responsible for preprocessing raw markdown documents before
chunking and metadata generation.

Pipeline:

Raw Markdown
    ↓
Unicode Normalization
    ↓
OCR Cleanup
    ↓
HTML Cleanup
    ↓
Navigation Removal
    ↓
Heading Normalization
    ↓
Table Normalization
    ↓
Markdown Normalization
    ↓
Clean Markdown

Author: SellerOS
Version: 1.1
"""

from __future__ import annotations

import re
import unicodedata

from dataclasses import dataclass
from typing import Dict


# ==========================================================
# CLEANING REPORT
# ==========================================================

@dataclass(slots=True)
class CleaningReport:
    """
    Stores cleaning statistics for a document.
    """

    original_characters: int
    cleaned_characters: int

    unicode_normalizations: int = 0
    navigation_blocks_removed: int = 0
    headings_normalized: int = 0
    tables_normalized: int = 0
    ocr_fixes_applied: int = 0
    html_elements_removed: int = 0

    @property
    def characters_removed(self) -> int:
        return (
            self.original_characters
            - self.cleaned_characters
        )

    def to_dict(self) -> Dict[str, int]:
        return {
            "original_characters": self.original_characters,
            "cleaned_characters": self.cleaned_characters,
            "characters_removed": self.characters_removed,
            "unicode_normalizations": self.unicode_normalizations,
            "navigation_blocks_removed": self.navigation_blocks_removed,
            "headings_normalized": self.headings_normalized,
            "tables_normalized": self.tables_normalized,
            "ocr_fixes_applied": self.ocr_fixes_applied,
            "html_elements_removed": self.html_elements_removed,
        }


# ==========================================================
# MARKDOWN CLEANER
# ==========================================================

class MarkdownCleaner:
    """
    Main markdown cleaning service.
    """

    NAVIGATION_PATTERNS = [
        r"(?im)^home\s*$",
        r"(?im)^back\s*$",
        r"(?im)^next\s*$",
        r"(?im)^previous\s*$",
        r"(?im)^contents\s*$",
        r"(?im)^table of contents\s*$",
    ]

    OCR_REPLACEMENTS = {
        "ﬁ": "fi",
        "ﬂ": "fl",
        "—": "-",
        "–": "-",
        "\u00a0": " ",
    }

    HTML_ENTITY_REPLACEMENTS = {
        "&lt;": "<",
        "&gt;": ">",
        "&amp;": "&",
        "&quot;": '"',
        "&#39;": "'",
    }

    def clean(
        self,
        markdown_text: str,
    ) -> tuple[str, CleaningReport]:
        """
        Execute complete cleaning pipeline.
        """

        report = CleaningReport(
            original_characters=len(markdown_text),
            cleaned_characters=0,
        )

        text = markdown_text

        text = self._normalize_unicode(text, report)
        text = self._clean_ocr_artifacts(text, report)
        text = self._remove_html_artifacts(text, report)
        text = self._remove_navigation(text, report)
        text = self._normalize_headings(text, report)
        text = self._normalize_tables(text, report)
        text = self._normalize_markdown(text)

        report.cleaned_characters = len(text)

        return text, report

    # ======================================================
    # UNICODE NORMALIZATION
    # ======================================================

    def _normalize_unicode(
        self,
        text: str,
        report: CleaningReport,
    ) -> str:

        normalized = unicodedata.normalize(
            "NFKC",
            text,
        )

        if normalized != text:
            report.unicode_normalizations += 1

        return normalized

    # ======================================================
    # OCR CLEANUP
    # ======================================================

    def _clean_ocr_artifacts(
        self,
        text: str,
        report: CleaningReport,
    ) -> str:

        for source, target in self.OCR_REPLACEMENTS.items():

            occurrences = text.count(source)

            if occurrences:
                report.ocr_fixes_applied += occurrences

            text = text.replace(
                source,
                target,
            )

        return text

    # ======================================================
    # HTML CLEANUP
    # ======================================================

    def _remove_html_artifacts(
        self,
        text: str,
        report: CleaningReport,
    ) -> str:

        br_matches = re.findall(
            r"<br\s*/?>",
            text,
            flags=re.IGNORECASE,
        )

        if br_matches:
            report.html_elements_removed += len(
                br_matches
            )

        text = re.sub(
            r"<br\s*/?>",
            "\n",
            text,
            flags=re.IGNORECASE,
        )

        for source, target in (
            self.HTML_ENTITY_REPLACEMENTS.items()
        ):
            occurrences = text.count(source)

            if occurrences:
                report.html_elements_removed += (
                    occurrences
                )

            text = text.replace(
                source,
                target,
            )

        return text

    # ======================================================
    # NAVIGATION CLEANUP
    # ======================================================

    def _remove_navigation(
        self,
        text: str,
        report: CleaningReport,
    ) -> str:

        for pattern in self.NAVIGATION_PATTERNS:

            matches = re.findall(
                pattern,
                text,
            )

            if matches:
                report.navigation_blocks_removed += (
                    len(matches)
                )

            text = re.sub(
                pattern,
                "",
                text,
            )

        return text

    # ======================================================
    # HEADING NORMALIZATION
    # ======================================================

    def _normalize_headings(
        self,
        text: str,
        report: CleaningReport,
    ) -> str:

        heading_pattern = re.compile(
            r"^(#{1,6})([^\s#].*)$",
            flags=re.MULTILINE,
        )

        matches = heading_pattern.findall(
            text
        )

        if matches:
            report.headings_normalized += len(
                matches
            )

        return heading_pattern.sub(
            r"\1 \2",
            text,
        )

    # ======================================================
    # TABLE NORMALIZATION
    # ======================================================

    def _normalize_tables(
        self,
        text: str,
        report: CleaningReport,
    ) -> str:

        lines = []

        for line in text.splitlines():

            if "|" in line:

                report.tables_normalized += 1

                cells = [
                    cell.strip()
                    for cell in line.split("|")
                ]

                line = " | ".join(cells)

            lines.append(line)

        return "\n".join(lines)

    # ======================================================
    # FINAL MARKDOWN CLEANUP
    # ======================================================

    @staticmethod
    def _normalize_markdown(
        text: str,
    ) -> str:

        text = re.sub(
            r"\n{3,}",
            "\n\n",
            text,
        )

        text = re.sub(
            r"[ \t]+$",
            "",
            text,
            flags=re.MULTILINE,
        )

        text = re.sub(
            r"[ \t]{2,}",
            " ",
            text,
        )

        return text.strip()