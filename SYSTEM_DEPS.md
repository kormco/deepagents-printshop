# System Dependencies

DeepAgents PrintShop requires several non-pip system packages for full functionality. The `Dockerfile` is the canonical source for the complete dependency list.

## TeX Live (Required for PDF compilation)

### Ubuntu/Debian
```bash
sudo apt-get update
sudo apt-get install -y \
    texlive-latex-base \
    texlive-latex-extra \
    texlive-fonts-recommended \
    texlive-fonts-extra \
    texlive-science \
    texlive-plain-generic \
    latexmk
```

### macOS
```bash
# Full distribution (recommended)
brew install --cask mactex

# Minimal distribution
brew install texlive
```

### Windows
Download and install [MiKTeX](https://miktex.org/download) (recommended) or [TeX Live](https://tug.org/texlive/).

MiKTeX auto-installs missing LaTeX packages on first use. After installation verify with:
```
pdflatex --version
```

## Ghostscript (Image processing)

### Ubuntu/Debian
```bash
sudo apt-get install -y ghostscript
```

### macOS
```bash
brew install ghostscript
```

### Windows
Download from [ghostscript.com](https://ghostscript.com/releases/gsdnld.html) and add to PATH.

## Poppler (PDF to image conversion for Visual QA)

### Ubuntu/Debian
```bash
sudo apt-get install -y poppler-utils
```

### macOS
```bash
brew install poppler
```

### Windows
Download from [Poppler for Windows](https://github.com/oschwartz10612/poppler-windows/releases/) and add to PATH.

## ImageMagick (Image processing)

### Ubuntu/Debian
```bash
sudo apt-get install -y imagemagick
```

### macOS
```bash
brew install imagemagick
```

### Windows
Download from [imagemagick.org](https://imagemagick.org/script/download.php).

## Docker Alternative

All system dependencies are pre-installed in the Docker image. This is the simplest way to run the full pipeline:

```bash
docker-compose build
docker-compose run --rm deepagents-printshop python agents/qa_orchestrator/agent.py
```

See `Dockerfile` for the exact package versions used.
