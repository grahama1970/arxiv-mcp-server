# ArXivBot - Research Automation for ArXiv Papers

[![Python Version](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![MCP Protocol](https://img.shields.io/badge/MCP-Model%20Context%20Protocol-blue)](https://modelcontextprotocol.io)
[![CLI Tool](https://img.shields.io/badge/CLI-Typer%20Powered-green)](https://typer.tiangolo.com/)

> 🤖 **Automate your literature review** - A powerful research bot that finds evidence to support or contradict your hypotheses across ArXiv papers

ArXivBot is both a **CLI tool** for direct command-line research automation AND an **MCP server** for AI assistant integration. It automates the tedious parts of academic research: searching papers, extracting key information, finding supporting or contradicting evidence, and building a searchable knowledge base. Let the bot handle the grunt work while you focus on the science.

## 🎛️ Two Ways to Use ArXivBot

### 1. Direct CLI Usage
```bash
# Use ArXivBot directly from your terminal
arxiv-cli search "quantum computing" --max-results 10
arxiv-cli find-support "My hypothesis about X" --all
```

### 2. MCP Integration with AI Assistants
```json
// Connect to Claude or other AI assistants
{
    "mcpServers": {
        "arxiv-bot": {
            "command": "python",
            "args": ["-m", "arxiv_mcp_server"]
        }
    }
}
```

This dual interface means you can use ArXivBot standalone for automated workflows OR let AI assistants like Claude access its capabilities for more complex research tasks.

## 🎯 The Power of Bolster & Contradict

The killer feature of ArXivBot is its ability to automatically find evidence across multiple papers that either **supports (bolsters)** or **challenges (contradicts)** your research hypotheses:

```bash
# Test your hypothesis against the literature
arxiv-cli find-support "Quantum computers can solve NP-complete problems in polynomial time" \
  --all \
  --type both

# Output:
# SUPPORTING EVIDENCE (3 findings):
# • Paper 2401.12345: "Recent experiments demonstrate polynomial speedup for specific NP problems..."
# • Paper 2401.67890: "Our quantum algorithm achieves O(n²) complexity for subset sum..."
#
# CONTRADICTING EVIDENCE (7 findings):
# • Paper 2402.11111: "Theoretical limits show exponential lower bounds remain for general NP..."
# • Paper 2402.22222: "No quantum advantage observed in comprehensive NP-complete benchmarks..."
```

This feature alone can save days of manual paper reading by automatically identifying relevant passages across your entire paper library.

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/arxiv-bot.git
cd arxiv-bot

# Install with uv (recommended)
uv pip install -e .

# Or install with pip
pip install -e .
```

### Basic Automation Workflow

```bash
# 1. Bot searches for relevant papers
arxiv-cli search "transformer architecture" --max-results 20

# 2. Bot downloads them all
arxiv-cli batch-download --search "transformer architecture" --max 10

# 3. Bot finds evidence for your hypothesis
arxiv-cli find-support "Attention mechanisms improve model interpretability" --all

# 4. Bot extracts all citations for your bibliography
arxiv-cli extract-citations 2401.12345 --format bibtex >> refs.bib
```

## 💪 Core Automation Features

### 1. Evidence Mining (Bolster/Contradict)
The bot's most powerful feature - automatically mine papers for supporting or contradicting evidence:

```bash
# Find supporting evidence only
arxiv-cli find-support "Thermal storage at 600°C is feasible" --all --type bolster

# Find contradicting evidence only
arxiv-cli find-support "Thermal storage at 600°C is feasible" --all --type contradict

# Find both and build a balanced view
arxiv-cli find-support "Thermal storage at 600°C is feasible" --all --type both

# Search your findings database later
arxiv-cli search-findings "thermal storage" --type contradict
```

The bot analyzes papers section by section, extracting relevant excerpts with confidence scores and storing them in a searchable database.

### 2. Automated Literature Processing
Let the bot handle the repetitive tasks:

```bash
# Bot downloads papers matching your criteria
arxiv-cli batch-download --search "quantum error correction" --max 20

# Bot summarizes each paper
for paper in $(arxiv-cli list-papers); do
    arxiv-cli summarize $paper --type abstract >> summaries.txt
done

# Bot extracts all code examples
arxiv-cli analyze-code 2401.12345 --lang python --extract-functions
```

### 3. Research Validation Automation
Validate your research claims against the literature:

```bash
# Bot compares papers with your research
arxiv-cli compare 2401.12345 "My approach uses topological quantum codes"

# Bot finds similar papers to check for prior art
arxiv-cli find-similar 2401.12345 --type content --top 10
```

### 4. Knowledge Base Building
The bot automatically builds a searchable research database:

```bash
# Bot stores your insights
arxiv-cli add-note 2401.12345 "Contradicts our approach but methodology is sound" \
  --tag contradiction --tag methodology

# Bot searches your knowledge base
arxiv-cli search-findings "methodology" --top 20
```

## 🛠️ Complete Tool Arsenal

### Research Automation Tools
- **find-support** - Mine papers for supporting/contradicting evidence ⭐
- **search-findings** - Query your evidence database
- **batch-download** - Mass download papers matching criteria
- **compare** - Compare papers with your research

### Information Extraction
- **summarize** - Auto-generate paper summaries
- **extract-citations** - Extract bibliography in any format
- **extract-sections** - Pull specific sections from papers
- **analyze-code** - Extract and analyze code blocks

### Discovery & Organization
- **search** - Smart ArXiv search with filters
- **find-similar** - Discover related papers
- **add-note** - Build your knowledge base
- **list-notes** - Search your annotations

### Analysis Tools
- **describe-content** - AI description of figures/tables
- **conversion-options** - PDF processing options
- **system-stats** - Bot performance metrics

## 🔬 Research Automation Examples

### Hypothesis Testing Workflow
```bash
# Define your hypothesis
HYPOTHESIS="Transformer models scale linearly with data size"

# 1. Bot finds relevant papers
arxiv-cli search "transformer scaling laws" --max-results 30

# 2. Bot downloads them all
arxiv-cli batch-download --search "transformer scaling laws" --max 30

# 3. Bot finds all supporting evidence
arxiv-cli find-support "$HYPOTHESIS" --all --type bolster > supporting.txt

# 4. Bot finds all contradicting evidence  
arxiv-cli find-support "$HYPOTHESIS" --all --type contradict > contradicting.txt

# 5. Bot helps you analyze the balance
echo "Supporting: $(wc -l < supporting.txt) findings"
echo "Contradicting: $(wc -l < contradicting.txt) findings"
```

### Prior Art Search
```bash
# Your innovation
IDEA="Using attention mechanisms for time series forecasting"

# Bot searches for prior work
arxiv-cli find-support "$IDEA" --all --type bolster

# If bot finds many supporting cases, prior art exists
# If bot finds few/none, your idea might be novel!
```

### Literature Review Automation
```bash
# Bot builds your literature review
TOPIC="quantum machine learning"

# 1. Systematic search
arxiv-cli search "$TOPIC" --from 2020-01-01 --max-results 100

# 2. Bulk download
arxiv-cli batch-download --search "$TOPIC" --max 50

# 3. Extract key findings
arxiv-cli find-support "Quantum ML provides exponential speedup" --all

# 4. Generate bibliography
for paper in $(arxiv-cli list-papers); do
    arxiv-cli extract-citations $paper --format bibtex
done > bibliography.bib
```

## 🤖 MCP Server Integration

ArXivBot implements the Model Context Protocol (MCP), making all its tools available to AI assistants like Claude. This means you can ask Claude to use ArXivBot's capabilities naturally:

**Example Claude Interactions:**
- "Use ArXivBot to find papers that contradict the idea that quantum computers can break RSA"
- "Search for recent transformer papers and find evidence supporting attention mechanism efficiency"
- "Download papers about nuclear fusion and extract all their citations"

**MCP Configuration:**
```json
{
    "mcpServers": {
        "arxiv-bot": {
            "command": "python",
            "args": ["-m", "arxiv_mcp_server", "--storage-path", "/path/to/papers"]
        }
    }
}
```

The MCP server exposes all 17 tools to AI assistants, allowing them to automate complex research workflows on your behalf.

## ⚙️ Configuration

### Storage Location
```bash
export ARXIV_STORAGE_PATH=/path/to/your/papers
```

### LLM Providers (for advanced features)
```bash
# For OpenAI
export OPENAI_API_KEY=your-key

# For Anthropic
export ANTHROPIC_API_KEY=your-key

# Or use mock provider for testing
arxiv-cli find-support "test hypothesis" --provider mock
```

### PDF Conversion
```bash
# Fast mode (default)
arxiv-cli download 2401.12345 --converter pymupdf4llm

# Accurate mode (slower but better for tables/equations)
arxiv-cli download 2401.12345 --converter marker-pdf
```

## 🏗️ Architecture

```
arxiv-bot/
├── src/arxiv_mcp_server/
│   ├── tools/              # 17 automation tools
│   │   ├── research_support.py  # Bolster/contradict engine
│   │   ├── search.py
│   │   └── ...
│   ├── converters/         # PDF processors  
│   ├── llm_providers.py    # AI integrations
│   ├── cli.py             # Command interface
│   └── server.py          # MCP server
├── examples/              # Automation examples
└── docs/                  # Documentation
```

## 📖 Documentation

- [Quick Reference](docs/QUICK_REFERENCE.md) - All bot commands at a glance
- [Usage Guide](docs/USAGE_GUIDE.md) - Detailed automation workflows
- [Research Examples](examples/research_workflow.py) - Complete automation scripts

## 🤝 Contributing

Help make research automation even better:

1. Fork the repository
2. Create a feature branch
3. Follow [CLAUDE.md](docs/development/CLAUDE.md) coding standards
4. Submit a pull request

Ideas for contributions:
- Improve bolster/contradict detection algorithms
- Add new paper sources beyond ArXiv
- Create research workflow templates
- Enhance the evidence ranking system

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

---

<div align="center">

**ArXivBot** - Automating Literature Review Since 2024

*Let the bot read papers while you do science*

</div>