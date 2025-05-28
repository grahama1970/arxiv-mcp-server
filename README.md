# ArXivBot - Research Automation for ArXiv Papers

[![Python Version](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![MCP Protocol](https://img.shields.io/badge/MCP-Model%20Context%20Protocol-blue)](https://modelcontextprotocol.io)
[![CLI Tool](https://img.shields.io/badge/CLI-Typer%20Powered-green)](https://typer.tiangolo.com/)

> 🤖 **Automate your literature review** - A powerful research bot with 45+ tools that finds evidence to support or contradict your hypotheses across ArXiv papers

**Latest Update (v1.0.1)**: Fixed critical search function issue in MCP integration. Added diagnostics tool for troubleshooting.

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

### Installation Options

#### Option 1: Docker (Recommended for Production)
Best for users who want isolation and easy deployment. See [Docker Deployment Guide](docs/DOCKER_DEPLOYMENT.md) for details.

```bash
# Clone and run with Docker
git clone https://github.com/yourusername/arxiv-mcp-server.git
cd arxiv-mcp-server
docker compose up -d arxiv-mcp
```

#### Option 2: Local Installation
For development or users comfortable with Python environments.

```bash
# Clone the repository
git clone https://github.com/yourusername/arxiv-mcp-server.git
cd arxiv-mcp-server

# Install with uv (recommended)
uv sync

# Or install with pip
pip install -e .
```

### Quick Test (No API Keys Required!)

```bash
# Test search functionality
arxiv-cli search "quantum computing" --max-results 5

# Test with mock evidence extraction
arxiv-cli find-support "Quantum computers are faster" --all --provider mock

# Check server health and connectivity (new!)
arxiv-cli diagnostics
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

### Enable Semantic Search (Optional)

```bash
# Index downloaded papers for natural language search
arxiv-cli index-papers

# Search with natural language
arxiv-cli semantic-search "how do transformers handle long sequences"
```

### New: Daily Research Workflow

```bash
# Set up daily digest for your research area
arxiv-cli create-digest "My Research" \
  --keywords "transformer,attention" \
  --authors "Vaswani,Hinton" \
  --categories "cs.LG,cs.CL"

# Get your daily digest
arxiv-cli daily-digest --format markdown > today.md

# Add interesting papers to reading list
arxiv-cli add-reading 2401.12345 --priority high --tags "important"

# Track citations of your papers
arxiv-cli citations 1706.03762 --limit 20

# Export bibliography when writing
arxiv-cli export-reading --format bibtex --tags "my-paper" > refs.bib
```

### Enhanced Daily Workflow Features

```bash
# Check if your saved papers have been updated
arxiv-cli check-updates --all

# Follow your favorite researchers
arxiv-cli follow "Yoshua Bengio" --notes "Deep learning pioneer"
arxiv-cli check-authors --days 30

# Quick citation copying (multiple styles)
arxiv-cli copy-cite 1706.03762 --style apa  # Copies to clipboard!

# Save complex searches as templates
arxiv-cli save-search "ML Security" \
  --query "adversarial attacks" \
  --author "Goodfellow" \
  --category "cs.LG"
arxiv-cli run-search "ML Security"

# Organize papers by project
arxiv-cli create-collection "PhD Chapter 3" --desc "Attention mechanisms"
arxiv-cli add-to-collection 1706.03762 "PhD Chapter 3" --notes "Seminal paper"
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

### Semantic Search
- **index-papers** - Build search index with embeddings
- **semantic-search** - Natural language search across papers
- **search-stats** - View search database statistics

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

### MCP Configuration Options

**Option 1: Docker (Recommended)**
```json
{
    "mcpServers": {
        "arxiv-bot": {
            "command": "bash",
            "args": ["/path/to/arxiv-mcp-server/scripts/docker-mcp-wrapper.sh"]
        }
    }
}
```

**Option 2: Local Python**
```json
{
    "mcpServers": {
        "arxiv-bot": {
            "command": "python",
            "args": ["-m", "arxiv_mcp_server"]
        }
    }
}
```

Or with custom storage path:
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

The MCP server exposes all 45+ tools to AI assistants, allowing them to automate complex research workflows on your behalf, including:
- Reading list management and paper update checking
- Author following and new paper notifications  
- Daily digests with personalized filtering
- Citation tracking and quick citation copying
- Search templates for repeated queries
- Paper collections for project organization
- Export to all major reference managers

## 🔧 Troubleshooting

### Search Not Working?

If you're experiencing issues with the search function, use the diagnostics tool:

```bash
# Check server health
arxiv-cli diagnostics

# Output shows:
# - ArXiv API connectivity status
# - Storage path and statistics  
# - Python environment details
# - Any configuration issues
```

Common fixes:
- **Network Issues**: Ensure you can reach arxiv.org
- **Rate Limiting**: The server automatically handles rate limits with retries
- **Empty Results**: Try broader search terms or remove date filters

### MCP Integration Issues?

For Claude Desktop or other MCP clients showing "No result received":
1. Run `arxiv-cli diagnostics` to check server health
2. Check MCP server logs for detailed error messages
3. Ensure proper path configuration in your MCP settings

## ⚙️ Configuration

### Storage Location
```bash
export ARXIV_STORAGE_PATH=/path/to/your/papers
```

### LLM Providers (for advanced features)

ArXivBot works out of the box with a mock provider for testing. For production use with real AI analysis:

```bash
# For Gemini (recommended - has free tier)
export GEMINI_API_KEY=your-key

# For OpenAI
export OPENAI_API_KEY=your-key

# For Anthropic
export ANTHROPIC_API_KEY=your-key

# Default is mock provider (no API key needed)
arxiv-cli find-support "test hypothesis" --all  # Works without API keys!
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
│   ├── tools/              # 45+ automation tools
│   │   ├── research_support.py  # Bolster/contradict engine
│   │   ├── reading_list.py      # Paper organization
│   │   ├── daily_digest.py      # Filtered notifications
│   │   ├── citation_tracking.py # Citation networks
│   │   ├── export_references.py # BibTeX/RIS export
│   │   ├── paper_updates.py     # Version tracking
│   │   ├── author_follow.py     # Author monitoring
│   │   ├── quick_cite.py        # Citation copying
│   │   ├── search_templates.py  # Saved searches
│   │   ├── paper_collections.py # Project organization
│   │   └── ...
│   ├── converters/         # PDF processors  
│   ├── llm_providers.py    # AI integrations
│   ├── cli.py             # Command interface
│   └── server.py          # MCP server
├── examples/              # Automation examples
└── docs/                  # Documentation
```

## 📖 Documentation

- [Tools Reference](TOOLS_REFERENCE.md) - Complete list of all 30+ research automation tools
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