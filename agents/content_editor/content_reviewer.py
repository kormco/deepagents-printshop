"""
Content Reviewer Tool

Provides content analysis and improvement capabilities using LLM-based review.
"""

import re
import os
from typing import Dict, List, Tuple
from anthropic import Anthropic


class ContentReviewer:
    """Content review and improvement tool using Anthropic Claude."""

    def __init__(self):
        """Initialize the content reviewer with API client."""
        self.client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    def analyze_readability(self, text: str) -> Dict:
        """
        Analyze text readability metrics.

        Args:
            text: Input text to analyze

        Returns:
            Dict with readability metrics
        """
        # Basic readability analysis
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]

        words = text.split()
        total_words = len(words)
        total_sentences = len(sentences)

        # Calculate average sentence length
        avg_sentence_length = total_words / total_sentences if total_sentences > 0 else 0

        # Count syllables (rough approximation)
        syllable_count = sum(self._count_syllables(word) for word in words)

        # Flesch Reading Ease (simplified)
        if total_sentences > 0 and total_words > 0:
            flesch_score = 206.835 - (1.015 * avg_sentence_length) - (84.6 * (syllable_count / total_words))
            flesch_score = max(0, min(100, flesch_score))
        else:
            flesch_score = 0

        # Passive voice detection (simplified)
        passive_indicators = ['was', 'were', 'been', 'being', 'is', 'are', 'am']
        passive_count = sum(1 for word in words if word.lower() in passive_indicators)
        passive_percentage = (passive_count / total_words * 100) if total_words > 0 else 0

        return {
            "total_words": total_words,
            "total_sentences": total_sentences,
            "avg_sentence_length": round(avg_sentence_length, 1),
            "flesch_reading_ease": round(flesch_score, 1),
            "passive_voice_percentage": round(passive_percentage, 1),
            "syllable_count": syllable_count
        }

    def _count_syllables(self, word: str) -> int:
        """Rough syllable counting approximation."""
        word = word.lower()
        vowels = "aeiouy"
        syllables = 0
        prev_was_vowel = False

        for char in word:
            if char in vowels:
                if not prev_was_vowel:
                    syllables += 1
                prev_was_vowel = True
            else:
                prev_was_vowel = False

        # Handle silent e
        if word.endswith('e') and syllables > 1:
            syllables -= 1

        return max(1, syllables)

    def calculate_quality_score(self, metrics: Dict, issues: List[str]) -> int:
        """
        Calculate overall content quality score (0-100).

        Args:
            metrics: Readability metrics
            issues: List of identified issues

        Returns:
            Quality score from 0-100
        """
        score = 100

        # Penalize for grammar/style issues
        score -= min(len(issues) * 2, 40)  # Up to 40 points for issues

        # Readability factors
        flesch = metrics.get("flesch_reading_ease", 0)
        if flesch < 30:  # Too difficult
            score -= 15
        elif flesch > 70:  # Too easy for academic content
            score -= 10

        # Sentence length factors
        avg_length = metrics.get("avg_sentence_length", 0)
        if avg_length > 25:  # Too long
            score -= 10
        elif avg_length < 10:  # Too short
            score -= 5

        # Passive voice penalty
        passive_pct = metrics.get("passive_voice_percentage", 0)
        if passive_pct > 30:
            score -= 10

        return max(0, min(100, score))

    def review_text(self, text: str) -> Dict:
        """
        Review and improve text content.

        Args:
            text: Original text content

        Returns:
            Dict with improved content and analysis
        """
        # Analyze original content
        original_metrics = self.analyze_readability(text)

        # Use Claude to review and improve the content
        prompt = f"""You are a professional editor specializing in academic and technical writing.

Please review and improve the following text for:
1. Grammar and spelling errors
2. Sentence structure and clarity
3. Word choice and precision
4. Flow and readability
5. Academic writing style

Original text:
{text}

Please provide:
1. The improved version of the text
2. A list of specific changes you made
3. A brief summary of the improvements

Format your response as:

IMPROVED TEXT:
[improved version here]

CHANGES MADE:
- [change 1]
- [change 2]
- [etc.]

SUMMARY:
[brief summary of improvements]
"""

        try:
            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}]
            )

            response_text = response.content[0].text

            # Parse the response
            improved_text, changes_made, summary = self._parse_review_response(response_text)

            # Analyze improved content
            improved_metrics = self.analyze_readability(improved_text)

            # Calculate quality scores
            original_issues = self._identify_issues(text, original_metrics)
            improved_issues = self._identify_issues(improved_text, improved_metrics)

            original_score = self.calculate_quality_score(original_metrics, original_issues)
            improved_score = self.calculate_quality_score(improved_metrics, improved_issues)

            return {
                "original_content": text,
                "improved_content": improved_text,
                "original_metrics": original_metrics,
                "improved_metrics": improved_metrics,
                "original_quality_score": original_score,
                "improved_quality_score": improved_score,
                "quality_improvement": improved_score - original_score,
                "changes_made": changes_made,
                "changes_summary": summary,
                "issues_fixed": len(original_issues) - len(improved_issues)
            }

        except Exception as e:
            print(f"Error during content review: {e}")
            return {
                "original_content": text,
                "improved_content": text,  # Fallback to original
                "original_metrics": original_metrics,
                "improved_metrics": original_metrics,
                "original_quality_score": self.calculate_quality_score(original_metrics, []),
                "improved_quality_score": self.calculate_quality_score(original_metrics, []),
                "quality_improvement": 0,
                "changes_made": [],
                "changes_summary": f"Review failed: {str(e)}",
                "issues_fixed": 0
            }

    def _parse_review_response(self, response: str) -> Tuple[str, List[str], str]:
        """Parse Claude's review response into components."""
        improved_text = ""
        changes_made = []
        summary = ""

        # Split response into sections
        sections = response.split('\n\n')
        current_section = ""

        for section in sections:
            if section.startswith("IMPROVED TEXT:"):
                current_section = "improved"
                improved_text = section.replace("IMPROVED TEXT:", "").strip()
            elif section.startswith("CHANGES MADE:"):
                current_section = "changes"
                changes_text = section.replace("CHANGES MADE:", "").strip()
                changes_made = [line.strip().lstrip("- ") for line in changes_text.split('\n') if line.strip()]
            elif section.startswith("SUMMARY:"):
                current_section = "summary"
                summary = section.replace("SUMMARY:", "").strip()
            elif current_section == "improved":
                improved_text += "\n\n" + section
            elif current_section == "changes":
                changes_made.extend([line.strip().lstrip("- ") for line in section.split('\n') if line.strip()])
            elif current_section == "summary":
                summary += "\n\n" + section

        return improved_text.strip(), changes_made, summary.strip()

    def _identify_issues(self, text: str, metrics: Dict) -> List[str]:
        """Identify potential issues in the text."""
        issues = []

        # Check sentence length
        if metrics.get("avg_sentence_length", 0) > 25:
            issues.append("Long sentences detected")

        # Check passive voice
        if metrics.get("passive_voice_percentage", 0) > 30:
            issues.append("High passive voice usage")

        # Check readability
        flesch = metrics.get("flesch_reading_ease", 0)
        if flesch < 30:
            issues.append("Text may be too complex")

        # Simple grammar checks
        if "....." in text:
            issues.append("Multiple consecutive periods")

        if "  " in text:
            issues.append("Multiple consecutive spaces")

        # Check for common issues
        common_errors = [
            (r'\bit\'s\b', "Possible incorrect apostrophe usage"),
            (r'\byour\b.*\byour\b', "Repeated 'your'"),
            (r'\bthe the\b', "Repeated 'the'"),
        ]

        for pattern, description in common_errors:
            if re.search(pattern, text, re.IGNORECASE):
                issues.append(description)

        return issues