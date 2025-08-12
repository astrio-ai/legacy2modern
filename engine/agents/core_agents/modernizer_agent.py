"""
Modernizer Agent - Generates new code using chosen stack/template.
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from .base_agent import BaseAgent, AgentRole
from ..utilities.prompt import PromptContext
from ..utilities.icon_handler import IconHandler

logger = logging.getLogger(__name__)

class ModernizerAgent(BaseAgent):
    """
    Modernizer Agent - Generates modern code from legacy analysis.
    
    This agent is responsible for:
    - Converting legacy code to modern frameworks
    - Generating new code using chosen technology stack
    - Applying modern best practices and patterns
    - Creating component-based architectures
    - Implementing responsive and accessible designs
    """
    
    def __init__(self, ai, memory, config, **kwargs):
        super().__init__(
            name="ModernizerAgent",
            role=AgentRole.MODERNIZER,
            ai=ai,
            memory=memory,
            config=config,
            **kwargs
        )
        
        # Initialize prompt builder
        from ..utilities.prompt import PromptBuilder
        self.prompt_builder = PromptBuilder()
        
        # Initialize icon handler
        self.icon_handler = IconHandler()
        
        self.generated_files = {}
        self.templates_used = {}
        self.conversion_mappings = {}
        
    def _get_default_system_prompt(self) -> str:
        """Return the default system prompt for the modernizer agent."""
        return """You are a Modernizer Agent specialized in converting legacy code to modern frameworks and technologies.

Your primary responsibilities:
1. Convert legacy code to modern frameworks (React, Next.js, Astro, etc.)
2. Apply modern best practices and design patterns
3. Generate clean, maintainable, and performant code
4. Implement responsive and accessible designs
5. Use modern tooling and development practices

You should focus on creating high-quality, production-ready code that follows modern standards."""
    
    async def process_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Process incoming messages for the modernizer agent."""
        message_type = message.get('type', 'unknown')
        
        if message_type == 'generate_code':
            return await self._generate_code(message.get('source_file', ''), message.get('target_stack', ''))
        elif message_type == 'convert_file':
            return await self._convert_file(message.get('file_path', ''), message.get('content', ''))
        elif message_type == 'create_component':
            return await self._create_component(message.get('component_name', ''), message.get('specs', {}))
        elif message_type == 'generate_project_structure':
            return await self._generate_project_structure(message.get('project_map', {}))
        else:
            return {
                'type': 'error',
                'message': f'Unknown message type: {message_type}'
            }
    
    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a specific task assigned to the modernizer agent."""
        task_type = task.get('type', 'unknown')
        
        if task_type == 'full_modernization':
            return await self._perform_full_modernization(task)
        elif task_type == 'file_conversion':
            return await self._convert_single_file(task)
        elif task_type == 'component_generation':
            return await self._generate_components(task)
        elif task_type == 'project_setup':
            return await self._setup_modern_project(task)
        else:
            return {
                'success': False,
                'error': f'Unknown task type: {task_type}'
            }
    
    async def _perform_full_modernization(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Perform full modernization of a project using chunked processing."""
        try:
            self.state.current_task = "full_modernization"
            self.update_progress(0.1)
            
            # Get architecture blueprint from architect agent
            architecture_blueprint = await self.memory.get('architecture_blueprint', {})
            if not architecture_blueprint:
                return {
                    'success': False,
                    'error': 'No architecture blueprint available. Run architect agent first.'
                }
            
            # Get project map from parser agent for content analysis
            project_map = await self.memory.get('project_map', {})
            if not project_map:
                return {
                    'success': False,
                    'error': 'No project map available. Run parser agent first.'
                }
            
            target_stack = self.config.get_target_stack()
            self.update_progress(0.2)
            
            # Step 1: Generate components using chunked processing
            logger.info("Generating modern components using chunked processing")
            components = await self._generate_modern_components_chunked(
                architecture_blueprint, project_map, target_stack
            )
            self.update_progress(0.7)
            
            # Step 2: Create configuration files
            logger.info("Creating configuration files")
            config_files = await self._create_configuration_files(target_stack)
            self.update_progress(1.0)
            
            # Combine all results
            modernization_result = {
                'architecture_blueprint': architecture_blueprint,
                'components': components,
                'config_files': config_files,
                'target_stack': target_stack
            }
            
            # Store results
            self.generated_files = modernization_result
            await self.memory.set('modernization_result', modernization_result)
            
            return {
                'success': True,
                'modernization_result': modernization_result,
                'message': 'Full modernization completed successfully using chunked processing'
            }
            
        except Exception as e:
            logger.error(f"Error in full modernization: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _generate_modern_components_chunked(self, architecture_blueprint: Dict, project_map: Dict, target_stack: str) -> Dict[str, Any]:
        """Generate modern components using chunked processing for better performance and error handling."""
        try:
            from ..utilities.chunked_processor import ChunkedProcessor, ChunkConfig
            
            # Extract architecture information
            folder_structure = architecture_blueprint.get('folderStructure', {})
            component_mapping = architecture_blueprint.get('mapping', {})
            routing_structure = architecture_blueprint.get('routing', [])
            shared_components = architecture_blueprint.get('sharedComponents', [])
            patterns = architecture_blueprint.get('patterns', [])
            
            # Extract project information for content analysis
            file_analyses = project_map.get('file_analyses', {})
            
            # Convert file analyses to chunk format
            file_infos = []
            for file_path, analysis in file_analyses.items():
                if analysis.get('status') == 'success':
                    file_infos.append({
                        'file_path': file_path,
                        'analysis': analysis,
                        'content': analysis.get('ai_analysis', ''),
                        'file_type': analysis.get('file_type', 'unknown')
                    })
            
            # Configure chunked processing for modernization
            config = ChunkConfig(
                max_files_per_chunk=3,  # Smaller chunks for modernization (more complex)
                max_tokens_per_chunk=30000,  # Conservative token limit
                max_parallel_chunks=2,  # Fewer parallel chunks for modernization
                rate_limit_delay=3.0,  # Longer delay for modernization
                retry_attempts=3,
                retry_delay=5.0
            )
            
            processor = ChunkedProcessor(config)
            
            # Split files into chunks
            chunks = await processor.split_project_into_chunks(file_infos)
            
            # Process chunks in parallel
            chunk_results = await processor.process_chunks_parallel(
                chunks, 
                lambda chunk: self._process_modernization_chunk(chunk, architecture_blueprint, target_stack)
            )
            
            # Merge results from all chunks
            all_components = {}
            for chunk_result in chunk_results['successful_chunks']:
                chunk_components = chunk_result.get('components', {})
                all_components.update(chunk_components)
            
            logger.info(f"Chunked modernization complete: {len(chunk_results['successful_chunks'])} successful, {len(chunk_results['failed_chunks'])} failed")
            logger.info(f"Generated {len(all_components)} components")
            
            return {
                'status': 'success',
                'target_stack': target_stack,
                'component_files': all_components,
                'component_list': list(all_components.keys()),
                'chunk_processing_stats': {
                    'total_chunks': chunk_results['total_chunks'],
                    'successful_chunks': len(chunk_results['successful_chunks']),
                    'failed_chunks': len(chunk_results['failed_chunks']),
                    'processing_time': chunk_results['processing_time']
                }
            }
            
        except Exception as e:
            logger.error(f"Error in chunked modernization: {e}")
            # Fallback to legacy method
            logger.warning("Falling back to legacy modernization method")
            return await self._generate_modern_components_from_blueprint(architecture_blueprint, project_map, target_stack)
    
    async def _process_modernization_chunk(self, chunk, architecture_blueprint: Dict, target_stack: str) -> Dict[str, Any]:
        """Process a single chunk for modernization."""
        try:
            components = {}
            
            for file_info in chunk.files:
                file_path = file_info.get('file_path', '')
                analysis = file_info.get('analysis', {})
                
                # Convert file to modern component
                if file_path.lower().endswith('.html') and analysis.get('is_single_page_multi_section', False):
                    # Handle HTML files with virtual pages
                    result = await self._convert_html_with_sections(file_path, analysis, target_stack)
                    if result.get('status') == 'success':
                        components.update(result.get('generated_components', {}))
                else:
                    # Handle regular files
                    result = await self._convert_regular_file(file_path, analysis, target_stack)
                    if result.get('status') == 'success':
                        components[file_path] = result.get('converted_content', '')
            
            return {
                'success': True,
                'components': components
            }
            
        except Exception as e:
            logger.error(f"Error processing modernization chunk {chunk.chunk_id}: {e}")
            return {
                'success': False,
                'error': str(e),
                'components': {}
            }
    
    async def _generate_modern_components_from_blueprint(self, architecture_blueprint: Dict, project_map: Dict, target_stack: str) -> Dict[str, Any]:
        """Generate modern components based on architecture blueprint."""
        try:
            # Extract architecture information
            folder_structure = architecture_blueprint.get('folderStructure', {})
            component_mapping = architecture_blueprint.get('mapping', {})
            routing_structure = architecture_blueprint.get('routing', [])
            shared_components = architecture_blueprint.get('sharedComponents', [])
            patterns = architecture_blueprint.get('patterns', [])  # Add patterns field
            
            # Extract project information for content analysis
            file_analyses = project_map.get('file_analyses', {})
            
            # Build context for component generation
            context = PromptContext(
                project_name=self.config.get_project_name(),
                target_stack=target_stack,
                current_task="component_generation_from_blueprint",
                user_requirements="Generate modern React components based on the architecture blueprint"
            )
            
            # Build prompt
            prompt_result = self.prompt_builder.build_modernization_prompt(
                context, task_type="generation"
            )
            
            # Create component generation prompt based on blueprint
            component_prompt = f"""
{prompt_result.user_prompt}

ARCHITECTURE BLUEPRINT:
Folder Structure: {folder_structure}
Component Mapping: {component_mapping}
Routing Structure: {routing_structure}
Shared Components: {shared_components}
Patterns: {patterns}

LEGACY CONTENT ANALYSIS:
{file_analyses}

REQUIREMENTS:
1. Generate components EXACTLY as specified in the architecture blueprint
2. Follow the folder structure and file naming conventions
3. Implement the routing structure as defined
4. Create shared components as identified
5. Use the legacy content analysis to implement actual functionality
6. Use modern {target_stack} patterns and best practices
7. Generate complete, runnable code (not templates)

COMPONENT GENERATION STRATEGY:
- Generate each component file as specified in the mapping
- Implement routing based on the routing structure
- Create shared components for reuse across pages
- Use Tailwind CSS for styling
- Follow React best practices and conventions

IMPORTANT: You MUST generate SEPARATE component files with proper file headers.

For each component file, start with a comment line like this:
// src/components/Navigation.jsx
// src/pages/Home.jsx
// src/styles/globals.css
// public/index.html

Then provide the complete code for that component.

IMPORTANT: Generate ONLY the actual code content. Do NOT include:
- Markdown code blocks (```tsx, ```jsx, etc.)
- Explanatory text or commentary
- Numbered lists or step-by-step instructions
- "Here's the code:" or similar phrases

IMPORTANT: For CSS files:
- Do NOT reference image files that don't exist
- Use CSS gradients or solid colors instead of background images
- Use Tailwind CSS classes when possible

IMPORTANT: For React components:
- Use valid href values for links (not just "#")
- Add proper accessibility attributes (target="_blank", rel="noopener noreferrer")
- Follow React best practices

Provide ONLY the clean, runnable code that can be directly saved to the proper directory structure.
"""
            
            # Get AI response
            components_response = await self.ai.chat(
                messages=[{'role': 'user', 'content': component_prompt}],
                system_prompt=prompt_result.system_prompt
            )
            
            # Parse components
            components = self._parse_components(components_response, target_stack)
            
            return components
            
        except Exception as e:
            logger.error(f"Error generating components from blueprint: {e}")
            return {
                'error': str(e),
                'status': 'failed'
            }

    
    async def _create_configuration_files(self, target_stack: str) -> Dict[str, Any]:
        """Create configuration files for the modern project."""
        try:
            config_files = {}
            
            # Generate package.json for Node.js projects
            if target_stack in ['react', 'nextjs', 'astro', 'vue', 'svelte']:
                package_json = await self._generate_package_json(target_stack)
                config_files['package.json'] = package_json
            
            # Generate configuration files based on stack
            if target_stack == 'nextjs':
                next_config = await self._generate_nextjs_config()
                config_files['next.config.js'] = next_config
            elif target_stack == 'astro':
                astro_config = await self._generate_astro_config()
                config_files['astro.config.mjs'] = astro_config
            
            # Generate TypeScript config if needed
            if self.config.get_code_quality_setting('use_typescript', True):
                ts_config = await self._generate_typescript_config(target_stack)
                config_files['tsconfig.json'] = ts_config
            
            # Generate ESLint config
            if self.config.get_code_quality_setting('use_eslint', True):
                eslint_config = await self._generate_eslint_config(target_stack)
                config_files['.eslintrc.json'] = eslint_config
            
            # Generate Prettier config
            if self.config.get_code_quality_setting('use_prettier', True):
                prettier_config = await self._generate_prettier_config()
                config_files['.prettierrc'] = prettier_config
            
            # Generate .gitignore
            gitignore = await self._generate_gitignore()
            config_files['.gitignore'] = gitignore
            
            # Generate README.md
            project_name = self.config.get_project_name()
            readme = await self._generate_readme(project_name)
            config_files['README.md'] = readme
            
            # Generate Vite config for React projects
            if target_stack == 'react':
                vite_config = await self._generate_vite_config()
                config_files['vite.config.js'] = vite_config
                
                # Generate Tailwind config
                tailwind_config = await self._generate_tailwind_config()
                config_files['tailwind.config.js'] = tailwind_config
                
                # Generate public files for React
                public_index = await self._generate_public_index_html()
                config_files['public/index.html'] = public_index
                
                public_manifest = await self._generate_public_manifest_json()
                config_files['public/manifest.json'] = public_manifest
            
            return config_files
            
        except Exception as e:
            logger.error(f"Error creating configuration files: {e}")
            return {
                'error': str(e),
                'status': 'failed'
            }
    
    async def _generate_package_json(self, target_stack: str) -> Dict[str, Any]:
        """Generate package.json for the target stack."""
        try:
            import json
            project_name = self.config.get_project_name()
            
            # Create specific package.json based on target stack
            if target_stack == 'react':
                package_json_content = {
                    "name": project_name.lower().replace(' ', '-'),
                    "version": "1.0.0",
                    "description": f"Modernized {project_name} using React",
                    "main": "src/index.js",
                    "scripts": {
                        "dev": "vite",
                        "build": "vite build",
                        "preview": "vite preview"
                    },
                    "dependencies": {
                        "react": "^18.2.0",
                        "react-dom": "^18.2.0",
                        "react-router-dom": "^6.16.0"
                    },
                    "devDependencies": {
                        "@vitejs/plugin-react": "^4.0.4",
                        "autoprefixer": "^10.4.15",
                        "postcss": "^8.4.29",
                        "tailwindcss": "^3.3.3",
                        "vite": "^4.4.9"
                    }
                }
            else:
                # Generic package.json for other frameworks
                package_json_content = {
                    "name": project_name.lower().replace(' ', '-'),
                    "version": "1.0.0",
                    "description": f"Modernized {project_name} using {target_stack}",
                    "main": "src/main.jsx",
                    "scripts": {
                        "start": "npm run dev",
                        "dev": "echo 'Add your dev script here'",
                        "build": "echo 'Add your build script here'"
                    },
                    "dependencies": {},
                    "devDependencies": {}
                }
            
            return {
                'status': 'success',
                'content': json.dumps(package_json_content, indent=2),
                'target_stack': target_stack
            }
            
        except Exception as e:
            logger.error(f"Error generating package.json: {e}")
            return {
                'error': str(e),
                'status': 'failed'
            }
    
    def _extract_code_from_response(self, response: str) -> str:
        """Extract actual code content from LLM response, removing markdown and commentary."""
        import re
        
        # Remove LLM commentary before code blocks
        lines = response.split('\n')
        code_lines = []
        in_code_block = False
        code_block_content = []
        
        for line in lines:
            # Check for code block start
            if line.strip().startswith('```'):
                if not in_code_block:
                    in_code_block = True
                    code_block_content = []
                else:
                    # End of code block, add the content
                    if code_block_content:
                        code_lines.extend(code_block_content)
                        code_lines.append('')  # Add empty line between blocks
                    in_code_block = False
                continue
            
            if in_code_block:
                code_block_content.append(line)
            elif not line.strip().startswith(('I\'ll help', 'Based on', 'Here\'s', 'These components', 'To use', 'This modernized')):
                # Skip common LLM commentary lines
                if line.strip() and not line.strip().isdigit() and not line.strip().endswith(':'):
                    code_lines.append(line)
        
        # If we have code content, return it
        if code_lines:
            return '\n'.join(code_lines).strip()
        
        # Fallback: try to extract any code-like content
        code_pattern = r'```(?:tsx?|jsx?|js|ts)?\s*\n(.*?)\n```'
        matches = re.findall(code_pattern, response, re.DOTALL)
        if matches:
            return '\n\n'.join(matches).strip()
        
        return response.strip()
    
    def _split_components_from_response(self, response: str) -> Dict[str, str]:
        """Split multiple components from a single response into separate files."""
        import re
        
        components = {}
        lines = response.split('\n')
        current_component = None
        current_content = []
        
        for line in lines:
            # Look for component file headers (e.g., "// src/App.jsx", "// src/components/Navigation.jsx")
            if line.strip().startswith('//') and ('.tsx' in line or '.jsx' in line or '.css' in line or '.html' in line or '.js' in line):
                # Save previous component if exists
                if current_component and current_content:
                    components[current_component] = '\n'.join(current_content).strip()
                
                # Start new component
                component_path = line.strip()[2:].strip()  # Remove "// "
                current_component = component_path
                current_content = []
            elif current_component:
                current_content.append(line)
        
        # Save the last component
        if current_component and current_content:
            components[current_component] = '\n'.join(current_content).strip()
        
        # If no components found, treat the whole response as a single component
        if not components:
            clean_content = self._extract_code_from_response(response)
            if clean_content:
                components['src/index.js'] = clean_content
        
        return components
    
    def _parse_components(self, response: str, target_stack: str) -> Dict[str, Any]:
        """Parse the AI response for components."""
        try:
            # Split components into separate files
            component_files = self._split_components_from_response(response)
            
            if not component_files:
                return {
                    'status': 'failed',
                    'error': 'No component code found in response'
                }
            
            components = {
                'status': 'success',
                'target_stack': target_stack,
                'component_files': component_files,
                'component_list': list(component_files.keys())
            }
            
            return components
            
        except Exception as e:
            logger.error(f"Error parsing components: {e}")
            return {
                'status': 'failed',
                'error': str(e)
            }
    
    def _parse_package_json(self, response: str, target_stack: str) -> Dict[str, Any]:
        """Parse the AI response for package.json."""
        try:
            # This is a simplified implementation
            package_json = {
                'status': 'success',
                'target_stack': target_stack,
                'package_json': response,
                'dependencies': self._extract_dependencies_from_package_json(response)
            }
            
            return package_json
            
        except Exception as e:
            logger.error(f"Error parsing package.json: {e}")
            return {
                'status': 'failed',
                'error': str(e)
            }
    
    def _extract_directories_from_response(self, response: str) -> List[str]:
        """Extract directory structure from AI response."""
        # This is a simplified implementation
        directories = []
        
        # Basic extraction logic
        lines = response.split('\n')
        for line in lines:
            if '/' in line and not line.startswith('#'):
                directories.append(line.strip())
        
        return directories
    
    def _extract_files_from_response(self, response: str) -> List[str]:
        """Extract file list from AI response."""
        # This is a simplified implementation
        files = []
        
        # Basic extraction logic
        lines = response.split('\n')
        for line in lines:
            if '.' in line and not line.startswith('#'):
                files.append(line.strip())
        
        return files
    
    def _extract_dependencies_from_package_json(self, response: str) -> Dict[str, str]:
        """Extract dependencies from package.json response."""
        # This is a simplified implementation
        dependencies = {}
        
        # Basic extraction logic
        if 'dependencies' in response.lower():
            dependencies['example'] = '^1.0.0'
        
        return dependencies
    
    async def _generate_nextjs_config(self) -> Dict[str, Any]:
        """Generate Next.js configuration."""
        return {
            'status': 'success',
            'content': '// Next.js configuration\nmodule.exports = {\n  // Configuration options\n}'
        }
    
    async def _generate_astro_config(self) -> Dict[str, Any]:
        """Generate Astro configuration."""
        return {
            'status': 'success',
            'content': '// Astro configuration\nexport default {\n  // Configuration options\n}'
        }
    
    async def _generate_typescript_config(self, target_stack: str) -> Dict[str, Any]:
        """Generate TypeScript configuration."""
        return {
            'status': 'success',
            'content': '{\n  "compilerOptions": {\n    "target": "es5",\n    "lib": ["dom", "dom.iterable", "es6"],\n    "allowJs": true,\n    "skipLibCheck": true,\n    "esModuleInterop": true,\n    "allowSyntheticDefaultImports": true,\n    "strict": true,\n    "forceConsistentCasingInFileNames": true,\n    "noFallthroughCasesInSwitch": true,\n    "module": "esnext",\n    "moduleResolution": "node",\n    "resolveJsonModule": true,\n    "isolatedModules": true,\n    "noEmit": true,\n    "jsx": "react-jsx",\n    "baseUrl": ".",\n    "paths": {\n      "@/*": ["src/*"]\n    }\n  },\n  "include": ["src/**/*", "*.tsx", "*.ts", "*.jsx", "*.js"],\n  "exclude": ["node_modules", "dist", "build"]\n}'
        }
    
    async def _generate_eslint_config(self, target_stack: str) -> Dict[str, Any]:
        """Generate ESLint configuration."""
        return {
            'status': 'success',
            'content': '{\n  "extends": ["react-app", "react-app/jest"]\n}'
        }
    
    async def _generate_prettier_config(self) -> Dict[str, Any]:
        """Generate Prettier configuration."""
        return {
            'status': 'success',
            'content': '{\n  "semi": true,\n  "trailingComma": "es5",\n  "singleQuote": true,\n  "printWidth": 80,\n  "tabWidth": 2\n}'
        }
    
    async def _generate_gitignore(self) -> Dict[str, Any]:
        """Generate .gitignore file."""
        return {
            'status': 'success',
            'content': '# Dependencies\nnode_modules/\npnpm-debug.log*\nyarn-debug.log*\nyarn-error.log*\n\n# Production\nbuild/\ndist/\n\n# Environment variables\n.env\n.env.local\n.env.development.local\n.env.test.local\n.env.production.local\n\n# IDE\n.vscode/\n.idea/\n*.swp\n*.swo\n\n# OS\n.DS_Store\nThumbs.db\n\n# Logs\nnpm-debug.log*\nyarn-debug.log*\nyarn-error.log*\n\n# Runtime data\npids\n*.pid\n*.seed\n*.pid.lock\n\n# Coverage directory used by tools like istanbul\ncoverage/\n\n# nyc test coverage\n.nyc_output\n\n# Dependency directories\njspm_packages/\n\n# Optional npm cache directory\n.npm\n\n# Optional eslint cache\n.eslintcache\n\n# Microbundle cache\n.rpt2_cache/\n.rts2_cache_cjs/\n.rts2_cache_es/\n.rts2_cache_umd/\n\n# Optional REPL history\n.node_repl_history\n\n# Output of \'npm pack\'\n*.tgz\n\n# Yarn Integrity file\n.yarn-integrity\n\n# parcel-bundler cache (https://parceljs.org/)\n.cache\n.parcel-cache\n\n# Next.js build output\n.next\n\n# Nuxt.js build / generate output\n.nuxt\ndist\n\n# Storybook build outputs\n.out\n.storybook-out\n\n# Temporary folders\ntmp/\ntemp/\n'
        }
    
    async def _generate_readme(self, project_name: str) -> Dict[str, Any]:
        """Generate README.md file."""
        return {
            'status': 'success',
            'content': f'# {project_name}\n\nThis is a modernized React application generated by Legacy2Modern.\n\n## Getting Started\n\n### Prerequisites\n\n- Node.js (version 16 or higher)\n- npm or yarn\n\n### Installation\n\n1. Install dependencies:\n```bash\nnpm install\n```\n\n2. Start the development server:\n```bash\nnpm start\n```\n\n3. Open [http://localhost:3000](http://localhost:3000) to view it in the browser.\n\n## Available Scripts\n\n- `npm start` - Runs the app in development mode\n- `npm run build` - Builds the app for production\n- `npm test` - Launches the test runner\n- `npm run eject` - Ejects from Create React App\n\n## Project Structure\n\n```\nproject-root/\n├── public/          # Static files\n├── src/             # Source code\n│   ├── components/  # Reusable components\n│   ├── pages/       # Page components\n│   ├── styles/      # CSS files\n│   └── utils/       # Utility functions\n└── package.json     # Dependencies and scripts\n```\n\n## Technologies Used\n\n- React 18\n- TypeScript\n- Tailwind CSS\n- Vite (for development)\n\n## Contributing\n\n1. Fork the repository\n2. Create your feature branch (`git checkout -b feature/amazing-feature`)\n3. Commit your changes (`git commit -m \'Add some amazing feature\'`)\n4. Push to the branch (`git push origin feature/amazing-feature`)\n5. Open a Pull Request\n\n## License\n\nThis project is licensed under the MIT License.\n'
        }
    
    async def _generate_vite_config(self) -> Dict[str, Any]:
        """Generate Vite configuration."""
        return {
            'status': 'success',
            'content': 'import { defineConfig } from \'vite\'\nimport react from \'@vitejs/plugin-react\'\nimport path from \'path\'\n\n// https://vitejs.dev/config/\nexport default defineConfig({\n  plugins: [react()],\n  resolve: {\n    alias: {\n      \'@\': path.resolve(__dirname, \'./src\'),\n    },\n  },\n  server: {\n    port: 3000,\n    open: true,\n  },\n  build: {\n    outDir: \'dist\',\n    sourcemap: true,\n  },\n})\n'
        }
    
    async def _generate_tailwind_config(self) -> Dict[str, Any]:
        """Generate Tailwind CSS configuration."""
        return {
            'status': 'success',
            'content': '/** @type {import(\'tailwindcss\').Config} */\nexport default {\n  content: [\n    "./index.html",\n    "./src/**/*.{js,ts,jsx,tsx}",\n  ],\n  theme: {\n    extend: {\n      colors: {\n        primary: {\n          50: \'#eff6ff\',\n          500: \'#3b82f6\',\n          600: \'#2563eb\',\n          700: \'#1d4ed8\',\n        },\n      },\n    },\n  },\n  plugins: [],\n}\n'
        }
    
    async def _generate_public_index_html(self) -> Dict[str, Any]:
        """Generate public/index.html file."""
        return {
            'status': 'success',
            'content': '<!DOCTYPE html>\n<html lang="en">\n  <head>\n    <meta charset="utf-8" />\n    <link rel="icon" href="%PUBLIC_URL%/favicon.ico" />\n    <meta name="viewport" content="width=device-width, initial-scale=1" />\n    <meta name="theme-color" content="#000000" />\n    <meta\n      name="description"\n      content="Modernized React application"\n    />\n    <link rel="apple-touch-icon" href="%PUBLIC_URL%/logo192.png" />\n    <link rel="manifest" href="%PUBLIC_URL%/manifest.json" />\n    <title>Modernized React App</title>\n  </head>\n  <body>\n    <noscript>You need to enable JavaScript to run this app.</noscript>\n    <div id="root"></div>\n  </body>\n</html>'
        }
    
    async def _generate_public_manifest_json(self) -> Dict[str, Any]:
        """Generate public/manifest.json file."""
        return {
            'status': 'success',
            'content': '{\n  "short_name": "React App",\n  "name": "Modernized React Application",\n  "icons": [\n    {\n      "src": "favicon.ico",\n      "sizes": "64x64 32x32 24x24 16x16",\n      "type": "image/x-icon"\n    }\n  ],\n  "start_url": ".",\n  "display": "standalone",\n  "theme_color": "#000000",\n  "background_color": "#ffffff"\n}'
        }
    
    async def _generate_public_favicon(self) -> Dict[str, Any]:
        """Generate a simple favicon.ico placeholder."""
        return {
            'status': 'success',
            'content': '<!-- This is a placeholder for favicon.ico -->\n<!-- In a real project, you would have an actual .ico file here -->\n<!-- For now, this file serves as a marker that favicon.ico should exist -->',
            'is_binary': True
        }
    
    async def _generate_code(self, source_file: str, target_stack: str) -> Dict[str, Any]:
        """Generate modern code from a source file."""
        return await self._convert_single_file_content(source_file, {}, target_stack)
    
    async def _convert_file(self, file_path: str, content: str) -> Dict[str, Any]:
        """Convert a file with given content."""
        analysis = {'analysis': content, 'status': 'success'}
        return await self._convert_single_file_content(file_path, analysis, self.config.get_target_stack())
    
    async def _create_component(self, component_name: str, specs: Dict) -> Dict[str, Any]:
        """Create a modern component."""
        # This would be implemented to create components based on specifications
        return {
            'status': 'success',
            'component_name': component_name,
            'specs': specs,
            'generated_component': f'// Generated component: {component_name}'
        }
    
    async def _convert_single_file(self, task: Dict) -> Dict[str, Any]:
        """Convert a single file task."""
        return await self._convert_single_file_content(
            task.get('file_path', ''),
            task.get('analysis', {}),
            task.get('target_stack', self.config.get_target_stack())
        )
    
    async def _convert_single_file_content(self, file_path: str, analysis: Dict, target_stack: str) -> Dict[str, Any]:
        """Convert a single file's content to modern code."""
        try:
            # Check if this is an HTML file with virtual pages
            if file_path.lower().endswith('.html') and analysis.get('is_single_page_multi_section', False):
                return await self._convert_html_with_sections(file_path, analysis, target_stack)
            else:
                return await self._convert_regular_file(file_path, analysis, target_stack)
                
        except Exception as e:
            logger.error(f"Error converting file {file_path}: {e}")
            return {
                'status': 'failed',
                'error': str(e),
                'file_path': file_path
            }
    
    async def _convert_html_with_sections(self, file_path: str, analysis: Dict, target_stack: str) -> Dict[str, Any]:
        """Convert HTML file with virtual pages to modern components."""
        try:
            from ..utilities.html_section_detector import HTMLSectionDetector
            
            # Get section data
            section_data = analysis.get('section_detection', {})
            virtual_pages = section_data.get('pages', [])
            shared_components = section_data.get('components', [])
            
            # Extract original HTML content
            html_content = analysis.get('ai_analysis', '')
            if not html_content:
                # Try to get content from file
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        html_content = f.read()
                except Exception as e:
                    logger.error(f"Could not read HTML file {file_path}: {e}")
                    return {
                        'status': 'failed',
                        'error': f'Could not read HTML file: {e}',
                        'file_path': file_path
                    }
            
            # Initialize section detector
            detector = HTMLSectionDetector()
            
            # Generate components for each virtual page
            generated_components = {}
            
            for page in virtual_pages:
                page_name = page.get('name', 'Page')
                selector = page.get('selector', '')
                
                # Extract section content
                section_content = detector.extract_section_content(html_content, selector)
                if section_content:
                    # Convert section to React component
                    component_code = await self._convert_html_section_to_react(
                        section_content, page_name, target_stack
                    )
                    generated_components[f"src/pages/{page_name}.jsx"] = component_code
            
            # Generate shared components
            for component in shared_components:
                component_name = component.get('name', 'Component')
                selector = component.get('selector', '')
                
                # Extract component content
                component_content = detector.extract_section_content(html_content, selector)
                if component_content:
                    # Convert component to React component
                    component_code = await self._convert_html_section_to_react(
                        component_content, component_name, target_stack, is_component=True
                    )
                    generated_components[f"src/components/{component_name}.jsx"] = component_code
            
            return {
                'status': 'success',
                'file_path': file_path,
                'generated_components': generated_components,
                'virtual_pages': virtual_pages,
                'shared_components': shared_components,
                'target_stack': target_stack
            }
            
        except Exception as e:
            logger.error(f"Error converting HTML with sections {file_path}: {e}")
            return {
                'status': 'failed',
                'error': str(e),
                'file_path': file_path
            }
    
    async def _convert_regular_file(self, file_path: str, analysis: Dict, target_stack: str) -> Dict[str, Any]:
        """Convert a regular file to modern code."""
        try:
            # Build context for conversion
            context = PromptContext(
                project_name=self.config.get_project_name(),
                target_stack=target_stack,
                current_task="file_conversion",
                file_content=analysis.get('analysis', ''),
                file_path=file_path,
                user_requirements="Convert this file to modern code using the target stack"
            )
            
            # Build prompt
            prompt_result = self.prompt_builder.build_modernization_prompt(
                context, task_type="modernization"
            )
            
            # Get AI conversion
            conversion_response = await self.ai.chat(
                messages=[{'role': 'user', 'content': prompt_result.user_prompt}],
                system_prompt=prompt_result.system_prompt
            )
            
            return {
                'status': 'success',
                'file_path': file_path,
                'converted_content': conversion_response,
                'target_stack': target_stack
            }
            
        except Exception as e:
            logger.error(f"Error converting regular file {file_path}: {e}")
            return {
                'status': 'failed',
                'error': str(e),
                'file_path': file_path
            }
    
    async def _convert_html_section_to_react(self, html_content: str, component_name: str, 
                                           target_stack: str, is_component: bool = False) -> str:
        """Convert HTML section to React component."""
        try:
            # Build context for HTML to React conversion
            context = PromptContext(
                project_name=self.config.get_project_name(),
                target_stack=target_stack,
                current_task="html_to_react_conversion",
                file_content=html_content,
                file_path=f"{component_name}.html",
                user_requirements=f"Convert this HTML section to a React component named {component_name}"
            )
            
            # Build prompt
            prompt_result = self.prompt_builder.build_modernization_prompt(
                context, task_type="modernization"
            )
            
            # Create specific prompt for HTML to React conversion
            conversion_prompt = f"""
{prompt_result.user_prompt}

HTML CONTENT TO CONVERT:
{html_content}

REQUIREMENTS:
1. Convert this HTML section to a React component named {component_name}
2. Use modern React patterns and hooks
3. Convert inline styles to Tailwind CSS classes
4. Handle any JavaScript functionality with React hooks
5. Make the component reusable and maintainable
6. Add proper TypeScript types if using TypeScript
7. Follow React best practices

COMPONENT TYPE: {'Shared Component' if is_component else 'Page Component'}

Generate ONLY the React component code, no explanations or markdown.
"""
            
            # Get AI conversion
            conversion_response = await self.ai.chat(
                messages=[{'role': 'user', 'content': conversion_prompt}],
                system_prompt=prompt_result.system_prompt
            )
            
            return conversion_response
            
        except Exception as e:
            logger.error(f"Error converting HTML section to React: {e}")
            return f"// Error converting {component_name}: {e}"
    
    async def _generate_components(self, task: Dict) -> Dict[str, Any]:
        """Generate components task."""
        architecture_blueprint = task.get('architecture_blueprint', {})
        project_map = task.get('project_map', {})
        return await self._generate_modern_components_from_blueprint(
            architecture_blueprint, project_map, self.config.get_target_stack()
        )
    
    async def _setup_modern_project(self, task: Dict) -> Dict[str, Any]:
        """Setup modern project task."""
        return await self._create_configuration_files(self.config.get_target_stack())
    
    async def _modernize_icons(self, file_path: str, content: str, target_stack: str) -> Dict[str, Any]:
        """Modernize icons in a file using the icon handler."""
        try:
            # Analyze icon usage in the file
            icon_analysis = self.icon_handler.analyze_icon_usage(file_path, content)
            
            if not icon_analysis['icon_libraries'] and not icon_analysis['svg_elements']:
                return {
                    'status': 'success',
                    'message': 'No icons found to modernize',
                    'modernized_content': content
                }
            
            # Generate modernization plan
            modernization_plan = self.icon_handler.generate_modernization_plan([icon_analysis])
            
            # Apply icon library conversions
            modernized_content = content
            import_statements = []
            
            for library_name, icons in icon_analysis['icon_libraries'].items():
                conversion_result = self.icon_handler.convert_icon_library_to_modern(
                    library_name, icons, target_stack
                )
                
                if conversion_result['status'] == 'success':
                    # Add import statements
                    import_statements.extend(conversion_result['imports'])
                    
                    # Replace icon usage in content
                    for icon in conversion_result['icons']:
                        old_usage = f'class="{icon["original_class"]}"'
                        new_usage = icon['usage']
                        modernized_content = modernized_content.replace(old_usage, new_usage)
            
            # Create SVG components for inline SVGs
            svg_components = []
            for svg_info in icon_analysis['svg_elements']:
                component_result = self.icon_handler.convert_svg_to_component(svg_info)
                if component_result['status'] == 'success':
                    svg_components.append(component_result)
            
            return {
                'status': 'success',
                'modernized_content': modernized_content,
                'import_statements': import_statements,
                'svg_components': svg_components,
                'package_dependencies': modernization_plan['package_dependencies'],
                'analysis': icon_analysis
            }
            
        except Exception as e:
            logger.error(f"Error modernizing icons in {file_path}: {e}")
            return {
                'status': 'error',
                'message': f'Failed to modernize icons: {str(e)}',
                'modernized_content': content
            } 