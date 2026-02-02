"""Magazine Layout Tools - Professional magazine LaTeX macros and templates.

DEPRECATED: All LaTeX macro definitions have been moved into
content_types/magazine/type.md as ```latex code blocks. The pipeline now reads
macros directly from type.md via ContentTypeDefinition.latex_preamble_blocks.
This file is kept for reference only and is no longer imported by active code.

Provides LaTeX macro definitions for creating professional magazine layouts including:
- Cover page mastheads with positioned callouts
- Creative contents pages with large numbers
- Dark/light page contrast
- Circle infographics and data visualizations
- Pull quotes and vertical text elements
"""

from typing import Dict, List, Optional
from dataclasses import dataclass, field


@dataclass
class MagazineTheme:
    """Color theme for magazine styling."""
    primary: str = "2E86AB"      # Deep blue
    secondary: str = "A23B72"    # Magenta
    accent: str = "F18F01"       # Orange
    dark: str = "1A1A2E"         # Near black
    light: str = "F5F5F5"        # Off white
    text_dark: str = "1A1A2E"
    text_light: str = "FFFFFF"


class MagazineLayoutGenerator:
    """Generate LaTeX macros and preamble for professional magazine layouts."""

    def __init__(self, theme: Optional[MagazineTheme] = None):
        self.theme = theme or MagazineTheme()

    def get_preamble_packages(self) -> str:
        """Get required LaTeX packages for magazine layout."""
        return r"""% Magazine Layout Packages
\usepackage{tikz}
\usepackage{eso-pic}
\usepackage{contour}
\usepackage{lettrine}
\usepackage{multicol}
\usepackage{enumitem}
\usepackage{xcolor}
\usepackage{graphicx}
\usepackage{geometry}
\usepackage{fancyhdr}
\usepackage{tcolorbox}
\usepackage{rotating}
\usepackage{wrapfig}
\usepackage{float}
\usepackage{calc}

% TikZ libraries
\usetikzlibrary{positioning, calc, shapes, backgrounds, fit}
"""

    def get_color_definitions(self) -> str:
        """Get color definitions for the theme."""
        return f"""% Magazine Color Theme
\\definecolor{{magprimary}}{{HTML}}{{{self.theme.primary}}}
\\definecolor{{magsecondary}}{{HTML}}{{{self.theme.secondary}}}
\\definecolor{{magaccent}}{{HTML}}{{{self.theme.accent}}}
\\definecolor{{magdark}}{{HTML}}{{{self.theme.dark}}}
\\definecolor{{maglight}}{{HTML}}{{{self.theme.light}}}
"""

    def get_masthead_macro(self) -> str:
        """LaTeX macro for magazine masthead."""
        return r"""% Magazine Masthead - Large title at top of cover
% Usage: \masthead{MAIN TITLE}{subtitle}
\newcommand{\masthead}[2]{%
  \begin{tikzpicture}[remember picture, overlay]
    % Main title - large and bold
    \node[anchor=north, font=\fontsize{64}{64}\selectfont\bfseries\sffamily, text=white]
      at ([yshift=-2cm]current page.north) {#1};
    % Subtitle - smaller, lighter weight
    \node[anchor=north, font=\fontsize{18}{20}\selectfont\sffamily, text=white]
      at ([yshift=-3.5cm]current page.north) {#2};
  \end{tikzpicture}%
}

% Masthead with shadow for better readability
% Usage: \mastheadshadow{MAIN TITLE}{subtitle}
\newcommand{\mastheadshadow}[2]{%
  \begin{tikzpicture}[remember picture, overlay]
    % Shadow layer
    \node[anchor=north, font=\fontsize{64}{64}\selectfont\bfseries\sffamily, text=black, opacity=0.5]
      at ([yshift=-1.95cm, xshift=0.1cm]current page.north) {#1};
    % Main title
    \node[anchor=north, font=\fontsize{64}{64}\selectfont\bfseries\sffamily, text=white]
      at ([yshift=-2cm]current page.north) {#1};
    % Subtitle
    \node[anchor=north, font=\fontsize{18}{20}\selectfont\sffamily, text=white]
      at ([yshift=-3.5cm]current page.north) {#2};
  \end{tikzpicture}%
}
"""

    def get_cover_callout_macros(self) -> str:
        """LaTeX macros for cover page callouts."""
        return r"""% Left side callout (positioned on left of cover)
% Usage: \leftcallout{y-offset}{HEADLINE}{subtext}
\newcommand{\leftcallout}[3]{%
  \begin{tikzpicture}[remember picture, overlay]
    \node[anchor=west, align=left, text width=5cm,
          font=\sffamily, text=white]
      at ([xshift=1.5cm, yshift=#1]current page.west) {%
        {\fontsize{11}{13}\selectfont\bfseries #2}\\[3pt]
        {\fontsize{9}{11}\selectfont #3}%
      };
  \end{tikzpicture}%
}

% Right side callout (positioned on right of cover)
% Usage: \rightcallout{y-offset}{HEADLINE}{subtext}
\newcommand{\rightcallout}[3]{%
  \begin{tikzpicture}[remember picture, overlay]
    \node[anchor=east, align=right, text width=5cm,
          font=\sffamily, text=white]
      at ([xshift=-1.5cm, yshift=#1]current page.east) {%
        {\fontsize{11}{13}\selectfont\bfseries #2}\\[3pt]
        {\fontsize{9}{11}\selectfont #3}%
      };
  \end{tikzpicture}%
}

% Feature headline at bottom of cover
% Usage: \coverfeature{MAIN HEADLINE}{subheadline}
\newcommand{\coverfeature}[2]{%
  \begin{tikzpicture}[remember picture, overlay]
    % Dark gradient overlay at bottom
    \fill[black, opacity=0.6]
      (current page.south west) rectangle ([yshift=5cm]current page.south east);
    % Main headline
    \node[anchor=south, font=\fontsize{42}{44}\selectfont\bfseries\sffamily, text=white]
      at ([yshift=2.5cm]current page.south) {#1};
    % Subheadline
    \node[anchor=south, font=\fontsize{14}{16}\selectfont\itshape, text=white]
      at ([yshift=1.5cm]current page.south) {#2};
  \end{tikzpicture}%
}

% Vertical text element (like "ISSUE 01")
% Usage: \verticaltext{x-offset}{TEXT}
\newcommand{\verticaltext}[2]{%
  \begin{tikzpicture}[remember picture, overlay]
    \node[anchor=center, rotate=90, font=\fontsize{10}{10}\selectfont\sffamily\bfseries,
          text=white, opacity=0.9]
      at ([xshift=#1, yshift=0cm]current page.west) {#2};
  \end{tikzpicture}%
}
"""

    def get_contents_page_macros(self) -> str:
        """LaTeX macros for creative contents page."""
        return r"""% Creative Contents Page with Large Numbers
% Usage: \contentsentry{PAGE}{TITLE}{description}
\newcommand{\contentsentry}[3]{%
  \noindent
  \begin{minipage}[t]{0.15\textwidth}
    \raggedleft
    {\fontsize{36}{38}\selectfont\color{magprimary}\bfseries #1}%
  \end{minipage}%
  \hspace{0.5cm}%
  \begin{minipage}[t]{0.75\textwidth}
    {\fontsize{12}{14}\selectfont\bfseries #2}\\[2pt]
    {\fontsize{9}{11}\selectfont\color{gray} #3}%
  \end{minipage}%
  \vspace{0.8cm}
}

% Contents page header with vertical text
% Usage: \contentsheader
\newcommand{\contentsheader}{%
  \begin{tikzpicture}[remember picture, overlay]
    \node[anchor=west, rotate=90, font=\fontsize{14}{14}\selectfont\sffamily,
          text=magdark, letter spacing=0.3em]
      at ([xshift=0.8cm, yshift=-5cm]current page.north west) {CONTENTS};
  \end{tikzpicture}%
}

% Contents with stacked large numbers (like the coffee magazine sample)
% Usage in environment
\newenvironment{creativecontents}{%
  \thispagestyle{empty}
  \contentsheader
  \vspace*{1cm}
  \begin{minipage}[t]{0.45\textwidth}
    \vspace{0pt}
    % Space for hero image
  \end{minipage}%
  \hfill
  \begin{minipage}[t]{0.5\textwidth}
    \vspace{0pt}
}{%
  \end{minipage}
  \newpage
}
"""

    def get_dark_light_page_macros(self) -> str:
        """LaTeX macros for dark/light page contrast."""
        return r"""% Dark page environment (full page dark background)
% Usage: \begin{darkpage} content \end{darkpage}
\newenvironment{darkpage}{%
  \newpage
  \pagecolor{magdark}%
  \color{white}%
  \thispagestyle{empty}%
}{%
  \newpage
  \nopagecolor
  \color{black}%
}

% Accent page environment (colored background)
% Usage: \begin{accentpage} content \end{accentpage}
\newenvironment{accentpage}{%
  \newpage
  \pagecolor{magprimary}%
  \color{white}%
  \thispagestyle{empty}%
}{%
  \newpage
  \nopagecolor
  \color{black}%
}

% Dark section box (inline dark background)
% Usage: \begin{darksection} content \end{darksection}
\newtcolorbox{darksection}{%
  colback=magdark,
  colframe=magdark,
  coltext=white,
  boxrule=0pt,
  arc=0pt,
  left=15pt,
  right=15pt,
  top=15pt,
  bottom=15pt,
  width=\textwidth
}

% Light section box
\newtcolorbox{lightsection}{%
  colback=maglight,
  colframe=maglight,
  coltext=magdark,
  boxrule=0pt,
  arc=0pt,
  left=15pt,
  right=15pt,
  top=15pt,
  bottom=15pt,
  width=\textwidth
}
"""

    def get_infographic_macros(self) -> str:
        """LaTeX macros for data visualizations and infographics."""
        return r"""% Circle statistic display
% Usage: \circlestat{percentage}{label}
\newcommand{\circlestat}[2]{%
  \begin{tikzpicture}
    % Outer circle
    \draw[magprimary, line width=3pt] (0,0) circle (1.2cm);
    % Percentage text
    \node[font=\fontsize{20}{20}\selectfont\bfseries] at (0,0) {#1\%};
    % Label below
    \node[font=\fontsize{8}{10}\selectfont, text width=2.5cm, align=center]
      at (0,-1.8) {#2};
  \end{tikzpicture}%
}

% Colored circle stat
% Usage: \circlestatcolor{percentage}{label}{color}
\newcommand{\circlestatcolor}[3]{%
  \begin{tikzpicture}
    % Filled circle with transparency
    \fill[#3, opacity=0.15] (0,0) circle (1.2cm);
    % Outer ring
    \draw[#3, line width=3pt] (0,0) circle (1.2cm);
    % Percentage
    \node[font=\fontsize{20}{20}\selectfont\bfseries, text=#3] at (0,0) {#1\%};
    % Label
    \node[font=\fontsize{8}{10}\selectfont, text width=2.5cm, align=center]
      at (0,-1.8) {#2};
  \end{tikzpicture}%
}

% Large number callout (for statistics)
% Usage: \bigstat{NUMBER}{label}
\newcommand{\bigstat}[2]{%
  \begin{minipage}{3cm}
    \centering
    {\fontsize{36}{38}\selectfont\bfseries\color{magprimary} #1}\\[5pt]
    {\fontsize{9}{11}\selectfont #2}
  \end{minipage}%
}

% Row of circle stats
% Usage: \statrrow{\circlestat{25}{Label 1}}{\circlestat{50}{Label 2}}{\circlestat{75}{Label 3}}
\newcommand{\statrow}[3]{%
  \begin{center}
    #1\hspace{1.5cm}#2\hspace{1.5cm}#3
  \end{center}
}
"""

    def get_pullquote_macro(self) -> str:
        """LaTeX macro for pull quotes."""
        return r"""% Pull quote styling
% Usage: \pullquote{Quote text here}
\newcommand{\pullquote}[1]{%
  \begin{center}
    \begin{minipage}{0.85\textwidth}
      \vspace{1em}
      {\color{magprimary}\rule{\textwidth}{2pt}}\\[0.8em]
      {\fontsize{16}{20}\selectfont\itshape ``#1''}\\[0.5em]
      {\color{magprimary}\rule{\textwidth}{2pt}}
      \vspace{1em}
    \end{minipage}
  \end{center}
}

% Pull quote with attribution
% Usage: \pullquoteattr{Quote text}{Author Name}
\newcommand{\pullquoteattr}[2]{%
  \begin{center}
    \begin{minipage}{0.85\textwidth}
      \vspace{1em}
      {\color{magprimary}\rule{\textwidth}{2pt}}\\[0.8em]
      {\fontsize{16}{20}\selectfont\itshape ``#1''}\\[0.5em]
      {\fontsize{10}{12}\selectfont\bfseries --- #2}\\[0.3em]
      {\color{magprimary}\rule{\textwidth}{2pt}}
      \vspace{1em}
    \end{minipage}
  \end{center}
}
"""

    def get_article_header_macro(self) -> str:
        """LaTeX macro for article headers."""
        return r"""% Article header with section tag
% Usage: \articleheader{SECTION TAG}{Article Title}{Subtitle or byline}
\newcommand{\articleheader}[3]{%
  \vspace*{0.5cm}
  {\fontsize{9}{10}\selectfont\sffamily\bfseries\color{magprimary} #1}\\[0.3cm]
  {\fontsize{28}{32}\selectfont\bfseries #2}\\[0.3cm]
  {\fontsize{11}{13}\selectfont\color{gray} #3}\\[0.8cm]
}

% Simple large article title
% Usage: \articletitle{Title Here}
\newcommand{\articletitle}[1]{%
  \vspace*{0.5cm}
  {\fontsize{32}{36}\selectfont\bfseries #1}\\[0.8cm]
}
"""

    def get_full_preamble(self) -> str:
        """Get complete magazine preamble with all macros."""
        sections = [
            self.get_preamble_packages(),
            self.get_color_definitions(),
            self.get_masthead_macro(),
            self.get_cover_callout_macros(),
            self.get_contents_page_macros(),
            self.get_dark_light_page_macros(),
            self.get_infographic_macros(),
            self.get_pullquote_macro(),
            self.get_article_header_macro(),
        ]
        return "\n".join(sections)

    def get_magazine_requirements(self) -> List[str]:
        """Get list of magazine requirements for LLM prompt."""
        return [
            """MAGAZINE PREAMBLE REQUIREMENTS:
Include all the magazine layout macros defined in the preamble. The document should use:
- \\masthead{TITLE}{subtitle} or \\mastheadshadow{TITLE}{subtitle} for cover title
- \\leftcallout{y-offset}{HEADLINE}{subtext} for left cover callouts
- \\rightcallout{y-offset}{HEADLINE}{subtext} for right cover callouts
- \\coverfeature{MAIN HEADLINE}{subheadline} for bottom feature headline
- \\verticaltext{x-offset}{TEXT} for vertical text elements like "ISSUE 01"
""",
            """COVER PAGE LAYOUT:
Create a visually striking cover with:
1. Full-bleed background image using eso-pic
2. Large masthead at top using \\mastheadshadow (64pt+ font)
3. 2-3 callouts on left and/or right sides
4. Feature headline at bottom using \\coverfeature
5. Vertical "ISSUE XX" text on left edge using \\verticaltext
6. All text should have good contrast against background
""",
            """CONTENTS PAGE DESIGN:
Use the creative contents style with large page numbers:
- Use \\contentsheader to add vertical "CONTENTS" text
- Use \\contentsentry{PAGE}{TITLE}{description} for each entry
- Page numbers should be large (36pt) and colored
- Include a hero image if available
- Keep layout clean with generous whitespace
""",
            """DATA VISUALIZATION:
When presenting statistics or metrics, use infographic macros:
- \\circlestat{percentage}{label} for percentage displays
- \\circlestatcolor{percentage}{label}{color} for colored circles
- \\bigstat{NUMBER}{label} for large number callouts
- \\statrow{...}{...}{...} to arrange stats in a row
Place infographics between article sections for visual interest.
""",
            """PAGE CONTRAST AND VARIETY:
Create visual variety using dark/light page contrast:
- Use \\begin{darkpage}...\\end{darkpage} for impact pages (intros, features)
- Use \\begin{darksection}...\\end{darksection} for inline dark boxes
- Alternate between light and dark sections to create rhythm
- Use \\begin{accentpage}...\\end{accentpage} for colored accent pages
""",
            """PULL QUOTES:
Add pull quotes to break up long text sections:
- Use \\pullquote{quote text} for anonymous quotes
- Use \\pullquoteattr{quote text}{Author Name} with attribution
- Place at natural break points in articles
- Use sparingly - 1-2 per major article
""",
            """ARTICLE HEADERS:
Start articles with proper headers:
- Use \\articleheader{SECTION}{Title}{Byline} for full headers
- Use \\articletitle{Title} for simpler title-only headers
- Section tags should be small, bold, and colored (e.g., "FEATURE", "INTERVIEW")
""",
        ]


def get_magazine_preamble(theme: Optional[MagazineTheme] = None) -> str:
    """Convenience function to get full magazine preamble."""
    generator = MagazineLayoutGenerator(theme)
    return generator.get_full_preamble()


def get_magazine_requirements() -> List[str]:
    """Convenience function to get magazine requirements for LLM."""
    generator = MagazineLayoutGenerator()
    return generator.get_magazine_requirements()


if __name__ == "__main__":
    # Print the full preamble for testing
    print("=" * 60)
    print("MAGAZINE LAYOUT PREAMBLE")
    print("=" * 60)
    print(get_magazine_preamble())
    print("\n" + "=" * 60)
    print("MAGAZINE REQUIREMENTS")
    print("=" * 60)
    for i, req in enumerate(get_magazine_requirements(), 1):
        print(f"\n--- Requirement {i} ---")
        print(req)
