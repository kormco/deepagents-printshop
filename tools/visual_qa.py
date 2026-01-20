"""Visual Quality Assurance for PDF documents."""

import os
import base64
import io
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

from pdf2image import convert_from_path
from PIL import Image

# Make anthropic import optional
try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    print("⚠️ Anthropic not available - visual analysis will be limited")


@dataclass
class VisualValidationResult:
    """Result of visual validation for a single page."""
    page_number: int
    page_type: str  # 'title', 'toc', 'content'
    overall_score: float  # 0-100
    issues_found: List[str]
    strengths_found: List[str]
    detailed_feedback: str
    element_scores: Dict[str, float]  # Specific element scores


@dataclass
class DocumentVisualQA:
    """Complete visual QA results for a document."""
    pdf_path: str
    total_pages: int
    overall_score: float
    page_results: List[VisualValidationResult]
    summary: str
    recommendations: List[str]
    timestamp: str


class PDFToImageConverter:
    """Convert PDF pages to images for visual analysis."""

    def __init__(self, dpi: int = 300):
        """
        Initialize PDF converter.

        Args:
            dpi: Resolution for image conversion (higher = better quality)
        """
        self.dpi = dpi

    def convert_pdf_to_images(self, pdf_path: str) -> List[Image.Image]:
        """
        Convert PDF to list of PIL Images.

        Args:
            pdf_path: Path to PDF file

        Returns:
            List of PIL Image objects, one per page
        """
        try:
            images = convert_from_path(pdf_path, dpi=self.dpi)
            print(f"✅ Converted PDF to {len(images)} page images")
            return images
        except Exception as e:
            print(f"❌ Error converting PDF to images: {e}")
            return []

    def save_images(self, images: List[Image.Image], output_dir: str, prefix: str = "page") -> List[str]:
        """Save images to disk and return file paths."""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        saved_paths = []
        for i, image in enumerate(images, 1):
            filename = f"{prefix}_{i:02d}.png"
            filepath = output_path / filename
            image.save(filepath, 'PNG')
            saved_paths.append(str(filepath))

        return saved_paths


class VisualValidator:
    """Basic visual validation using image analysis."""

    def __init__(self):
        self.validation_rules = self._init_validation_rules()

    def _init_validation_rules(self) -> Dict:
        """Initialize validation rules for different page types."""
        return {
            'title_page': {
                'required_elements': ['title', 'author', 'date'],
                'layout_checks': ['centered', 'proper_spacing'],
                'typography_checks': ['title_size', 'font_consistency']
            },
            'toc_page': {
                'required_elements': ['toc_header', 'section_list', 'page_numbers'],
                'layout_checks': ['alignment', 'indentation', 'spacing'],
                'typography_checks': ['consistent_fonts', 'number_alignment']
            },
            'content_page': {
                'required_elements': ['header', 'footer', 'page_number'],
                'layout_checks': ['margins', 'line_spacing', 'paragraph_structure'],
                'typography_checks': ['font_consistency', 'heading_hierarchy']
            }
        }

    def detect_page_type(self, page_number: int, total_pages: int) -> str:
        """Detect the type of page based on position."""
        if page_number == 1:
            return 'title_page'
        elif page_number == 2:
            return 'toc_page'
        else:
            return 'content_page'

    def validate_basic_structure(self, image: Image.Image, page_type: str) -> Dict:
        """Perform basic structural validation of an image."""
        # This is a simplified version - in production you'd use computer vision
        width, height = image.size
        aspect_ratio = width / height

        # Basic checks that can be done programmatically
        checks = {
            'image_dimensions': (width, height),
            'aspect_ratio': aspect_ratio,
            'is_portrait': height > width,
            'resolution_adequate': width >= 1000 and height >= 1000,
            'file_size_reasonable': True  # Could check actual file size
        }

        return checks


class MultimodalLLMAnalyzer:
    """Use Claude's vision capabilities for detailed visual analysis."""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Claude analyzer.

        Args:
            api_key: Anthropic API key (will use environment variable if None)
        """
        if not ANTHROPIC_AVAILABLE:
            self.client = None
            self.api_key = None
            print("⚠️ Anthropic not available - using fallback analysis")
        else:
            self.api_key = api_key or os.getenv('ANTHROPIC_API_KEY')
            if not self.api_key:
                print("⚠️ ANTHROPIC_API_KEY not found - using fallback analysis")
                self.client = None
            else:
                self.client = anthropic.Anthropic(api_key=self.api_key)

        self.validation_prompts = self._init_validation_prompts()

    def _init_validation_prompts(self) -> Dict[str, str]:
        """Initialize validation prompts for different page types."""
        return {
            'title_page': """
Analyze this title page image for a research document. Evaluate the following aspects and provide scores (1-10) for each:

1. **Title Visibility** (1-10): Is the document title clearly visible, properly sized, and well-positioned?
2. **Author Information** (1-10): Is the author name present and appropriately placed?
3. **Date Information** (1-10): Is the date shown and properly formatted?
4. **Layout Quality** (1-10): Is the content centered and professionally arranged? Are borders or diagrams overlapping?
5. **Typography** (1-10): Are fonts appropriate, consistent, and readable?

**CRITICAL CHECK - LaTeX Syntax Detection:**
⚠️ **RED FLAG**: Check if any LaTeX code or commands are visible in the rendered PDF (e.g., \\textbf{}, \\section{}, \\begin{}, \\usepackage{}, etc.).
- If ANY LaTeX syntax is visible in the output, this is a CRITICAL FAILURE
- The PDF should show formatted text, not raw LaTeX commands
- Score must be reduced to 1/10 if LaTeX syntax is detected
- Add "CRITICAL: Visible LaTeX syntax detected" to issues_found

Also identify:
- Any missing elements that should be present
- Formatting issues or visual problems
- Suggestions for improvement

Provide your response in this JSON format:
{
    "scores": {
        "title_visibility": <score>,
        "author_information": <score>,
        "date_information": <score>,
        "layout_quality": <score>,
        "typography": <score>
    },
    "overall_score": <average_score>,
    "issues_found": ["list", "of", "issues"],
    "strengths_found": ["list", "of", "strengths"],
    "detailed_feedback": "Comprehensive analysis of the page quality and specific recommendations"
}
""",

            'toc_page': """
Examine this table of contents page. Evaluate these aspects with scores (1-10):

1. **Header Presence** (1-10): Is there a clear "Table of Contents" or similar header?
2. **Content Listing** (1-10): Are sections/chapters properly listed?
3. **Page Numbers** (1-10): Are page numbers present and aligned correctly?
4. **Hierarchy** (1-10): Is the section hierarchy clear with proper indentation?
5. **Formatting** (1-10): Is the overall formatting clean and professional?

**CRITICAL CHECK - LaTeX Syntax Detection:**
⚠️ **RED FLAG**: Check if any LaTeX code or commands are visible in the rendered PDF (e.g., \\textbf{}, \\section{}, \\begin{}, \\usepackage{}, etc.).
- If ANY LaTeX syntax is visible in the output, this is a CRITICAL FAILURE
- The PDF should show formatted text, not raw LaTeX commands
- Score must be reduced to 1/10 if LaTeX syntax is detected
- Add "CRITICAL: Visible LaTeX syntax detected" to issues_found

Identify:
- Missing or malformed elements
- Alignment and spacing issues
- Typography and readability concerns

Respond in JSON format:
{
    "scores": {
        "header_presence": <score>,
        "content_listing": <score>,
        "page_numbers": <score>,
        "hierarchy": <score>,
        "formatting": <score>
    },
    "overall_score": <average_score>,
    "issues_found": ["list", "of", "issues"],
    "strengths_found": ["list", "of", "strengths"],
    "detailed_feedback": "Detailed analysis and recommendations"
}
""",

            'content_page': """
Analyze this content page for visual quality. Score these elements (1-10):

1. **Headers/Footers** (1-10): Are headers and footers present, consistent, and well-formatted?
2. **Page Numbers** (1-10): Is the page number visible and properly positioned?
3. **Text Layout** (1-10): Are margins, spacing, and text flow appropriate?
4. **Typography** (1-10): Are fonts consistent, readable, and properly sized?
5. **Content Elements** (1-10): Are tables, figures, or other elements well-formatted?

**CRITICAL CHECK - LaTeX Syntax Detection:**
⚠️ **RED FLAG**: Check if any LaTeX code or commands are visible in the rendered PDF (e.g., \\textbf{}, \\section{}, \\begin{}, \\usepackage{}, \\cite{}, \\ref{}, etc.).
- If ANY LaTeX syntax is visible in the output, this is a CRITICAL FAILURE
- The PDF should show formatted text, not raw LaTeX commands
- Score must be reduced to 1/10 if LaTeX syntax is detected
- Add "CRITICAL: Visible LaTeX syntax detected" to issues_found

Look for:
- Inconsistent formatting
- Poor spacing or alignment
- Missing page elements
- Typography issues

JSON response format:
{
    "scores": {
        "headers_footers": <score>,
        "page_numbers": <score>,
        "text_layout": <score>,
        "typography": <score>,
        "content_elements": <score>
    },
    "overall_score": <average_score>,
    "issues_found": ["list", "of", "issues"],
    "strengths_found": ["list", "of", "strengths"],
    "detailed_feedback": "Comprehensive quality assessment and improvement suggestions"
}
"""
        }

    def image_to_base64(self, image: Image.Image, max_size_bytes: int = 5 * 1024 * 1024) -> Tuple[str, str]:
        """
        Convert PIL Image to base64 string, compressing if needed.

        Args:
            image: PIL Image to convert
            max_size_bytes: Maximum size in bytes (default 5MB for Claude API)

        Returns:
            Tuple of (base64_string, media_type)
        """
        # First try PNG
        buffer = io.BytesIO()
        image.save(buffer, format='PNG')
        image_data = buffer.getvalue()

        # If under limit, return as-is
        if len(image_data) <= max_size_bytes:
            return base64.b64encode(image_data).decode('utf-8'), "image/png"

        # Need to compress - try JPEG with decreasing quality
        print(f"   ⚠️ Image too large ({len(image_data) / 1024 / 1024:.1f}MB), compressing...")

        # Convert to RGB if necessary (JPEG doesn't support alpha)
        if image.mode in ('RGBA', 'P'):
            rgb_image = Image.new('RGB', image.size, (255, 255, 255))
            rgb_image.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
            image = rgb_image

        # Try decreasing quality levels
        for quality in [85, 70, 50, 30]:
            buffer = io.BytesIO()
            image.save(buffer, format='JPEG', quality=quality, optimize=True)
            image_data = buffer.getvalue()

            if len(image_data) <= max_size_bytes:
                print(f"   ✅ Compressed to {len(image_data) / 1024 / 1024:.1f}MB (JPEG quality={quality})")
                return base64.b64encode(image_data).decode('utf-8'), "image/jpeg"

        # If still too large, resize the image
        scale = 0.75
        while len(image_data) > max_size_bytes and scale > 0.25:
            new_size = (int(image.width * scale), int(image.height * scale))
            resized = image.resize(new_size, Image.Resampling.LANCZOS)

            buffer = io.BytesIO()
            resized.save(buffer, format='JPEG', quality=50, optimize=True)
            image_data = buffer.getvalue()

            if len(image_data) <= max_size_bytes:
                print(f"   ✅ Compressed to {len(image_data) / 1024 / 1024:.1f}MB (resized to {scale:.0%})")
                return base64.b64encode(image_data).decode('utf-8'), "image/jpeg"

            scale -= 0.1

        # Final fallback - aggressive resize
        print(f"   ⚠️ Using aggressive compression")
        new_size = (int(image.width * 0.25), int(image.height * 0.25))
        resized = image.resize(new_size, Image.Resampling.LANCZOS)
        buffer = io.BytesIO()
        resized.save(buffer, format='JPEG', quality=30, optimize=True)
        image_data = buffer.getvalue()

        return base64.b64encode(image_data).decode('utf-8'), "image/jpeg"

    def analyze_page(self, image: Image.Image, page_type: str) -> Dict:
        """
        Analyze a page image using Claude's vision capabilities.

        Args:
            image: PIL Image of the page
            page_type: Type of page ('title_page', 'toc_page', 'content_page')

        Returns:
            Analysis results as dictionary
        """
        # Use fallback analysis if Claude is not available
        if not self.client:
            return self._fallback_analysis(image, page_type)

        try:
            # Convert image to base64 (with compression if needed)
            image_b64, media_type = self.image_to_base64(image)

            # Get appropriate prompt
            prompt = self.validation_prompts.get(page_type, self.validation_prompts['content_page'])

            # Analyze with Claude
            response = self.client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=1500,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": media_type,
                                    "data": image_b64
                                }
                            },
                            {
                                "type": "text",
                                "text": prompt
                            }
                        ]
                    }
                ]
            )

            # Parse JSON response
            import json
            response_text = response.content[0].text

            # Extract JSON from response (handle cases where there's extra text)
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            json_content = response_text[json_start:json_end]

            analysis_result = json.loads(json_content)
            return analysis_result

        except Exception as e:
            print(f"❌ Error analyzing page with Claude: {e}")
            return self._fallback_analysis(image, page_type)

    def _fallback_analysis(self, image: Image.Image, page_type: str) -> Dict:
        """Provide basic fallback analysis when Claude is not available."""
        width, height = image.size

        # Basic heuristic analysis
        if page_type == 'title_page':
            # For title page, assume it's decent if image is reasonable size
            score = 7.5 if width > 1000 and height > 1000 else 6.0
            issues = ["Visual analysis limited - install Anthropic API for detailed analysis"]
            strengths = ["Page successfully rendered"] if width > 1000 else []
            scores = {
                "title_visibility": score,
                "author_information": score,
                "date_information": score,
                "layout_quality": score,
                "typography": score
            }
        elif page_type == 'toc_page':
            score = 7.0 if width > 1000 and height > 1000 else 6.0
            issues = ["Visual analysis limited - install Anthropic API for detailed analysis"]
            strengths = ["Page successfully rendered"] if width > 1000 else []
            scores = {
                "header_presence": score,
                "content_listing": score,
                "page_numbers": score,
                "hierarchy": score,
                "formatting": score
            }
        else:  # content_page
            score = 7.0 if width > 1000 and height > 1000 else 6.0
            issues = ["Visual analysis limited - install Anthropic API for detailed analysis"]
            strengths = ["Page successfully rendered"] if width > 1000 else []
            scores = {
                "headers_footers": score,
                "page_numbers": score,
                "text_layout": score,
                "typography": score,
                "content_elements": score
            }

        return {
            "scores": scores,
            "overall_score": score,
            "issues_found": issues,
            "strengths_found": strengths,
            "detailed_feedback": f"Basic visual check completed for {page_type}. Page dimensions: {width}x{height}. For detailed analysis, configure Anthropic API key."
        }


class VisualQAAgent:
    """Main Visual QA Agent that orchestrates the entire process."""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Visual QA Agent.

        Args:
            api_key: Anthropic API key (optional, will use environment variable)
        """
        self.pdf_converter = PDFToImageConverter()
        self.validator = VisualValidator()
        self.llm_analyzer = MultimodalLLMAnalyzer(api_key)

        # Create output directory for images
        self.output_dir = Path("artifacts/reviewed_content/v3_visual_qa")
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def validate_pdf_visual_quality(self, pdf_path: str) -> DocumentVisualQA:
        """
        Perform complete visual quality assessment of a PDF.

        Args:
            pdf_path: Path to PDF file

        Returns:
            Complete visual QA results
        """
        print(f"🔍 Starting Visual QA for: {pdf_path}")
        print("=" * 60)

        # Convert PDF to images
        images = self.pdf_converter.convert_pdf_to_images(pdf_path)
        if not images:
            return self._create_error_result(pdf_path, "Failed to convert PDF to images")

        # Save images for reference
        image_paths = self.pdf_converter.save_images(
            images,
            str(self.output_dir / "page_images"),
            "page"
        )

        # Analyze each page
        page_results = []
        total_score = 0

        for i, image in enumerate(images, 1):
            print(f"\n📄 Analyzing page {i}/{len(images)}...")

            # Detect page type
            page_type = self.validator.detect_page_type(i, len(images))
            print(f"   Detected page type: {page_type}")

            # Basic validation
            basic_checks = self.validator.validate_basic_structure(image, page_type)

            # LLM analysis
            llm_analysis = self.llm_analyzer.analyze_page(image, page_type)

            # Combine results
            page_result = VisualValidationResult(
                page_number=i,
                page_type=page_type,
                overall_score=llm_analysis.get('overall_score', 0),
                issues_found=llm_analysis.get('issues_found', []),
                strengths_found=llm_analysis.get('strengths_found', []),
                detailed_feedback=llm_analysis.get('detailed_feedback', ''),
                element_scores=llm_analysis.get('scores', {})
            )

            page_results.append(page_result)
            total_score += page_result.overall_score

            print(f"   Score: {page_result.overall_score:.1f}/10")
            if page_result.issues_found:
                print(f"   Issues: {len(page_result.issues_found)} found")

        # Calculate overall score
        overall_score = (total_score / len(images)) * 10 if images else 0  # Convert to 0-100 scale

        # Generate summary and recommendations
        summary, recommendations = self._generate_summary(page_results, overall_score)

        # Create final result
        result = DocumentVisualQA(
            pdf_path=pdf_path,
            total_pages=len(images),
            overall_score=overall_score,
            page_results=page_results,
            summary=summary,
            recommendations=recommendations,
            timestamp=datetime.now().isoformat()
        )

        print("\n" + "=" * 60)
        print(f"🎯 Visual QA Complete!")
        print(f"   Overall Score: {overall_score:.1f}/100")
        print(f"   Pages Analyzed: {len(images)}")
        print(f"   Issues Found: {sum(len(p.issues_found) for p in page_results)}")

        return result

    def _create_error_result(self, pdf_path: str, error_message: str) -> DocumentVisualQA:
        """Create error result when analysis fails."""
        return DocumentVisualQA(
            pdf_path=pdf_path,
            total_pages=0,
            overall_score=0,
            page_results=[],
            summary=f"Visual QA failed: {error_message}",
            recommendations=["Fix PDF conversion issues and retry"],
            timestamp=datetime.now().isoformat()
        )

    def _generate_summary(self, page_results: List[VisualValidationResult], overall_score: float) -> Tuple[str, List[str]]:
        """Generate summary and recommendations based on page results."""
        total_issues = sum(len(p.issues_found) for p in page_results)
        total_strengths = sum(len(p.strengths_found) for p in page_results)

        # Generate summary
        if overall_score >= 85:
            quality_level = "Excellent"
        elif overall_score >= 75:
            quality_level = "Good"
        elif overall_score >= 60:
            quality_level = "Acceptable"
        else:
            quality_level = "Needs Improvement"

        summary = f"""Visual Quality Assessment: {quality_level} ({overall_score:.1f}/100)

Analyzed {len(page_results)} pages with {total_issues} issues identified and {total_strengths} strengths noted.
Pages include: {', '.join(set(p.page_type.replace('_', ' ').title() for p in page_results))}"""

        # Generate recommendations
        recommendations = []

        # Collect common issues
        all_issues = []
        for page in page_results:
            all_issues.extend(page.issues_found)

        # Group similar issues
        if any('title' in issue.lower() for issue in all_issues):
            recommendations.append("Review title page formatting and ensure all elements are visible")

        if any('table of contents' in issue.lower() or 'toc' in issue.lower() for issue in all_issues):
            recommendations.append("Fix table of contents formatting and alignment issues")

        if any('header' in issue.lower() or 'footer' in issue.lower() for issue in all_issues):
            recommendations.append("Ensure consistent headers and footers across all pages")

        if any('spacing' in issue.lower() or 'margin' in issue.lower() for issue in all_issues):
            recommendations.append("Adjust spacing and margins for better visual consistency")

        if any('font' in issue.lower() or 'typography' in issue.lower() for issue in all_issues):
            recommendations.append("Review typography choices for consistency and readability")

        if not recommendations:
            if overall_score >= 85:
                recommendations.append("Document visual quality is excellent - ready for publication")
            else:
                recommendations.append("Review identified issues and consider LaTeX template improvements")

        return summary, recommendations

    def save_report(self, result: DocumentVisualQA, output_path: Optional[str] = None) -> str:
        """Save visual QA report to file."""
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = str(self.output_dir / f"visual_qa_report_{timestamp}.md")

        # Generate markdown report
        report_content = f"""# Visual Quality Assessment Report

**Document:** {result.pdf_path}
**Generated:** {result.timestamp}
**Overall Score:** {result.overall_score:.1f}/100

## Summary

{result.summary}

## Page-by-Page Analysis

"""

        for page in result.page_results:
            report_content += f"""### Page {page.page_number} ({page.page_type.replace('_', ' ').title()})

**Score:** {page.overall_score:.1f}/10

**Element Scores:**
"""
            for element, score in page.element_scores.items():
                report_content += f"- {element.replace('_', ' ').title()}: {score}/10\n"

            if page.issues_found:
                report_content += f"\n**Issues Found:**\n"
                for issue in page.issues_found:
                    report_content += f"- {issue}\n"

            if page.strengths_found:
                report_content += f"\n**Strengths:**\n"
                for strength in page.strengths_found:
                    report_content += f"- {strength}\n"

            report_content += f"\n**Detailed Feedback:**\n{page.detailed_feedback}\n\n"

        report_content += f"""## Recommendations

"""
        for rec in result.recommendations:
            report_content += f"- {rec}\n"

        report_content += f"""
## Next Steps

{'✅ Document ready for publication' if result.overall_score >= 85 else '⚠️ Address identified issues before final publication'}

**Generated by DeepAgents PrintShop Visual QA System**
"""

        # Save report
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report_content)

        print(f"📄 Visual QA report saved: {output_path}")
        return output_path


def main():
    """Test the Visual QA system."""
    # Test with current research report
    pdf_path = "artifacts/output/research_report.pdf"

    if not os.path.exists(pdf_path):
        print(f"❌ PDF not found: {pdf_path}")
        return

    print("🔍 Testing Visual QA System")
    print("=" * 50)

    # Initialize Visual QA Agent
    try:
        agent = VisualQAAgent()

        # Run visual quality assessment
        result = agent.validate_pdf_visual_quality(pdf_path)

        # Save report
        report_path = agent.save_report(result)

        print(f"\n✅ Visual QA Complete!")
        print(f"📊 Overall Score: {result.overall_score:.1f}/100")
        print(f"📄 Report: {report_path}")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()