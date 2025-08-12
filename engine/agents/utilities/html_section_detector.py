"""
HTML Section Detector - Detects virtual pages within single HTML files.
"""

import re
import logging
from typing import Dict, List, Optional, Any, Tuple
from bs4 import BeautifulSoup
from pathlib import Path

logger = logging.getLogger(__name__)

class HTMLSectionDetector:
    """
    Detects sections in single HTML files that represent virtual pages.
    
    This utility analyzes HTML files to identify:
    - Navigation elements and their target sections
    - Section wrappers with IDs or classes
    - Logical page divisions based on content structure
    - Shared components (header, footer, navigation)
    """
    
    def __init__(self):
        self.section_patterns = [
            # Common section selectors
            r'<section[^>]*id=["\']([^"\']+)["\'][^>]*>',
            r'<div[^>]*id=["\']([^"\']+)["\'][^>]*>',
            r'<div[^>]*class=["\'][^"\']*page[^"\']*["\'][^>]*>',
            r'<div[^>]*class=["\'][^"\']*section[^"\']*["\'][^>]*>',
            r'<main[^>]*>',
            r'<article[^>]*>'
        ]
        
        self.navigation_patterns = [
            # Navigation elements
            r'<nav[^>]*>.*?</nav>',
            r'<ul[^>]*class=["\'][^"\']*nav[^"\']*["\'][^>]*>.*?</ul>',
            r'<div[^>]*class=["\'][^"\']*navigation[^"\']*["\'][^>]*>.*?</div>'
        ]
        
        self.anchor_patterns = [
            # Anchor links
            r'href=["\']#([^"\']+)["\']',
            r'href=["\']([^"\']+\.html#[^"\']*)["\']'
        ]
    
    def detect_virtual_pages(self, html_content: str, file_path: str = "") -> Dict[str, Any]:
        """
        Detect virtual pages within a single HTML file.
        
        Args:
            html_content: The HTML content to analyze
            file_path: Path to the HTML file (for context)
            
        Returns:
            Dictionary containing detected pages, components, and assets
        """
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Detect navigation and extract section targets
            navigation_data = self._extract_navigation_data(soup)
            
            # Detect sections based on various patterns
            sections = self._detect_sections(soup, navigation_data)
            
            # Identify shared components
            shared_components = self._identify_shared_components(soup)
            
            # Extract assets
            assets = self._extract_assets(soup, html_content)
            
            # Generate logical page names
            pages = self._generate_page_mapping(sections, navigation_data)
            
            return {
                "pages": pages,
                "components": shared_components,
                "assets": assets,
                "navigation": navigation_data,
                "sections": sections,
                "file_path": file_path,
                "is_single_page": len(pages) > 1
            }
            
        except Exception as e:
            logger.error(f"Error detecting virtual pages: {e}")
            return {
                "pages": [],
                "components": [],
                "assets": {},
                "navigation": {},
                "sections": [],
                "file_path": file_path,
                "is_single_page": False,
                "error": str(e)
            }
    
    def _extract_navigation_data(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract navigation elements and their target sections."""
        navigation_data = {
            "nav_elements": [],
            "anchor_targets": [],
            "menu_items": []
        }
        
        # Find navigation elements
        nav_elements = soup.find_all(['nav', 'ul', 'div'], class_=re.compile(r'nav|navigation|menu'))
        for nav in nav_elements:
            nav_info = {
                "element": nav.name,
                "classes": nav.get('class', []),
                "id": nav.get('id', ''),
                "anchor_links": []
            }
            
            # Extract anchor links
            anchor_links = nav.find_all('a', href=re.compile(r'^#'))
            for link in anchor_links:
                href = link.get('href', '')
                text = link.get_text(strip=True)
                
                # If text is empty, try to get text from title attribute or generate from ID
                if not text:
                    text = link.get('title', '')
                    if not text and href.startswith('#'):
                        # Generate name from ID
                        target_id = href[1:]
                        text = target_id.replace('-', ' ').title()
                
                if href.startswith('#'):
                    target_id = href[1:]
                    nav_info["anchor_links"].append({
                        "href": href,
                        "target_id": target_id,
                        "text": text
                    })
                    # Avoid duplicates
                    if target_id not in navigation_data["anchor_targets"]:
                        navigation_data["anchor_targets"].append(target_id)
                        navigation_data["menu_items"].append({
                            "text": text,
                            "target": target_id
                        })
            
            navigation_data["nav_elements"].append(nav_info)
        
        return navigation_data
    
    def _detect_sections(self, soup: BeautifulSoup, navigation_data: Dict) -> List[Dict[str, Any]]:
        """Detect sections in the HTML content."""
        sections = []
        
        # Find sections by ID (from navigation)
        for target_id in navigation_data["anchor_targets"]:
            if target_id:  # Skip empty target IDs
                section = soup.find(id=target_id)
                if section:
                    sections.append({
                        "id": target_id,
                        "element": section.name,
                        "classes": section.get('class', []),
                        "content": str(section),
                        "type": "navigation_target"
                    })
        
        # Find sections by common patterns (only if we don't have enough navigation targets)
        if len(sections) < 2:
            section_elements = soup.find_all(['section', 'div', 'main', 'article'])
            for element in section_elements:
                # Skip if already found via navigation
                element_id = element.get('id', '')
                if any(s["id"] == element_id for s in sections):
                    continue
                
                # Check if it looks like a page section
                if self._is_page_section(element):
                    sections.append({
                        "id": element_id or f"section_{len(sections)}",
                        "element": element.name,
                        "classes": element.get('class', []),
                        "content": str(element),
                        "type": "detected_section"
                    })
        
        return sections
    
    def _is_page_section(self, element) -> bool:
        """Determine if an element represents a page section."""
        # Check for common section indicators
        classes = element.get('class', [])
        class_str = ' '.join(classes).lower()
        
        # Section indicators
        section_indicators = [
            'section', 'page', 'content', 'main', 'hero', 'about', 
            'services', 'contact', 'portfolio', 'gallery', 'blog'
        ]
        
        # Check classes
        if any(indicator in class_str for indicator in section_indicators):
            return True
        
        # Check for substantial content
        text_content = element.get_text(strip=True)
        if len(text_content) > 100:  # Substantial text content
            return True
        
        # Check for headings (h1, h2, h3)
        headings = element.find_all(['h1', 'h2', 'h3'])
        if len(headings) > 0:
            return True
        
        # Check for forms (contact forms, etc.)
        forms = element.find_all('form')
        if len(forms) > 0:
            return True
        
        return False
    
    def _identify_shared_components(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Identify components that should be shared across pages."""
        components = []
        
        # Header/Navigation
        header = soup.find(['header', 'nav'])
        if header:
            components.append({
                "name": "Header",
                "selector": "header, nav",
                "element": header.name,
                "classes": header.get('class', []),
                "content": str(header),
                "type": "navigation"
            })
        
        # Footer
        footer = soup.find('footer')
        if footer:
            components.append({
                "name": "Footer",
                "selector": "footer",
                "element": footer.name,
                "classes": footer.get('class', []),
                "content": str(footer),
                "type": "footer"
            })
        
        # Sidebar
        sidebar = soup.find(['aside', 'div'], class_=re.compile(r'sidebar|aside'))
        if sidebar:
            components.append({
                "name": "Sidebar",
                "selector": "aside, .sidebar",
                "element": sidebar.name,
                "classes": sidebar.get('class', []),
                "content": str(sidebar),
                "type": "sidebar"
            })
        
        # Common UI components
        ui_components = self._find_ui_components(soup)
        components.extend(ui_components)
        
        return components
    
    def _find_ui_components(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Find reusable UI components."""
        components = []
        
        # Buttons
        buttons = soup.find_all('button')
        if len(buttons) > 2:  # Multiple buttons suggest a component
            components.append({
                "name": "Button",
                "selector": "button",
                "type": "ui_component",
                "count": len(buttons)
            })
        
        # Forms
        forms = soup.find_all('form')
        if forms:
            components.append({
                "name": "Form",
                "selector": "form",
                "type": "ui_component",
                "count": len(forms)
            })
        
        # Cards
        cards = soup.find_all(['div', 'article'], class_=re.compile(r'card|feature'))
        if cards:
            components.append({
                "name": "Card",
                "selector": ".card, .feature",
                "type": "ui_component",
                "count": len(cards)
            })
        
        return components
    
    def _extract_assets(self, soup: BeautifulSoup, html_content: str) -> Dict[str, List[str]]:
        """Extract assets from the HTML."""
        assets = {
            "css": [],
            "js": [],
            "images": [],
            "fonts": []
        }
        
        # CSS files
        css_links = soup.find_all('link', rel='stylesheet')
        for link in css_links:
            href = link.get('href', '')
            if href:
                assets["css"].append(href)
        
        # Inline CSS
        style_tags = soup.find_all('style')
        if style_tags:
            assets["css"].append("inline_styles")
        
        # JavaScript files
        script_tags = soup.find_all('script', src=True)
        for script in script_tags:
            src = script.get('src', '')
            if src:
                assets["js"].append(src)
        
        # Inline JavaScript
        inline_scripts = soup.find_all('script', src=False)
        if inline_scripts:
            assets["js"].append("inline_scripts")
        
        # Images
        images = soup.find_all('img')
        for img in images:
            src = img.get('src', '')
            if src:
                assets["images"].append(src)
        
        # Fonts
        font_links = soup.find_all('link', rel='preconnect')
        for link in font_links:
            href = link.get('href', '')
            if 'fonts' in href:
                assets["fonts"].append(href)
        
        return assets
    
    def _generate_page_mapping(self, sections: List[Dict], navigation_data: Dict) -> List[Dict[str, Any]]:
        """Generate page mapping from sections and navigation."""
        pages = []
        used_selectors = set()
        
        # Create pages from navigation targets
        for menu_item in navigation_data["menu_items"]:
            target_id = menu_item["target"]
            section = next((s for s in sections if s["id"] == target_id), None)
            
            if section:
                selector = f"#{target_id}"
                if selector not in used_selectors:
                    pages.append({
                        "name": menu_item["text"],
                        "selector": selector,
                        "components": ["Header", "Footer"],
                        "section_data": section,
                        "type": "navigation_page"
                    })
                    used_selectors.add(selector)
        
        # Add any remaining sections as pages
        for section in sections:
            selector = f"#{section['id']}" if section['id'] else f"section:nth-child({len(pages) + 1})"
            if selector not in used_selectors:
                # Generate a name from the section
                page_name = self._generate_page_name(section)
                pages.append({
                    "name": page_name,
                    "selector": selector,
                    "components": ["Header", "Footer"],
                    "section_data": section,
                    "type": "detected_page"
                })
                used_selectors.add(selector)
        
        # If no sections found, treat the whole file as one page
        if not pages:
            pages.append({
                "name": "Home",
                "selector": "body",
                "components": [],
                "section_data": None,
                "type": "single_page"
            })
        
        return pages
    
    def _generate_page_name(self, section: Dict) -> str:
        """Generate a logical page name from section data."""
        # Try to find a heading
        soup = BeautifulSoup(section["content"], 'html.parser')
        headings = soup.find_all(['h1', 'h2', 'h3'])
        
        if headings:
            heading_text = headings[0].get_text(strip=True)
            # Clean up the heading text
            name = re.sub(r'[^\w\s]', '', heading_text)
            name = ' '.join(name.split())
            return name if name else "Page"
        
        # Use ID if available
        if section["id"] and section["id"] != f"section_{len(section)}":
            return section["id"].replace('-', ' ').replace('_', ' ').title()
        
        # Use class names
        classes = section["classes"]
        if classes:
            for class_name in classes:
                if class_name.lower() in ['home', 'about', 'services', 'contact', 'portfolio']:
                    return class_name.title()
        
        return "Page"
    
    def extract_section_content(self, html_content: str, selector: str) -> Optional[str]:
        """
        Extract content for a specific section using CSS selector.
        
        Args:
            html_content: The full HTML content
            selector: CSS selector for the section
            
        Returns:
            HTML content of the section or None if not found
        """
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            if selector.startswith('#'):
                # ID selector
                element_id = selector[1:]
                element = soup.find(id=element_id)
            elif selector.startswith('.'):
                # Class selector
                class_name = selector[1:]
                element = soup.find(class_=class_name)
            else:
                # Other selectors
                element = soup.select_one(selector)
            
            if element:
                return str(element)
            else:
                return None
                
        except Exception as e:
            logger.error(f"Error extracting section content: {e}")
            return None 