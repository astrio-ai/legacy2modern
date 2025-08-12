"""
Architect Agent - Creates modern React architecture blueprint from parser analysis.
"""

import logging
from typing import Dict, List, Optional, Any
from pathlib import Path
from .base_agent import BaseAgent, AgentRole
from ..utilities.prompt import PromptContext

logger = logging.getLogger(__name__)

class ArchitectAgent(BaseAgent):
    """
    Architect Agent - Creates modern React architecture blueprint from legacy analysis.
    
    This agent is responsible for:
    - Taking parser's structured output (JSON map of pages, assets, components)
    - Deciding modern file/folder structure
    - Mapping each old page/component → new React equivalent
    - Deciding React Router setup, shared components, and asset placement
    - Creating a comprehensive architecture blueprint
    """
    
    def __init__(self, ai, memory, config, **kwargs):
        super().__init__(
            name="ArchitectAgent",
            role=AgentRole.ARCHITECT,
            ai=ai,
            memory=memory,
            config=config,
            **kwargs
        )
        
        # Initialize prompt builder
        from ..utilities.prompt import PromptBuilder
        self.prompt_builder = PromptBuilder()
        
        self.architecture_blueprint = {}
        self.component_mappings = {}
        self.routing_structure = {}
        
    def _get_default_system_prompt(self) -> str:
        """Return the default system prompt for the architect agent."""
        return """You are an Architect Agent specialized in creating modern React architecture blueprints from legacy code analysis.

Your primary responsibilities:
1. Analyze parser output to understand legacy structure
2. Design modern React file/folder organization
3. Map legacy pages/components to React equivalents
4. Plan React Router structure and navigation
5. Identify shared components and reusable patterns
6. Create comprehensive architecture blueprint

You should focus on creating clean, scalable, and maintainable React architectures that follow modern best practices."""
    
    async def process_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Process incoming messages for the architect agent."""
        message_type = message.get('type', 'unknown')
        
        if message_type == 'create_architecture':
            return await self._create_architecture(message.get('parser_output', {}))
        elif message_type == 'design_folder_structure':
            return await self._design_folder_structure(message.get('project_analysis', {}))
        elif message_type == 'map_components':
            return await self._map_legacy_to_react(message.get('legacy_structure', {}))
        elif message_type == 'plan_routing':
            return await self._plan_routing_structure(message.get('pages', []))
        elif message_type == 'get_blueprint':
            return await self._get_architecture_blueprint()
        else:
            return {
                'type': 'error',
                'message': f'Unknown message type: {message_type}'
            }
    
    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a specific task assigned to the architect agent."""
        task_type = task.get('type', 'unknown')
        
        if task_type == 'full_architecture_design':
            return await self._perform_full_architecture_design(task)
        elif task_type == 'component_mapping':
            return await self._map_components_task(task)
        elif task_type == 'routing_design':
            return await self._design_routing_task(task)
        elif task_type == 'folder_structure_design':
            return await self._design_folder_structure_task(task)
        else:
            return {
                'success': False,
                'error': f'Unknown task type: {task_type}'
            }
    
    async def _perform_full_architecture_design(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Perform full architecture design from parser output."""
        try:
            self.state.current_task = "full_architecture_design"
            self.update_progress(0.1)
            
            # Get parser output from memory
            parser_output = await self.memory.get('project_map', {})
            if not parser_output:
                return {
                    'success': False,
                    'error': 'No parser output available. Run parser first.'
                }
            
            self.update_progress(0.2)
            
            # Analyze project structure
            project_structure = parser_output.get('structure', {})
            file_analyses = parser_output.get('file_analyses', {})
            
            # Design folder structure
            folder_structure = await self._design_folder_structure(project_structure, file_analyses)
            self.update_progress(0.4)
            
            # Map legacy components to React
            component_mapping = await self._map_legacy_to_react(file_analyses)
            self.update_progress(0.6)
            
            # Plan routing structure
            routing_structure = await self._plan_routing_structure(component_mapping)
            self.update_progress(0.8)
            
            # Create comprehensive blueprint
            architecture_blueprint = {
                'folderStructure': folder_structure,
                'mapping': component_mapping,
                'routing': routing_structure,
                'sharedComponents': self._identify_shared_components(file_analyses),
                'assetPlacement': self._plan_asset_placement(project_structure),
                'dependencies': self._plan_dependencies(parser_output.get('dependencies', {})),
                'patterns': parser_output.get('patterns', []),  # Add patterns from parser output
                'metadata': {
                    'project_name': self.config.get_project_name(),
                    'target_stack': self.config.get_target_stack(),
                    'architecture_type': self._determine_architecture_type(file_analyses),
                    'total_pages': len([f for f in file_analyses.values() if f.get('file_type') == 'html']),
                    'total_components': len([f for f in file_analyses.values() if f.get('file_type') == 'component'])
                }
            }
            
            # Store blueprint
            self.architecture_blueprint = architecture_blueprint
            await self.memory.set('architecture_blueprint', architecture_blueprint)
            
            self.update_progress(1.0)
            
            return {
                'success': True,
                'architecture_blueprint': architecture_blueprint,
                'message': 'Architecture blueprint created successfully'
            }
            
        except Exception as e:
            logger.error(f"Error in full architecture design: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _design_folder_structure(self, project_structure: Dict, file_analyses: Dict) -> Dict[str, Any]:
        """Design modern React folder structure."""
        try:
            # Check for single-page multi-section HTML files
            virtual_pages = []
            shared_components = []
            
            for file_path, analysis in file_analyses.items():
                if analysis.get('status') == 'success' and analysis.get('is_single_page_multi_section', False):
                    virtual_pages.extend(analysis.get('virtual_pages', []))
                    shared_components.extend(analysis.get('shared_components', []))
            
            # Build context for folder structure design
            context = PromptContext(
                project_name=self.config.get_project_name(),
                target_stack=self.config.get_target_stack(),
                current_task="folder_structure_design",
                user_requirements="Design a modern React folder structure based on the legacy project"
            )
            
            # Build prompt
            prompt_result = self.prompt_builder.build_modernization_prompt(
                context, task_type="architecture"
            )
            
            # Create folder structure design prompt
            folder_prompt = f"""
{prompt_result.user_prompt}

PROJECT STRUCTURE ANALYSIS:
{project_structure}

FILE ANALYSES:
{file_analyses}

VIRTUAL PAGES DETECTED:
{virtual_pages}

SHARED COMPONENTS:
{shared_components}

REQUIREMENTS:
1. Design a modern React folder structure
2. Organize components, pages, and assets logically
3. Follow React best practices and conventions
4. Consider scalability and maintainability
5. Include proper separation of concerns
6. Handle virtual pages from single HTML files

Create a JSON structure like this:
{{
  "src": {{
    "components": ["list of shared component files"],
    "pages": ["list of page component files"],
    "assets": {{
      "css": ["list of CSS files"],
      "images": ["list of image files"],
      "js": ["list of utility JS files"]
    }},
    "App.jsx": "main app component",
    "index.jsx": "entry point"
  }}
}}

Provide ONLY the JSON structure, no explanations.
"""
            
            # Get AI response
            folder_response = await self.ai.chat(
                messages=[{'role': 'user', 'content': folder_prompt}],
                system_prompt=prompt_result.system_prompt
            )
            
            # Parse folder structure
            folder_structure = self._parse_folder_structure(folder_response)
            
            # Enhance with virtual pages if detected
            if virtual_pages:
                folder_structure = self._enhance_folder_structure_with_virtual_pages(
                    folder_structure, virtual_pages, shared_components
                )
            
            return folder_structure
            
        except Exception as e:
            logger.error(f"Error designing folder structure: {e}")
            return self._get_default_folder_structure()
    
    async def _map_legacy_to_react(self, file_analyses: Dict) -> Dict[str, str]:
        """Map legacy files to React components."""
        try:
            mapping = {}
            
            for file_path, analysis in file_analyses.items():
                if analysis.get('status') == 'success':
                    file_type = self._determine_file_type(file_path, analysis)
                    
                    if file_type == 'html':
                        # Check if this is a single-page multi-section HTML file
                        if analysis.get('is_single_page_multi_section', False):
                            # Map virtual pages from sections
                            virtual_pages = analysis.get('virtual_pages', [])
                            for page in virtual_pages:
                                page_name = page.get('name', 'Page')
                                selector = page.get('selector', '')
                                react_component = f"src/pages/{page_name}.jsx"
                                mapping[f"{file_path}:{selector}"] = react_component
                            
                            # Map shared components
                            shared_components = analysis.get('shared_components', [])
                            for component in shared_components:
                                component_name = component.get('name', 'Component')
                                selector = component.get('selector', '')
                                react_component = f"src/components/{component_name}.jsx"
                                mapping[f"{file_path}:{selector}"] = react_component
                        else:
                            # Map regular HTML pages to React pages
                            react_component = self._map_html_to_react_page(file_path, analysis)
                            mapping[file_path] = react_component
                    elif file_type == 'component':
                        # Map HTML components to React components
                        react_component = self._map_html_to_react_component(file_path, analysis)
                        mapping[file_path] = react_component
                    elif file_type == 'css':
                        # Map CSS files
                        mapping[file_path] = f"src/styles/{Path(file_path).name}"
                    elif file_type == 'asset':
                        # Map assets
                        mapping[file_path] = f"src/assets/{Path(file_path).name}"
            
            return mapping
            
        except Exception as e:
            logger.error(f"Error mapping legacy to React: {e}")
            return {}
    
    async def _plan_routing_structure(self, component_mapping: Dict) -> List[Dict[str, str]]:
        """Plan React Router structure."""
        try:
            routing = []
            
            # Extract pages from mapping
            pages = {k: v for k, v in component_mapping.items() 
                    if v.startswith('src/pages/')}
            
            # Create routing structure
            for legacy_path, react_component in pages.items():
                # Handle virtual pages (format: file_path:selector)
                if ':' in legacy_path:
                    # Extract selector to determine route
                    selector = legacy_path.split(':', 1)[1]
                    route_path = self._determine_virtual_page_route(selector)
                else:
                    route_path = self._determine_route_path(legacy_path)
                
                component_name = Path(react_component).stem
                
                routing.append({
                    "path": route_path,
                    "component": component_name
                })
            
            # Add default route
            if routing:
                routing.append({
                    "path": "*",
                    "component": "NotFound"
                })
            
            return routing
            
        except Exception as e:
            logger.error(f"Error planning routing structure: {e}")
            return []
    
    def _identify_shared_components(self, file_analyses: Dict) -> List[str]:
        """Identify components that should be shared across pages."""
        shared_components = []
        
        # Look for common patterns in file analyses
        for file_path, analysis in file_analyses.items():
            if analysis.get('status') == 'success':
                content = analysis.get('analysis', '').lower()
                
                # Identify common UI components
                if any(keyword in content for keyword in ['header', 'navigation', 'nav', 'menu']):
                    shared_components.append('Header')
                elif any(keyword in content for keyword in ['footer', 'bottom']):
                    shared_components.append('Footer')
                elif any(keyword in content for keyword in ['sidebar', 'aside']):
                    shared_components.append('Sidebar')
                elif any(keyword in content for keyword in ['button', 'form', 'input']):
                    shared_components.append('UIComponents')
        
        return list(set(shared_components))
    
    def _plan_asset_placement(self, project_structure: Dict) -> Dict[str, List[str]]:
        """Plan where to place different types of assets."""
        assets = {
            'css': [],
            'images': [],
            'js': [],
            'fonts': [],
            'other': []
        }
        
        categorized_files = project_structure.get('categorized_files', {})
        
        # Map categorized files to asset types
        if 'css' in categorized_files:
            assets['css'] = categorized_files['css']
        if 'images' in categorized_files:
            assets['images'] = categorized_files['images']
        if 'javascript' in categorized_files:
            assets['js'] = categorized_files['javascript']
        
        return assets
    
    def _plan_dependencies(self, dependencies: Dict) -> Dict[str, List[str]]:
        """Plan React dependencies based on legacy dependencies."""
        react_dependencies = {
            'core': ['react', 'react-dom'],
            'routing': ['react-router-dom'],
            'styling': ['tailwindcss'],
            'development': ['@vitejs/plugin-react', 'vite'],
            'optional': []
        }
        
        # Add dependencies based on legacy analysis
        if dependencies.get('imports'):
            react_dependencies['optional'].extend([
                'axios',  # for HTTP requests
                'lodash',  # for utilities
                'date-fns'  # for date handling
            ])
        
        return react_dependencies
    
    def _determine_architecture_type(self, file_analyses: Dict) -> str:
        """Determine the type of architecture (SPA, MPA, etc.)."""
        html_files = [f for f in file_analyses.values() 
                     if f.get('file_type') == 'html']
        
        if len(html_files) == 1:
            return 'single_page_application'
        elif len(html_files) > 1:
            return 'multi_page_application'
        else:
            return 'component_library'
    
    def _determine_file_type(self, file_path: str, analysis: Dict) -> str:
        """Determine the type of file for mapping purposes."""
        file_ext = Path(file_path).suffix.lower()
        
        if file_ext == '.html':
            # Check if it's a page or component
            content = analysis.get('analysis', '').lower()
            if any(keyword in content for keyword in ['page', 'main', 'index', 'home']):
                return 'html'
            else:
                return 'component'
        elif file_ext in ['.css', '.scss', '.sass']:
            return 'css'
        elif file_ext in ['.jpg', '.jpeg', '.png', '.gif', '.svg']:
            return 'asset'
        else:
            return 'other'
    
    def _map_html_to_react_page(self, file_path: str, analysis: Dict) -> str:
        """Map HTML file to React page component."""
        file_name = Path(file_path).stem
        
        # Convert file name to React component name
        component_name = ''.join(word.capitalize() for word in file_name.split('-'))
        if component_name.lower() in ['index', 'home', 'main']:
            component_name = 'Home'
        
        return f"src/pages/{component_name}.jsx"
    
    def _map_html_to_react_component(self, file_path: str, analysis: Dict) -> str:
        """Map HTML file to React component."""
        file_name = Path(file_path).stem
        
        # Convert file name to React component name
        component_name = ''.join(word.capitalize() for word in file_name.split('-'))
        
        return f"src/components/{component_name}.jsx"
    
    def _determine_route_path(self, legacy_path: str) -> str:
        """Determine React Router path from legacy file path."""
        file_name = Path(legacy_path).stem
        
        if file_name.lower() in ['index', 'home', 'main']:
            return "/"
        else:
            return f"/{file_name.lower().replace('-', '-')}"
    
    def _determine_virtual_page_route(self, selector: str) -> str:
        """Determine React Router path from virtual page selector."""
        if selector.startswith('#'):
            # ID selector - use the ID as route
            page_id = selector[1:]
            if page_id.lower() in ['home', 'main']:
                return "/"
            else:
                return f"/{page_id.lower()}"
        elif selector.startswith('section:nth-child'):
            # Section selector - use index
            import re
            match = re.search(r'nth-child\((\d+)\)', selector)
            if match:
                index = int(match.group(1))
                if index == 1:
                    return "/"
                else:
                    return f"/section-{index}"
            else:
                return "/"
        else:
            # Default fallback
            return "/"
    
    def _parse_folder_structure(self, response: str) -> Dict[str, Any]:
        """Parse AI response for folder structure."""
        try:
            # Extract JSON from response
            import json
            import re
            
            # Find JSON in the response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                return self._get_default_folder_structure()
                
        except Exception as e:
            logger.error(f"Error parsing folder structure: {e}")
            return self._get_default_folder_structure()
    
    def _get_default_folder_structure(self) -> Dict[str, Any]:
        """Get default folder structure if parsing fails."""
        return {
            "src": {
                "components": ["Header.jsx", "Footer.jsx", "Layout.jsx"],
                "pages": ["Home.jsx", "NotFound.jsx"],
                "assets": {
                    "css": ["globals.css"],
                    "images": [],
                    "js": []
                },
                "App.jsx": "",
                "index.jsx": ""
            }
        }
    
    def _enhance_folder_structure_with_virtual_pages(self, folder_structure: Dict, 
                                                   virtual_pages: List[Dict], 
                                                   shared_components: List[Dict]) -> Dict[str, Any]:
        """Enhance folder structure with virtual pages from single HTML files."""
        try:
            # Ensure src structure exists
            if "src" not in folder_structure:
                folder_structure["src"] = {}
            
            # Add virtual pages
            if "pages" not in folder_structure["src"]:
                folder_structure["src"]["pages"] = []
            
            for page in virtual_pages:
                page_name = page.get('name', 'Page')
                page_file = f"{page_name}.jsx"
                if page_file not in folder_structure["src"]["pages"]:
                    folder_structure["src"]["pages"].append(page_file)
            
            # Add shared components
            if "components" not in folder_structure["src"]:
                folder_structure["src"]["components"] = []
            
            for component in shared_components:
                component_name = component.get('name', 'Component')
                component_file = f"{component_name}.jsx"
                if component_file not in folder_structure["src"]["components"]:
                    folder_structure["src"]["components"].append(component_file)
            
            # Ensure other required files exist
            if "App.jsx" not in folder_structure["src"]:
                folder_structure["src"]["App.jsx"] = ""
            if "index.jsx" not in folder_structure["src"]:
                folder_structure["src"]["index.jsx"] = ""
            
            return folder_structure
            
        except Exception as e:
            logger.error(f"Error enhancing folder structure with virtual pages: {e}")
            return folder_structure
    
    async def _create_architecture(self, parser_output: Dict) -> Dict[str, Any]:
        """Create architecture from parser output."""
        return await self._perform_full_architecture_design({
            'type': 'full_architecture_design',
            'parser_output': parser_output
        })
    
    async def _get_architecture_blueprint(self) -> Dict[str, Any]:
        """Get current architecture blueprint."""
        if not self.architecture_blueprint:
            return {'error': 'No architecture blueprint available'}
        
        return self.architecture_blueprint
    
    async def _map_components_task(self, task: Dict) -> Dict[str, Any]:
        """Map components task."""
        file_analyses = task.get('file_analyses', {})
        mapping = await self._map_legacy_to_react(file_analyses)
        
        return {
            'success': True,
            'mapping': mapping
        }
    
    async def _design_routing_task(self, task: Dict) -> Dict[str, Any]:
        """Design routing task."""
        pages = task.get('pages', [])
        routing = await self._plan_routing_structure(pages)
        
        return {
            'success': True,
            'routing': routing
        }
    
    async def _design_folder_structure_task(self, task: Dict) -> Dict[str, Any]:
        """Design folder structure task."""
        project_structure = task.get('project_structure', {})
        file_analyses = task.get('file_analyses', {})
        folder_structure = await self._design_folder_structure(project_structure, file_analyses)
        
        return {
            'success': True,
            'folder_structure': folder_structure
        } 