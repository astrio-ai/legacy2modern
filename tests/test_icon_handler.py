"""
Test Icon Handler functionality for Legacy2Modern
"""

import pytest
import sys
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from engine.agents.utilities.icon_handler import IconHandler


class TestIconHandler:
    """Test cases for the IconHandler class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.icon_handler = IconHandler()
    
    def test_detect_font_awesome_icons(self):
        """Test detection of Font Awesome icons."""
        html_content = """
        <div>
            <i class="fas fa-home"></i>
            <i class="far fa-user"></i>
            <i class="fab fa-github"></i>
        </div>
        """
        
        detected = self.icon_handler.detect_icon_libraries(html_content)
        
        assert 'font_awesome' in detected
        assert 'fas fa-home' in detected['font_awesome']
        assert 'far fa-user' in detected['font_awesome']
        assert 'fab fa-github' in detected['font_awesome']
    
    def test_detect_bootstrap_icons(self):
        """Test detection of Bootstrap icons."""
        html_content = """
        <div>
            <i class="bi bi-house"></i>
            <i class="bi bi-person"></i>
        </div>
        """
        
        detected = self.icon_handler.detect_icon_libraries(html_content)
        
        assert 'bootstrap_icons' in detected
        assert 'bi bi-house' in detected['bootstrap_icons']
        assert 'bi bi-person' in detected['bootstrap_icons']
    
    def test_extract_svg_elements(self):
        """Test extraction of inline SVG elements."""
        html_content = """
        <div>
            <svg class="custom-icon" viewBox="0 0 24 24" width="24" height="24">
                <path d="M12 2L2 7l10 5 10-5-10-5z"/>
            </svg>
            <svg id="logo" width="32" height="32">
                <circle cx="16" cy="16" r="14" fill="blue"/>
            </svg>
        </div>
        """
        
        svg_elements = self.icon_handler.extract_svg_elements(html_content)
        
        assert len(svg_elements) == 2
        assert svg_elements[0]['classes'] == ['custom-icon']
        assert svg_elements[0]['viewBox'] == '0 0 24 24'
        assert svg_elements[1]['id'] == 'logo'
    
    def test_convert_font_awesome_to_modern(self):
        """Test conversion of Font Awesome icons to modern equivalents."""
        icon_classes = ['fas fa-home', 'far fa-user']
        
        result = self.icon_handler.convert_icon_library_to_modern(
            'font_awesome', icon_classes, 'react'
        )
        
        assert result['status'] == 'success'
        assert result['modern_library'] == 'react-icons/fa'
        assert len(result['icons']) == 2
        
        # Check icon conversions
        icon_names = [icon['modern_name'] for icon in result['icons']]
        assert 'FaHome' in icon_names
        assert 'FaUser' in icon_names
    
    def test_convert_svg_to_component(self):
        """Test conversion of SVG element to React component."""
        svg_info = {
            'element': '<svg class="test-icon" viewBox="0 0 24 24">',
            'attributes': {'class': 'test-icon', 'viewBox': '0 0 24 24'},
            'content': '<path d="M12 2L2 7l10 5 10-5-10-5z"/>',
            'classes': ['test-icon'],
            'id': 'test-icon',
            'viewBox': '0 0 24 24',
            'width': '',
            'height': ''
        }
        
        result = self.icon_handler.convert_svg_to_component(svg_info, 'TestIcon')
        
        assert result['status'] == 'success'
        assert result['component_name'] == 'TestIcon'
        assert 'interface TestIconProps' in result['component_code']
        assert 'const TestIcon:' in result['component_code']
    
    def test_analyze_icon_usage(self):
        """Test comprehensive icon usage analysis."""
        html_content = """
        <div>
            <i class="fas fa-home"></i>
            <i class="bi bi-house"></i>
            <svg class="custom-icon" viewBox="0 0 24 24">
                <path d="M12 2L2 7l10 5 10-5-10-5z"/>
            </svg>
        </div>
        """
        
        analysis = self.icon_handler.analyze_icon_usage('test.html', html_content)
        
        assert analysis['file_path'] == 'test.html'
        assert 'font_awesome' in analysis['icon_libraries']
        assert 'bootstrap_icons' in analysis['icon_libraries']
        assert len(analysis['svg_elements']) == 1
        assert len(analysis['recommendations']) == 2
    
    def test_generate_modernization_plan(self):
        """Test generation of modernization plan."""
        analysis_results = [
            {
                'file_path': 'test1.html',
                'icon_libraries': {
                    'font_awesome': ['fas fa-home'],
                    'bootstrap_icons': ['bi bi-house']
                },
                'svg_elements': []
            },
            {
                'file_path': 'test2.html',
                'icon_libraries': {},
                'svg_elements': [
                    {
                        'id': 'custom-icon',
                        'attributes': {'class': 'icon'},
                        'content': '<path d="M12 2L2 7l10 5 10-5-10-5z"/>'
                    }
                ]
            }
        ]
        
        plan = self.icon_handler.generate_modernization_plan(analysis_results)
        
        assert plan['total_files_analyzed'] == 2
        assert 'font_awesome' in plan['libraries_to_migrate']
        assert 'bootstrap_icons' in plan['libraries_to_migrate']
        assert len(plan['svg_components_to_create']) == 1
        assert 'react-icons/fa' in plan['package_dependencies']
        assert 'react-icons/bs' in plan['package_dependencies']
    
    def test_extract_icon_name(self):
        """Test icon name extraction from CSS classes."""
        # Font Awesome
        assert self.icon_handler._extract_icon_name('fas fa-home', 'font_awesome') == 'FaHome'
        assert self.icon_handler._extract_icon_name('far fa-user-circle', 'font_awesome') == 'FaUserCircle'
        
        # Bootstrap Icons
        assert self.icon_handler._extract_icon_name('bi bi-house', 'bootstrap_icons') == 'BsHouse'
        assert self.icon_handler._extract_icon_name('bi bi-person-badge', 'bootstrap_icons') == 'BsPersonBadge'
        
        # Material Icons (not class-based)
        assert self.icon_handler._extract_icon_name('material-icons', 'material_icons') is None
    
    def test_to_camel_case(self):
        """Test conversion of kebab-case to camelCase."""
        assert self.icon_handler._to_camel_case('view-box') == 'viewBox'
        assert self.icon_handler._to_camel_case('stroke-width') == 'strokeWidth'
        assert self.icon_handler._to_camel_case('fill-rule') == 'fillRule'
    
    def test_generate_modern_usage(self):
        """Test generation of modern usage examples."""
        # React
        assert self.icon_handler._generate_modern_usage('FaHome', 'react') == '<FaHome className="w-6 h-6" />'
        
        # Next.js
        assert self.icon_handler._generate_modern_usage('FaHome', 'nextjs') == '<FaHome className="w-6 h-6" />'
        
        # Other frameworks
        assert self.icon_handler._generate_modern_usage('FaHome', 'vue') == '<FaHome />'


if __name__ == '__main__':
    # Run tests
    pytest.main([__file__, '-v']) 