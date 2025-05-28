"""
ArXiv Search Engine - SQLite-based BM25 and semantic search.

Purpose:
    Provides lightweight search capabilities using SQLite FTS5 for BM25
    and sqlite-vec for semantic search. Implements hybrid search using
    Reciprocal Rank Fusion.

Links:
    - SQLite FTS5: https://www.sqlite.org/fts5.html
    - sqlite-vec: https://github.com/asg017/sqlite-vec
    - Sentence Transformers: https://www.sbert.net/

Sample input:
    paper_data = {
        "title": "Attention Is All You Need",
        "authors": ["Ashish Vaswani", "Noam Shazeer"],
        "abstract": "The dominant sequence transduction models...",
        "categories": ["cs.CL", "cs.LG"]
    }

Expected output:
    Search results with paper metadata and relevance scores
"""

import sqlite3
import json
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import logging

# Import compatibility checker
try:
    from ..utils.mac_compatibility import check_semantic_search_availability
except ImportError:
    # When running as standalone script
    import sys
    sys.path.append(str(Path(__file__).parent.parent))
    from utils.mac_compatibility import check_semantic_search_availability

logger = logging.getLogger(__name__)

# Check if we can use semantic search
_semantic_available, _semantic_message = check_semantic_search_availability()

# Conditionally import heavy ML dependencies
if _semantic_available:
    try:
        from sentence_transformers import SentenceTransformer
        logger.info("Sentence transformers loaded successfully")
    except ImportError as e:
        _semantic_available = False
        _semantic_message = f"Failed to import sentence-transformers: {e}"
        logger.warning(_semantic_message)
else:
    logger.info(f"Semantic search disabled: {_semantic_message}")


class ArxivSearchEngine:
    """SQLite-based search engine for ArXiv papers."""
    
    def __init__(self, db_path: str = "arxiv_papers.db"):
        """Initialize search engine with database connection."""
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.enable_load_extension(True)
        
        # Try to load sqlite-vec extension
        try:
            # First try the Python package method
            try:
                import sqlite_vec
                sqlite_vec.load(self.conn)
                self.vec_enabled = True
                logger.info("Loaded sqlite-vec via Python package")
            except ImportError:
                # Fall back to manual loading
                vec_paths = [
                    "vec0",
                    "./vec0",
                    "/usr/local/lib/vec0",
                    "/usr/lib/vec0",
                    "~/.local/lib/vec0"
                ]
                
                loaded = False
                for path in vec_paths:
                    try:
                        self.conn.load_extension(path)
                        loaded = True
                        logger.info(f"Loaded sqlite-vec extension from {path}")
                        break
                    except Exception:
                        continue
                        
                if not loaded:
                    logger.warning("Could not load sqlite-vec extension - semantic search disabled")
                    self.vec_enabled = False
                else:
                    self.vec_enabled = True
                
        except Exception as e:
            logger.warning(f"sqlite-vec extension not available: {e}")
            self.vec_enabled = False
            
        # Initialize sentence transformer model only if available
        self.model = None
        if _semantic_available and self.vec_enabled:
            try:
                self.model = SentenceTransformer("all-MiniLM-L6-v2")
                logger.info("Initialized sentence transformer model")
            except Exception as e:
                logger.warning(f"Could not initialize sentence transformer: {e}")
                self.vec_enabled = False
        elif not _semantic_available:
            logger.info(f"Sentence transformer not initialized: {_semantic_message}")
            self.vec_enabled = False
            
        self._setup_tables()
    
    def _setup_tables(self):
        """Create tables for papers, chunks, and search indices."""
        cur = self.conn.cursor()
        
        # Main papers table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS papers (
                paper_id TEXT PRIMARY KEY,
                title TEXT,
                authors TEXT,
                abstract TEXT,
                categories TEXT,
                published_date TEXT,
                pdf_path TEXT,
                markdown_path TEXT,
                json_path TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Paper chunks with section hierarchy
        cur.execute("""
            CREATE TABLE IF NOT EXISTS paper_chunks (
                chunk_id INTEGER PRIMARY KEY AUTOINCREMENT,
                paper_id TEXT,
                section_hash TEXT,
                section_title TEXT,
                section_level INTEGER,
                section_path TEXT,  -- JSON breadcrumb path
                content TEXT,
                chunk_index INTEGER,
                start_char INTEGER,
                end_char INTEGER,
                FOREIGN KEY (paper_id) REFERENCES papers(paper_id)
            )
        """)
        
        # FTS5 table for BM25 search
        cur.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts USING fts5(
                chunk_id UNINDEXED,
                paper_id UNINDEXED,
                title,
                content,
                section_title,
                tokenize="porter unicode61"
            )
        """)
        
        # Vector table for semantic search (only if vec extension available)
        if self.vec_enabled:
            try:
                # First check if table exists
                cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='chunk_embeddings'")
                if not cur.fetchone():
                    # Create regular table for embeddings
                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS chunk_embeddings (
                            chunk_id INTEGER PRIMARY KEY,
                            embedding BLOB
                        )
                    """)
            except Exception as e:
                logger.warning(f"Could not create embeddings table: {e}")
        
        self.conn.commit()
    
    def index_paper(self, paper_id: str, paper_data: Dict, chunks: List[Dict]):
        """Index a paper and its chunks."""
        cur = self.conn.cursor()
        
        # Insert paper metadata
        cur.execute("""
            INSERT OR REPLACE INTO papers 
            (paper_id, title, authors, abstract, categories, published_date, 
             pdf_path, markdown_path, json_path)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            paper_id,
            paper_data.get("title", ""),
            json.dumps(paper_data.get("authors", [])),
            paper_data.get("abstract", ""),
            json.dumps(paper_data.get("categories", [])),
            paper_data.get("published_date", ""),
            paper_data.get("pdf_path", ""),
            paper_data.get("markdown_path", ""),
            paper_data.get("json_path", "")
        ))
        
        # Process and index chunks
        # Show progress if available
        try:
            from tqdm import tqdm
            chunks_iter = tqdm(enumerate(chunks), total=len(chunks), desc=f"Indexing {paper_id}")
        except ImportError:
            chunks_iter = enumerate(chunks)
        
        for i, chunk in chunks_iter:
            # Insert chunk
            cur.execute("""
                INSERT INTO paper_chunks 
                (paper_id, section_hash, section_title, section_level,
                 section_path, content, chunk_index, start_char, end_char)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                paper_id,
                chunk.get("section_hash", ""),
                chunk.get("section_title", ""),
                chunk.get("section_level", 0),
                json.dumps(chunk.get("section_path", [])),
                chunk["content"],
                i,
                chunk.get("start_char", 0),
                chunk.get("end_char", 0)
            ))
            
            chunk_id = cur.lastrowid
            
            # Insert into FTS5
            cur.execute("""
                INSERT INTO chunks_fts (chunk_id, paper_id, title, content, section_title)
                VALUES (?, ?, ?, ?, ?)
            """, (
                chunk_id,
                paper_id,
                paper_data.get("title", ""),
                chunk["content"],
                chunk.get("section_title", "")
            ))
            
            # Generate and store embedding if vec extension and model are available
            if self.vec_enabled and self.model is not None:
                try:
                    # Encode with normalization for better cosine similarity
                    embedding = self.model.encode(chunk["content"], normalize_embeddings=True)
                    # Convert to numpy array and ensure it's float32
                    if hasattr(embedding, 'cpu'):
                        # Handle torch tensors
                        embedding = embedding.cpu().numpy()
                    embedding = np.array(embedding, dtype=np.float32)
                    cur.execute("""
                        INSERT INTO chunk_embeddings (chunk_id, embedding)
                        VALUES (?, ?)
                    """, (chunk_id, embedding.tobytes()))
                except Exception as e:
                    logger.warning(f"Failed to store embedding: {e}")
        
        self.conn.commit()
        logger.info(f"Indexed {len(chunks)} chunks for paper {paper_id}")
    
    def bm25_search(self, query: str, limit: int = 10, paper_filter: Optional[str] = None) -> List[Dict]:
        """Perform BM25 full-text search."""
        cur = self.conn.cursor()
        
        try:
            # Escape special characters for FTS5
            # Replace double quotes with spaces and ensure query is properly formatted
            fts_query = query.replace('"', ' ').replace("'", ' ')
            # If query has special characters, wrap each word in quotes
            if any(c in fts_query for c in ['(', ')', '-', '+', '*', '?']):
                words = fts_query.split()
                fts_query = ' '.join(f'"{word}"' for word in words if word)
            
            results = cur.execute("""
                SELECT 
                    c.chunk_id,
                    c.paper_id,
                    c.section_title,
                    c.content,
                    c.section_path,
                    p.title as paper_title,
                    p.authors,
                    bm25(chunks_fts) as score
                FROM chunks_fts f
                JOIN paper_chunks c ON f.chunk_id = c.chunk_id
                JOIN papers p ON c.paper_id = p.paper_id
                WHERE chunks_fts MATCH ?
                AND (? IS NULL OR c.paper_id = ?)
                ORDER BY bm25(chunks_fts)
                LIMIT ?
            """, (fts_query, paper_filter, paper_filter, limit)).fetchall()
            
            return [self._format_result(r) for r in results]
        except Exception as e:
            logger.error(f"BM25 search failed: {e}")
            return []
    
    def semantic_search(self, query: str, limit: int = 10, paper_filter: Optional[str] = None) -> List[Dict]:
        """Perform semantic vector search using cosine similarity."""
        if not self.vec_enabled:
            logger.warning("Semantic search not available - embeddings not enabled")
            return []
            
        if self.model is None:
            logger.warning(f"Semantic search not available: {_semantic_message}")
            return []
            
        try:
            # Encode query with normalization for cosine similarity
            query_embedding = self.model.encode(query, normalize_embeddings=True)
            
            cur = self.conn.cursor()
            
            # Get all embeddings (we'll compute similarity in Python)
            if paper_filter:
                results = cur.execute("""
                    SELECT 
                        e.chunk_id,
                        e.embedding,
                        c.paper_id,
                        c.section_title,
                        c.content,
                        c.section_path,
                        p.title as paper_title,
                        p.authors
                    FROM chunk_embeddings e
                    JOIN paper_chunks c ON e.chunk_id = c.chunk_id
                    JOIN papers p ON c.paper_id = p.paper_id
                    WHERE c.paper_id = ?
                """, (paper_filter,)).fetchall()
            else:
                results = cur.execute("""
                    SELECT 
                        e.chunk_id,
                        e.embedding,
                        c.paper_id,
                        c.section_title,
                        c.content,
                        c.section_path,
                        p.title as paper_title,
                        p.authors
                    FROM chunk_embeddings e
                    JOIN paper_chunks c ON e.chunk_id = c.chunk_id
                    JOIN papers p ON c.paper_id = p.paper_id
                """).fetchall()
            
            # Compute cosine similarities
            scored_results = []
            for row in results:
                chunk_id, embedding_blob, paper_id, section_title, content, section_path, paper_title, authors = row
                
                # Convert blob to numpy array
                chunk_embedding = np.frombuffer(embedding_blob, dtype=np.float32)
                
                # Normalize for cosine similarity
                chunk_embedding = chunk_embedding / np.linalg.norm(chunk_embedding)
                
                # Compute cosine similarity (dot product of normalized vectors)
                similarity = float(np.dot(query_embedding, chunk_embedding))
                
                scored_results.append({
                    "chunk_id": chunk_id,
                    "paper_id": paper_id,
                    "section_title": section_title,
                    "content": content,
                    "section_path": json.loads(section_path) if section_path else [],
                    "paper_title": paper_title,
                    "authors": json.loads(authors) if authors else [],
                    "score": similarity
                })
            
            # Sort by similarity score (descending) and return top results
            scored_results.sort(key=lambda x: x["score"], reverse=True)
            return scored_results[:limit]
            
        except Exception as e:
            logger.error(f"Semantic search failed: {e}")
            return []
    
    def hybrid_search(self, query: str, limit: int = 10, alpha: float = 0.5) -> List[Dict]:
        """Hybrid search using Reciprocal Rank Fusion."""
        # Get BM25 results
        bm25_results = self.bm25_search(query, limit * 2)
        bm25_ranks = {r["chunk_id"]: i + 1 for i, r in enumerate(bm25_results)}
        
        # Get semantic results if available
        if self.vec_enabled:
            semantic_results = self.semantic_search(query, limit * 2)
            semantic_ranks = {r["chunk_id"]: i + 1 for i, r in enumerate(semantic_results)}
        else:
            # Fall back to BM25 only
            return bm25_results[:limit]
        
        # Combine using RRF
        all_chunks = set(bm25_ranks.keys()) | set(semantic_ranks.keys())
        rrf_scores = {}
        
        for chunk_id in all_chunks:
            bm25_rank = bm25_ranks.get(chunk_id, limit * 2 + 1)
            semantic_rank = semantic_ranks.get(chunk_id, limit * 2 + 1)
            
            # RRF formula with alpha weighting
            rrf_scores[chunk_id] = (
                alpha / (60 + bm25_rank) + 
                (1 - alpha) / (60 + semantic_rank)
            )
        
        # Sort by RRF score and return top results
        sorted_chunks = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)[:limit]
        
        # Fetch full results for top chunks
        chunk_ids = [chunk_id for chunk_id, _ in sorted_chunks]
        return self._fetch_chunks_by_ids(chunk_ids)
    
    def _format_result(self, row: Tuple) -> Dict:
        """Format search result."""
        return {
            "chunk_id": row[0],
            "paper_id": row[1],
            "section_title": row[2],
            "content": row[3],
            "section_path": json.loads(row[4]) if row[4] else [],
            "paper_title": row[5],
            "authors": json.loads(row[6]) if row[6] else [],
            "score": row[7] if len(row) > 7 else None
        }
    
    def _fetch_chunks_by_ids(self, chunk_ids: List[int]) -> List[Dict]:
        """Fetch chunks by their IDs."""
        if not chunk_ids:
            return []
        
        placeholders = ",".join(["?" for _ in chunk_ids])
        cur = self.conn.cursor()
        
        results = cur.execute(f"""
            SELECT 
                c.chunk_id,
                c.paper_id,
                c.section_title,
                c.content,
                c.section_path,
                p.title as paper_title,
                p.authors
            FROM paper_chunks c
            JOIN papers p ON c.paper_id = p.paper_id
            WHERE c.chunk_id IN ({placeholders})
        """, chunk_ids).fetchall()
        
        # Maintain order from chunk_ids
        result_dict = {r[0]: r for r in results}
        return [self._format_result(result_dict[cid]) for cid in chunk_ids if cid in result_dict]
    
    def get_paper_chunks(self, paper_id: str) -> List[Dict]:
        """Get all chunks for a specific paper."""
        cur = self.conn.cursor()
        
        results = cur.execute("""
            SELECT 
                c.chunk_id,
                c.paper_id,
                c.section_title,
                c.content,
                c.section_path,
                p.title as paper_title,
                p.authors
            FROM paper_chunks c
            JOIN papers p ON c.paper_id = p.paper_id
            WHERE c.paper_id = ?
            ORDER BY c.chunk_index
        """, (paper_id,)).fetchall()
        
        return [self._format_result(r) for r in results]
    
    def get_stats(self) -> Dict[str, int]:
        """Get database statistics."""
        cur = self.conn.cursor()
        
        stats = {
            "total_papers": cur.execute("SELECT COUNT(*) FROM papers").fetchone()[0],
            "total_chunks": cur.execute("SELECT COUNT(*) FROM paper_chunks").fetchone()[0],
            "vec_enabled": self.vec_enabled
        }
        
        if self.vec_enabled:
            stats["total_embeddings"] = cur.execute(
                "SELECT COUNT(*) FROM chunk_embeddings"
            ).fetchone()[0]
            
        return stats


# Run validation when module is executed directly
if __name__ == "__main__":
    # Test with in-memory database
    engine = ArxivSearchEngine(":memory:")
    
    # Example: Index a paper
    paper_data = {
        "title": "Attention Is All You Need",
        "authors": ["Ashish Vaswani", "Noam Shazeer"],
        "abstract": "The dominant sequence transduction models...",
        "categories": ["cs.CL", "cs.LG"]
    }
    
    chunks = [
        {
            "section_hash": "abc123",
            "section_title": "Introduction",
            "section_level": 1,
            "section_path": [{"title": "Introduction", "level": 1}],
            "content": "Recurrent neural networks, long short-term memory..."
        }
    ]
    
    engine.index_paper("1706.03762", paper_data, chunks)
    
    # Test searches
    print("Testing BM25 search...")
    results = engine.bm25_search("recurrent neural networks")
    print(f"Found {len(results)} results")
    
    print("\nTesting hybrid search...")
    results = engine.hybrid_search("transformer architecture attention")
    for r in results:
        print(f"Paper: {r['paper_title']}")
        print(f"Section: {r['section_title']}")
        print(f"Content: {r['content'][:100]}...")
        print()
    
    print("\nDatabase stats:")
    print(json.dumps(engine.get_stats(), indent=2))
