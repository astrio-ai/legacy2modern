"""
Repository Handler - Manages GitHub repositories, zip files, and complex project structures.

This module provides functionality to:
- Clone GitHub repositories
- Extract zip files
- Handle complex multi-folder legacy projects
- Prepare projects for modernization
"""

import os
import sys
import shutil
import tempfile
import zipfile
import logging
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from urllib.parse import urlparse
import requests

logger = logging.getLogger(__name__)

class RepositoryHandler:
    """
    Handles repository operations including GitHub cloning and zip extraction.
    """
    
    def __init__(self, work_dir: Optional[str] = None):
        """
        Initialize the repository handler.
        
        Args:
            work_dir: Working directory for temporary files (defaults to temp dir)
        """
        self.work_dir = Path(work_dir) if work_dir else Path(tempfile.mkdtemp(prefix="legacy2modern_"))
        self.temp_dirs = []
        
    def __del__(self):
        """Cleanup temporary directories."""
        self.cleanup()
    
    def cleanup(self):
        """Clean up temporary directories."""
        for temp_dir in self.temp_dirs:
            try:
                if temp_dir.exists():
                    shutil.rmtree(temp_dir)
                    logger.debug(f"Cleaned up temporary directory: {temp_dir}")
            except Exception as e:
                logger.warning(f"Failed to cleanup {temp_dir}: {e}")
    
    def prepare_project(self, input_source: str) -> Dict[str, Any]:
        """
        Prepare a project from various input sources.
        
        Args:
            input_source: Can be:
                - Local file path
                - Local directory path
                - GitHub repository URL
                - Zip file path
                
        Returns:
            Dict containing project information and prepared path
        """
        try:
            # Determine input type
            input_type = self._detect_input_type(input_source)
            
            if input_type == "github":
                return self._handle_github_repository(input_source)
            elif input_type == "zip":
                return self._handle_zip_file(input_source)
            elif input_type == "local_file":
                return self._handle_local_file(input_source)
            elif input_type == "local_directory":
                return self._handle_local_directory(input_source)
            else:
                raise ValueError(f"Unsupported input type: {input_type}")
                
        except Exception as e:
            logger.error(f"Error preparing project: {e}")
            raise
    
    def _detect_input_type(self, input_source: str) -> str:
        """Detect the type of input source."""
        # Check if it's a GitHub URL
        if input_source.startswith(('http://github.com/', 'https://github.com/', 'git@github.com:')):
            return "github"
        
        # Check if it's a zip file
        if input_source.lower().endswith('.zip'):
            return "zip"
        
        # Check if it's a local path
        path = Path(input_source)
        if path.exists():
            if path.is_file():
                return "local_file"
            elif path.is_dir():
                return "local_directory"
        
        # Try to parse as GitHub URL with different formats
        if 'github.com' in input_source:
            return "github"
        
        raise ValueError(f"Cannot determine input type for: {input_source}")
    
    def _handle_github_repository(self, repo_url: str) -> Dict[str, Any]:
        """Handle GitHub repository cloning."""
        try:
            # Parse GitHub URL
            repo_info = self._parse_github_url(repo_url)
            
            # Create temporary directory for cloning
            temp_dir = self.work_dir / f"repo_{repo_info['owner']}_{repo_info['repo']}"
            temp_dir.mkdir(parents=True, exist_ok=True)
            self.temp_dirs.append(temp_dir)
            
            # Clone the repository
            logger.info(f"Cloning repository: {repo_url}")
            clone_result = self._clone_repository(repo_url, temp_dir)
            
            if not clone_result['success']:
                raise Exception(f"Failed to clone repository: {clone_result['error']}")
            
            # Analyze the cloned repository
            project_info = self._analyze_project_structure(temp_dir, repo_info)
            
            return {
                'success': True,
                'project_path': str(temp_dir),
                'project_type': 'github_repository',
                'repository_info': repo_info,
                'project_info': project_info,
                'temp_directory': str(temp_dir)
            }
            
        except Exception as e:
            logger.error(f"Error handling GitHub repository: {e}")
            raise
    
    def _handle_zip_file(self, zip_path: str) -> Dict[str, Any]:
        """Handle zip file extraction."""
        try:
            zip_path = Path(zip_path)
            if not zip_path.exists():
                raise FileNotFoundError(f"Zip file not found: {zip_path}")
            
            # Create temporary directory for extraction
            temp_dir = self.work_dir / f"zip_{zip_path.stem}"
            temp_dir.mkdir(parents=True, exist_ok=True)
            self.temp_dirs.append(temp_dir)
            
            # Extract zip file
            logger.info(f"Extracting zip file: {zip_path}")
            self._extract_zip_file(zip_path, temp_dir)
            
            # Analyze the extracted project
            project_info = self._analyze_project_structure(temp_dir, {'name': zip_path.stem})
            
            return {
                'success': True,
                'project_path': str(temp_dir),
                'project_type': 'zip_archive',
                'archive_info': {
                    'name': zip_path.name,
                    'size': zip_path.stat().st_size
                },
                'project_info': project_info,
                'temp_directory': str(temp_dir)
            }
            
        except Exception as e:
            logger.error(f"Error handling zip file: {e}")
            raise
    
    def _handle_local_file(self, file_path: str) -> Dict[str, Any]:
        """Handle local file."""
        try:
            file_path = Path(file_path)
            if not file_path.exists():
                raise FileNotFoundError(f"File not found: {file_path}")
            
            # Create temporary directory and copy file
            temp_dir = self.work_dir / f"file_{file_path.stem}"
            temp_dir.mkdir(parents=True, exist_ok=True)
            self.temp_dirs.append(temp_dir)
            
            # Copy file to temp directory
            shutil.copy2(file_path, temp_dir / file_path.name)
            
            # Analyze the file
            project_info = self._analyze_project_structure(temp_dir, {'name': file_path.stem})
            
            return {
                'success': True,
                'project_path': str(temp_dir),
                'project_type': 'local_file',
                'file_info': {
                    'name': file_path.name,
                    'size': file_path.stat().st_size
                },
                'project_info': project_info,
                'temp_directory': str(temp_dir)
            }
            
        except Exception as e:
            logger.error(f"Error handling local file: {e}")
            raise
    
    def _handle_local_directory(self, dir_path: str) -> Dict[str, Any]:
        """Handle local directory."""
        try:
            dir_path = Path(dir_path)
            if not dir_path.exists() or not dir_path.is_dir():
                raise NotADirectoryError(f"Directory not found: {dir_path}")
            
            # Create temporary directory and copy contents
            temp_dir = self.work_dir / f"dir_{dir_path.name}"
            temp_dir.mkdir(parents=True, exist_ok=True)
            self.temp_dirs.append(temp_dir)
            
            # Copy directory contents
            self._copy_directory_contents(dir_path, temp_dir)
            
            # Analyze the project
            project_info = self._analyze_project_structure(temp_dir, {'name': dir_path.name})
            
            return {
                'success': True,
                'project_path': str(temp_dir),
                'project_type': 'local_directory',
                'directory_info': {
                    'name': dir_path.name,
                    'path': str(dir_path)
                },
                'project_info': project_info,
                'temp_directory': str(temp_dir)
            }
            
        except Exception as e:
            logger.error(f"Error handling local directory: {e}")
            raise
    
    def _parse_github_url(self, url: str) -> Dict[str, str]:
        """Parse GitHub URL to extract owner and repository name."""
        # Handle different GitHub URL formats
        if url.startswith('git@github.com:'):
            # SSH format: git@github.com:owner/repo.git
            path = url.replace('git@github.com:', '').replace('.git', '')
        elif url.startswith(('http://github.com/', 'https://github.com/')):
            # HTTPS format: https://github.com/owner/repo
            path = urlparse(url).path.strip('/')
        else:
            # Assume it's already in owner/repo format
            path = url
        
        # Split into owner and repo
        parts = path.split('/')
        if len(parts) >= 2:
            owner = parts[0]
            repo = parts[1].replace('.git', '')
        else:
            raise ValueError(f"Invalid GitHub URL format: {url}")
        
        return {
            'owner': owner,
            'repo': repo,
            'url': url
        }
    
    def _clone_repository(self, repo_url: str, target_dir: Path) -> Dict[str, Any]:
        """Clone a Git repository."""
        try:
            # Check if git is available
            if not self._is_git_available():
                raise Exception("Git is not installed or not available in PATH")
            
            # Clone the repository
            result = subprocess.run(
                ['git', 'clone', repo_url, str(target_dir)],
                capture_output=True,
                text=True,
                timeout=300  # 5 minutes timeout
            )
            
            if result.returncode != 0:
                return {
                    'success': False,
                    'error': result.stderr
                }
            
            return {
                'success': True,
                'output': result.stdout
            }
            
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'error': 'Repository cloning timed out'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _extract_zip_file(self, zip_path: Path, target_dir: Path):
        """Extract a zip file."""
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(target_dir)
            
            # Handle case where zip contains a single directory
            extracted_items = list(target_dir.iterdir())
            if len(extracted_items) == 1 and extracted_items[0].is_dir():
                # Move contents up one level
                single_dir = extracted_items[0]
                for item in single_dir.iterdir():
                    shutil.move(str(item), str(target_dir / item.name))
                single_dir.rmdir()
                
        except Exception as e:
            raise Exception(f"Failed to extract zip file: {e}")
    
    def _copy_directory_contents(self, source_dir: Path, target_dir: Path):
        """Copy directory contents recursively."""
        try:
            for item in source_dir.iterdir():
                if item.is_file():
                    shutil.copy2(item, target_dir / item.name)
                elif item.is_dir():
                    # Skip common directories that shouldn't be copied
                    if item.name not in ['.git', '__pycache__', 'node_modules', '.DS_Store']:
                        shutil.copytree(item, target_dir / item.name)
        except Exception as e:
            raise Exception(f"Failed to copy directory contents: {e}")
    
    def _analyze_project_structure(self, project_dir: Path, repo_info: Dict[str, str]) -> Dict[str, Any]:
        """Analyze the structure of a project."""
        try:
            # Get all files recursively
            all_files = []
            
            # Define directories to skip (performance optimization)
            skip_dirs = {
                '.git', '__pycache__', 'node_modules', '.DS_Store', 
                '.next', '.nuxt', 'dist', 'build', 'out', 'coverage',
                '.nyc_output', '.cache', 'tmp', 'temp', 'logs',
                'vendor', 'bower_components', '.pytest_cache',
                '.mypy_cache', '.tox', '.venv', 'venv', 'env',
                'target', '.gradle', '.idea', '.vscode'
            }
            
            for root, dirs, files in os.walk(project_dir):
                # Skip unnecessary directories for performance
                dirs[:] = [d for d in dirs if d not in skip_dirs]
                
                for file in files:
                    # Skip hidden files and common build artifacts
                    if not file.startswith('.') and not file.endswith(('.log', '.tmp', '.temp')):
                        file_path = Path(root) / file
                        all_files.append(str(file_path.relative_to(project_dir)))
            
            # Categorize files by type
            file_categories = self._categorize_files(all_files)
            
            # Detect project type
            project_type = self._detect_project_type(file_categories)
            
            # Get project metadata
            metadata = self._extract_project_metadata(project_dir, repo_info)
            
            return {
                'total_files': len(all_files),
                'file_categories': file_categories,
                'project_type': project_type,
                'metadata': metadata,
                'structure': {
                    'files': all_files,
                    'directories': self._get_directory_structure(project_dir)
                }
            }
            
        except Exception as e:
            logger.error(f"Error analyzing project structure: {e}")
            return {
                'total_files': 0,
                'file_categories': {},
                'project_type': 'unknown',
                'metadata': {},
                'structure': {'files': [], 'directories': {}}
            }
    
    def _categorize_files(self, files: List[str]) -> Dict[str, List[str]]:
        """Categorize files by type."""
        categories = {
            'html': [],
            'css': [],
            'javascript': [],
            'images': [],
            'documents': [],
            'config': [],
            'binary': [],
            'other': []
        }
        
        for file_path in files:
            file_lower = file_path.lower()
            
            if file_lower.endswith(('.html', '.htm')):
                categories['html'].append(file_path)
            elif file_lower.endswith(('.css', '.scss', '.sass', '.less')):
                categories['css'].append(file_path)
            elif file_lower.endswith(('.js', '.jsx', '.ts', '.tsx')):
                categories['javascript'].append(file_path)
            elif file_lower.endswith(('.jpg', '.jpeg', '.png', '.gif', '.svg', '.ico', '.webp')):
                categories['images'].append(file_path)
            elif file_lower.endswith(('.pdf', '.doc', '.docx', '.txt', '.md')):
                categories['documents'].append(file_path)
            elif file_lower.endswith(('.json', '.xml', '.yaml', '.yml', '.toml', '.ini', '.conf')):
                categories['config'].append(file_path)
            elif file_lower.endswith(('.m4a', '.mp3', '.wav', '.mp4', '.avi', '.mov', '.zip', '.tar', '.gz', '.rar', '.7z')):
                categories['binary'].append(file_path)
            else:
                categories['other'].append(file_path)
        
        return categories
    
    def _detect_project_type(self, file_categories: Dict[str, List[str]]) -> str:
        """Detect the type of project based on file categories."""
        html_count = len(file_categories['html'])
        js_count = len(file_categories['javascript'])
        css_count = len(file_categories['css'])
        
        if html_count > 0 and js_count == 0 and css_count == 0:
            return 'static_html'
        elif html_count > 0 and (js_count > 0 or css_count > 0):
            return 'web_application'
        elif js_count > 0 and html_count == 0:
            return 'javascript_library'
        elif len(file_categories['config']) > 0:
            return 'configured_project'
        else:
            return 'mixed_content'
    
    def _extract_project_metadata(self, project_dir: Path, repo_info: Dict[str, str]) -> Dict[str, Any]:
        """Extract project metadata from various sources."""
        metadata = {
            'name': repo_info.get('name', project_dir.name),
            'description': '',
            'version': '',
            'dependencies': [],
            'scripts': {}
        }
        
        # Try to read package.json
        package_json = project_dir / 'package.json'
        if package_json.exists():
            try:
                import json
                with open(package_json, 'r') as f:
                    package_data = json.load(f)
                    metadata.update({
                        'name': package_data.get('name', metadata['name']),
                        'description': package_data.get('description', ''),
                        'version': package_data.get('version', ''),
                        'dependencies': list(package_data.get('dependencies', {}).keys()),
                        'scripts': package_data.get('scripts', {})
                    })
            except Exception as e:
                logger.warning(f"Failed to read package.json: {e}")
        
        # Try to read README files
        readme_files = ['README.md', 'README.txt', 'readme.md', 'readme.txt']
        for readme_name in readme_files:
            readme_path = project_dir / readme_name
            if readme_path.exists():
                try:
                    with open(readme_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        if not metadata['description'] and len(content) > 0:
                            # Extract first paragraph as description
                            lines = content.split('\n')
                            description_lines = []
                            for line in lines:
                                if line.strip() and not line.startswith('#'):
                                    description_lines.append(line.strip())
                                if len(description_lines) >= 3:
                                    break
                            metadata['description'] = ' '.join(description_lines)
                except Exception as e:
                    logger.warning(f"Failed to read {readme_name}: {e}")
                break
        
        return metadata
    
    def _get_directory_structure(self, project_dir: Path) -> Dict[str, Any]:
        """Get the directory structure of the project."""
        structure = {}
        
        # Define directories to skip (performance optimization)
        skip_dirs = {
            '.git', '__pycache__', 'node_modules', '.DS_Store', 
            '.next', '.nuxt', 'dist', 'build', 'out', 'coverage',
            '.nyc_output', '.cache', 'tmp', 'temp', 'logs',
            'vendor', 'bower_components', '.pytest_cache',
            '.mypy_cache', '.tox', '.venv', 'venv', 'env',
            'target', '.gradle', '.idea', '.vscode'
        }
        
        for root, dirs, files in os.walk(project_dir):
            # Skip unnecessary directories for performance
            dirs[:] = [d for d in dirs if d not in skip_dirs]
            
            rel_path = Path(root).relative_to(project_dir)
            if str(rel_path) == '.':
                rel_path = Path('.')
            
            structure[str(rel_path)] = {
                'directories': dirs,
                'files': [f for f in files if not f.startswith('.') and not f.endswith(('.log', '.tmp', '.temp'))]
            }
        
        return structure
    
    def _is_git_available(self) -> bool:
        """Check if Git is available in the system."""
        try:
            result = subprocess.run(['git', '--version'], capture_output=True, text=True)
            return result.returncode == 0
        except Exception:
            return False
    
    def get_project_summary(self, project_info: Dict[str, Any]) -> str:
        """Generate a human-readable project summary."""
        summary_parts = []
        
        # Basic info
        summary_parts.append(f"Project: {project_info['metadata']['name']}")
        if project_info['metadata']['description']:
            summary_parts.append(f"Description: {project_info['metadata']['description']}")
        
        # File statistics
        file_cats = project_info['file_categories']
        summary_parts.append(f"Total files: {project_info['total_files']}")
        summary_parts.append(f"HTML files: {len(file_cats['html'])}")
        summary_parts.append(f"CSS files: {len(file_cats['css'])}")
        summary_parts.append(f"JavaScript files: {len(file_cats['javascript'])}")
        summary_parts.append(f"Images: {len(file_cats['images'])}")
        summary_parts.append(f"Binary files: {len(file_cats['binary'])}")
        
        # Analysis strategy
        text_files = len(file_cats['html']) + len(file_cats['css']) + len(file_cats['javascript']) + len(file_cats['config'])
        binary_files = len(file_cats['images']) + len(file_cats['binary'])
        summary_parts.append(f"Analysis strategy: {text_files} text files to analyze, {binary_files} binary files to preserve")
        
        # Project type
        summary_parts.append(f"Detected type: {project_info['project_type']}")
        
        # Performance optimization note
        summary_parts.append(f"Performance: Skipped node_modules and build directories for faster analysis")
        
        return "\n".join(summary_parts)
    
    def get_skipped_directories(self) -> List[str]:
        """Get list of directories that are skipped for performance optimization."""
        return [
            '.git', '__pycache__', 'node_modules', '.DS_Store', 
            '.next', '.nuxt', 'dist', 'build', 'out', 'coverage',
            '.nyc_output', '.cache', 'tmp', 'temp', 'logs',
            'vendor', 'bower_components', '.pytest_cache',
            '.mypy_cache', '.tox', '.venv', 'venv', 'env',
            'target', '.gradle', '.idea', '.vscode'
        ] 