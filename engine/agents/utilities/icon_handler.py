"""
Icon Handler for Legacy2Modern

Handles detection, conversion, and modernization of icons from various sources:
- Icon libraries (Font Awesome, Material Icons, etc.)
- Manual SVG files
- Inline SVG elements
- Icon fonts
"""

import re
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from bs4 import BeautifulSoup, Tag

logger = logging.getLogger(__name__)

class IconHandler:
    """Handles icon detection and modernization."""
    
    def __init__(self):
        # Common icon library patterns
        self.icon_libraries = {
            'font_awesome': {
                'patterns': [
                    r'fa[sr]?\s+fa-[\w-]+',
                    r'fas\s+fa-[\w-]+',
                    r'far\s+fa-[\w-]+',
                    r'fab\s+fa-[\w-]+',
                    r'fal\s+fa-[\w-]+',
                    r'fad\s+fa-[\w-]+'
                ],
                'modern_equivalent': 'react-icons/fa',
                'import_pattern': 'import { {icon_name} } from "react-icons/fa"'
            },
            'material_icons': {
                'patterns': [
                    r'material-icons',
                    r'material-icons-outlined',
                    r'material-icons-round',
                    r'material-icons-sharp',
                    r'material-icons-two-tone'
                ],
                'modern_equivalent': 'react-icons/md',
                'import_pattern': 'import { {icon_name} } from "react-icons/md"'
            },
            'bootstrap_icons': {
                'patterns': [
                    r'bi\s+bi-[\w-]+'
                ],
                'modern_equivalent': 'react-icons/bs',
                'import_pattern': 'import { {icon_name} } from "react-icons/bs"'
            },
            'heroicons': {
                'patterns': [
                    r'heroicon-[a-z]+\s+heroicon-[a-z]+-[\w-]+'
                ],
                'modern_equivalent': '@heroicons/react',
                'import_pattern': 'import { {icon_name}Icon } from "@heroicons/react/24/outline"'
            },
            'feather_icons': {
                'patterns': [
                    r'feather\s+feather-[\w-]+'
                ],
                'modern_equivalent': 'react-icons/fi',
                'import_pattern': 'import { {icon_name} } from "react-icons/fi"'
            }
        }
        
        # SVG element patterns
        self.svg_patterns = [
            r'<svg[^>]*>.*?</svg>',
            r'<svg[^>]*/>'
        ]
    
    def detect_icon_libraries(self, html_content: str) -> Dict[str, List[str]]:
        """Detect icon libraries used in the HTML content."""
        detected_libraries = {}
        
        for library_name, library_info in self.icon_libraries.items():
            detected_icons = []
            for pattern in library_info['patterns']:
                matches = re.findall(pattern, html_content, re.IGNORECASE)
                detected_icons.extend(matches)
            
            if detected_icons:
                detected_libraries[library_name] = list(set(detected_icons))
        
        return detected_libraries
    
    def extract_svg_elements(self, html_content: str) -> List[Dict[str, Any]]:
        """Extract inline SVG elements from HTML content."""
        svg_elements = []
        
        soup = BeautifulSoup(html_content, 'html.parser')
        svg_tags = soup.find_all('svg')
        
        for svg_tag in svg_tags:
            svg_info = {
                'element': str(svg_tag),
                'attributes': dict(svg_tag.attrs),
                'content': svg_tag.decode_contents(),
                'classes': svg_tag.get('class', []),
                'id': svg_tag.get('id', ''),
                'viewBox': svg_tag.get('viewBox', ''),
                'width': svg_tag.get('width', ''),
                'height': svg_tag.get('height', '')
            }
            svg_elements.append(svg_info)
        
        return svg_elements
    
    def convert_icon_library_to_modern(self, library_name: str, icon_classes: List[str], target_framework: str = 'react') -> Dict[str, Any]:
        """Convert legacy icon library usage to modern equivalents."""
        if library_name not in self.icon_libraries:
            return {'status': 'error', 'message': f'Unknown icon library: {library_name}'}
        
        library_info = self.icon_libraries[library_name]
        modern_icons = []
        imports = set()
        
        for icon_class in icon_classes:
            # Extract icon name from class
            icon_name = self._extract_icon_name(icon_class, library_name)
            if icon_name:
                modern_icon = {
                    'original_class': icon_class,
                    'modern_name': icon_name,
                    'import_statement': library_info['import_pattern'].format(icon_name=icon_name),
                    'usage': self._generate_modern_usage(icon_name, target_framework)
                }
                modern_icons.append(modern_icon)
                imports.add(library_info['import_pattern'].format(icon_name=icon_name))
        
        return {
            'status': 'success',
            'library_name': library_name,
            'modern_library': library_info['modern_equivalent'],
            'icons': modern_icons,
            'imports': list(imports),
            'package_dependencies': [library_info['modern_equivalent']]
        }
    
    def convert_svg_to_component(self, svg_info: Dict[str, Any], component_name: str = None) -> Dict[str, Any]:
        """Convert SVG element to React component."""
        if not component_name:
            component_name = f"Icon{svg_info.get('id', 'Svg')}"
        
        # Clean and optimize SVG attributes
        svg_attrs = svg_info['attributes'].copy()
        
        # Remove problematic attributes for React
        for attr in ['xmlns', 'xmlns:xlink', 'version']:
            svg_attrs.pop(attr, None)
        
        # Convert attributes to camelCase for React
        react_attrs = {}
        for key, value in svg_attrs.items():
            react_key = self._to_camel_case(key)
            react_attrs[react_key] = value
        
        # Generate React component
        component_code = f"""import React from 'react';

interface {component_name}Props {{
  className?: string;
  width?: string | number;
  height?: string | number;
  color?: string;
  [key: string]: any;
}}

const {component_name}: React.FC<{component_name}Props> = ({{
  className = '',
  width = '24',
  height = '24',
  color = 'currentColor',
  ...props
}}) => {{
  return (
    <svg
      width={{width}}
      height={{height}}
      className={{className}}
      fill={{color}}
      {{...props}}
    >
      {svg_info['content']}
    </svg>
  );
}};

export default {component_name};
"""
        
        return {
            'status': 'success',
            'component_name': component_name,
            'component_code': component_code,
            'file_name': f'{component_name}.tsx'
        }
    
    def analyze_icon_usage(self, file_path: str, content: str) -> Dict[str, Any]:
        """Comprehensive analysis of icon usage in a file."""
        analysis = {
            'file_path': file_path,
            'icon_libraries': self.detect_icon_libraries(content),
            'svg_elements': self.extract_svg_elements(content),
            'recommendations': []
        }
        
        # Generate recommendations
        if analysis['icon_libraries']:
            analysis['recommendations'].append({
                'type': 'library_migration',
                'message': f"Found {len(analysis['icon_libraries'])} icon library(ies) that should be modernized",
                'libraries': list(analysis['icon_libraries'].keys())
            })
        
        if analysis['svg_elements']:
            analysis['recommendations'].append({
                'type': 'svg_optimization',
                'message': f"Found {len(analysis['svg_elements'])} inline SVG element(s) that can be converted to components",
                'count': len(analysis['svg_elements'])
            })
        
        return analysis
    
    def generate_modernization_plan(self, analysis_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate a comprehensive modernization plan for icons."""
        plan = {
            'total_files_analyzed': len(analysis_results),
            'libraries_to_migrate': {},
            'svg_components_to_create': [],
            'package_dependencies': set(),
            'import_statements': [],
            'files_to_update': []
        }
        
        for analysis in analysis_results:
            # Process icon libraries
            for library_name, icons in analysis['icon_libraries'].items():
                if library_name not in plan['libraries_to_migrate']:
                    plan['libraries_to_migrate'][library_name] = []
                plan['libraries_to_migrate'][library_name].extend(icons)
            
            # Process SVG elements
            for svg_info in analysis['svg_elements']:
                component_info = self.convert_svg_to_component(svg_info)
                plan['svg_components_to_create'].append(component_info)
            
            # Collect package dependencies
            for library_name in analysis['icon_libraries'].keys():
                if library_name in self.icon_libraries:
                    plan['package_dependencies'].add(self.icon_libraries[library_name]['modern_equivalent'])
        
        # Convert sets to lists for JSON serialization
        plan['package_dependencies'] = list(plan['package_dependencies'])
        
        return plan
    
    def _extract_icon_name(self, icon_class: str, library_name: str) -> Optional[str]:
        """Extract icon name from CSS class."""
        if library_name == 'font_awesome':
            # Extract from patterns like "fas fa-home" -> "FaHome"
            match = re.search(r'fa-([\w-]+)', icon_class)
            if match:
                icon_name = match.group(1)
                return ''.join(word.capitalize() for word in icon_name.split('-'))
        
        elif library_name == 'material_icons':
            # Material icons are typically text content, not class-based
            return None
        
        elif library_name == 'bootstrap_icons':
            # Extract from patterns like "bi bi-house" -> "BsHouse"
            match = re.search(r'bi-([\w-]+)', icon_class)
            if match:
                icon_name = match.group(1)
                return 'Bs' + ''.join(word.capitalize() for word in icon_name.split('-'))
        
        return None
    
    def _generate_modern_usage(self, icon_name: str, target_framework: str) -> str:
        """Generate modern usage example for the icon."""
        if target_framework == 'react':
            return f'<{icon_name} className="w-6 h-6" />'
        elif target_framework == 'nextjs':
            return f'<{icon_name} className="w-6 h-6" />'
        else:
            return f'<{icon_name} />'
    
    def _to_camel_case(self, snake_case: str) -> str:
        """Convert snake_case to camelCase."""
        components = snake_case.split('-')
        return components[0] + ''.join(word.capitalize() for word in components[1:]) 