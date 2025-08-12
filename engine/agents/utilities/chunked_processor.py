#!/usr/bin/env python3
"""
Chunked Processor for handling large legacy projects efficiently.

This module provides utilities for:
- Splitting large projects into manageable chunks
- Processing chunks in parallel with rate limiting
- Respecting Anthropic's ramp-up rules
- Making debugging easier by isolating failures
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Callable, Awaitable
from dataclasses import dataclass
from pathlib import Path
import time
from concurrent.futures import ThreadPoolExecutor
import json

logger = logging.getLogger(__name__)

@dataclass
class ChunkConfig:
    """Configuration for chunked processing."""
    max_files_per_chunk: int = 5
    max_tokens_per_chunk: int = 50000  # Conservative token limit
    max_parallel_chunks: int = 3  # Respect rate limits
    rate_limit_delay: float = 2.0  # Seconds between chunks
    retry_attempts: int = 3
    retry_delay: float = 5.0

@dataclass
class ProcessingChunk:
    """Represents a chunk of files to be processed."""
    chunk_id: str
    files: List[Dict[str, Any]]
    estimated_tokens: int
    priority: int = 0  # Higher priority chunks processed first

class ChunkedProcessor:
    """Handles chunked processing of large legacy projects."""
    
    def __init__(self, config: ChunkConfig = None):
        self.config = config or ChunkConfig()
        self.semaphore = asyncio.Semaphore(self.config.max_parallel_chunks)
        self.rate_limit_lock = asyncio.Lock()
        self.last_request_time = 0.0
        
    async def split_project_into_chunks(self, project_files: List[Dict[str, Any]]) -> List[ProcessingChunk]:
        """Split a project into manageable chunks based on file size and type."""
        chunks = []
        current_chunk = []
        current_tokens = 0
        chunk_id = 0
        
        # Sort files by priority (HTML files first, then others)
        sorted_files = sorted(project_files, key=self._get_file_priority, reverse=True)
        
        for file_info in sorted_files:
            file_tokens = self._estimate_tokens(file_info)
            
            # Check if adding this file would exceed chunk limits
            if (len(current_chunk) >= self.config.max_files_per_chunk or 
                current_tokens + file_tokens > self.config.max_tokens_per_chunk):
                
                # Create chunk from current files
                if current_chunk:
                    chunks.append(ProcessingChunk(
                        chunk_id=f"chunk_{chunk_id}",
                        files=current_chunk.copy(),
                        estimated_tokens=current_tokens,
                        priority=self._calculate_chunk_priority(current_chunk)
                    ))
                    chunk_id += 1
                
                # Start new chunk
                current_chunk = [file_info]
                current_tokens = file_tokens
            else:
                current_chunk.append(file_info)
                current_tokens += file_tokens
        
        # Add final chunk
        if current_chunk:
            chunks.append(ProcessingChunk(
                chunk_id=f"chunk_{chunk_id}",
                files=current_chunk.copy(),
                estimated_tokens=current_tokens,
                priority=self._calculate_chunk_priority(current_chunk)
            ))
        
        # Sort chunks by priority
        chunks.sort(key=lambda x: x.priority, reverse=True)
        
        logger.info(f"Split project into {len(chunks)} chunks")
        for chunk in chunks:
            logger.info(f"  {chunk.chunk_id}: {len(chunk.files)} files, ~{chunk.estimated_tokens} tokens")
        
        return chunks
    
    def _get_file_priority(self, file_info: Dict[str, Any]) -> int:
        """Calculate priority for file processing order."""
        file_path = file_info.get('file_path', '')
        file_type = file_info.get('file_type', '')
        
        # HTML files get highest priority (they're the main content)
        if file_path.lower().endswith('.html') or file_type == 'html':
            return 100
        
        # CSS files next (they define styling)
        if file_path.lower().endswith('.css') or file_type == 'css':
            return 80
        
        # JavaScript files
        if file_path.lower().endswith(('.js', '.jsx', '.ts', '.tsx')) or file_type in ['javascript', 'typescript']:
            return 60
        
        # Image files
        if file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.svg')):
            return 40
        
        # Other files
        return 20
    
    def _calculate_chunk_priority(self, files: List[Dict[str, Any]]) -> int:
        """Calculate overall priority for a chunk based on its files."""
        if not files:
            return 0
        
        # Average priority of files in the chunk
        total_priority = sum(self._get_file_priority(f) for f in files)
        return total_priority // len(files)
    
    def _estimate_tokens(self, file_info: Dict[str, Any]) -> int:
        """Estimate token count for a file."""
        content = file_info.get('content', '')
        if not content:
            return 1000  # Default estimate
        
        # Rough estimation: 1 token ≈ 4 characters
        return len(content) // 4
    
    async def process_chunks_parallel(
        self, 
        chunks: List[ProcessingChunk], 
        processor_func: Callable[[ProcessingChunk], Awaitable[Dict[str, Any]]]
    ) -> Dict[str, Any]:
        """Process chunks in parallel with rate limiting and error handling."""
        results = {
            'successful_chunks': [],
            'failed_chunks': [],
            'total_chunks': len(chunks),
            'processing_time': 0.0
        }
        
        start_time = time.time()
        
        # Create tasks for all chunks
        tasks = []
        for chunk in chunks:
            task = asyncio.create_task(
                self._process_chunk_with_retry(chunk, processor_func)
            )
            tasks.append(task)
        
        # Process chunks with rate limiting
        for i, task in enumerate(tasks):
            try:
                # Wait for rate limit
                await self._respect_rate_limit()
                
                # Process chunk
                chunk_result = await task
                
                if chunk_result.get('success', False):
                    results['successful_chunks'].append(chunk_result)
                    logger.info(f"✅ Chunk {chunk_result['chunk_id']} processed successfully")
                else:
                    results['failed_chunks'].append(chunk_result)
                    logger.error(f"❌ Chunk {chunk_result['chunk_id']} failed: {chunk_result.get('error', 'Unknown error')}")
                
            except Exception as e:
                logger.error(f"❌ Error processing chunk {i}: {e}")
                results['failed_chunks'].append({
                    'chunk_id': f"chunk_{i}",
                    'success': False,
                    'error': str(e)
                })
        
        results['processing_time'] = time.time() - start_time
        
        # Log summary
        logger.info(f"📊 Chunk processing complete:")
        logger.info(f"   ✅ Successful: {len(results['successful_chunks'])}")
        logger.info(f"   ❌ Failed: {len(results['failed_chunks'])}")
        logger.info(f"   ⏱️  Total time: {results['processing_time']:.2f}s")
        
        return results
    
    async def _process_chunk_with_retry(
        self, 
        chunk: ProcessingChunk, 
        processor_func: Callable[[ProcessingChunk], Awaitable[Dict[str, Any]]]
    ) -> Dict[str, Any]:
        """Process a single chunk with retry logic."""
        for attempt in range(self.config.retry_attempts):
            try:
                async with self.semaphore:
                    result = await processor_func(chunk)
                    result['chunk_id'] = chunk.chunk_id
                    result['attempt'] = attempt + 1
                    return result
                    
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1} failed for chunk {chunk.chunk_id}: {e}")
                
                if attempt < self.config.retry_attempts - 1:
                    await asyncio.sleep(self.config.retry_delay * (attempt + 1))
                else:
                    return {
                        'chunk_id': chunk.chunk_id,
                        'success': False,
                        'error': str(e),
                        'attempt': attempt + 1
                    }
        
        return {
            'chunk_id': chunk.chunk_id,
            'success': False,
            'error': 'Max retry attempts exceeded',
            'attempt': self.config.retry_attempts
        }
    
    async def _respect_rate_limit(self):
        """Ensure we respect rate limits between requests."""
        async with self.rate_limit_lock:
            current_time = time.time()
            time_since_last = current_time - self.last_request_time
            
            if time_since_last < self.config.rate_limit_delay:
                sleep_time = self.config.rate_limit_delay - time_since_last
                await asyncio.sleep(sleep_time)
            
            self.last_request_time = time.time()
    
    def merge_chunk_results(self, chunk_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Merge results from multiple chunks into a single result."""
        merged = {
            'status': 'success',
            'file_analyses': {},
            'patterns': [],
            'dependencies': {},
            'summary': {
                'total_files': 0,
                'successful_files': 0,
                'failed_files': 0,
                'total_chunks': len(chunk_results)
            }
        }
        
        for chunk_result in chunk_results:
            if not chunk_result.get('success', False):
                continue
            
            # Merge file analyses
            chunk_analyses = chunk_result.get('file_analyses', {})
            merged['file_analyses'].update(chunk_analyses)
            
            # Merge patterns
            chunk_patterns = chunk_result.get('patterns', [])
            merged['patterns'].extend(chunk_patterns)
            
            # Merge dependencies
            chunk_deps = chunk_result.get('dependencies', {})
            for dep_type, deps in chunk_deps.items():
                if dep_type not in merged['dependencies']:
                    merged['dependencies'][dep_type] = []
                merged['dependencies'][dep_type].extend(deps)
            
            # Update summary
            merged['summary']['total_files'] += len(chunk_analyses)
            merged['summary']['successful_files'] += len([a for a in chunk_analyses.values() if a.get('status') == 'success'])
        
        merged['summary']['failed_files'] = merged['summary']['total_files'] - merged['summary']['successful_files']
        
        # Deduplicate patterns
        merged['patterns'] = self._deduplicate_patterns(merged['patterns'])
        
        return merged
    
    def _deduplicate_patterns(self, patterns: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate patterns based on pattern name and type."""
        seen = set()
        unique_patterns = []
        
        for pattern in patterns:
            pattern_key = f"{pattern.get('name', '')}:{pattern.get('type', '')}"
            if pattern_key not in seen:
                seen.add(pattern_key)
                unique_patterns.append(pattern)
        
        return unique_patterns

class FileChunker:
    """Utility for splitting individual files into smaller pieces."""
    
    def __init__(self, max_chunk_size: int = 10000):
        self.max_chunk_size = max_chunk_size
    
    def split_large_file(self, file_path: str, content: str) -> List[Dict[str, Any]]:
        """Split a large file into smaller chunks."""
        if len(content) <= self.max_chunk_size:
            return [{'file_path': file_path, 'content': content, 'chunk_index': 0}]
        
        chunks = []
        lines = content.split('\n')
        current_chunk = []
        current_size = 0
        chunk_index = 0
        
        for line in lines:
            line_size = len(line) + 1  # +1 for newline
            
            if current_size + line_size > self.max_chunk_size and current_chunk:
                # Save current chunk
                chunks.append({
                    'file_path': f"{file_path}.part{chunk_index}",
                    'content': '\n'.join(current_chunk),
                    'chunk_index': chunk_index,
                    'original_file': file_path
                })
                chunk_index += 1
                current_chunk = [line]
                current_size = line_size
            else:
                current_chunk.append(line)
                current_size += line_size
        
        # Add final chunk
        if current_chunk:
            chunks.append({
                'file_path': f"{file_path}.part{chunk_index}",
                'content': '\n'.join(current_chunk),
                'chunk_index': chunk_index,
                'original_file': file_path
            })
        
        return chunks
    
    def merge_file_chunks(self, chunks: List[Dict[str, Any]]) -> str:
        """Merge file chunks back into original content."""
        # Sort by chunk index
        sorted_chunks = sorted(chunks, key=lambda x: x.get('chunk_index', 0))
        
        # Extract content
        content_parts = [chunk.get('content', '') for chunk in sorted_chunks]
        
        return '\n'.join(content_parts) 