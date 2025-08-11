"""
Static Site Modernizer

This package provides website modernization capabilities,
including HTML parsing, framework conversion, and functionality mapping.
"""

from .functionality_mapper import (
    WebsiteFunctionalityMapper, WebsiteModernizationMapping,
    UIComponentMapping, APIMapping, WebsiteFramework, UIComponentType
)

__all__ = [
    'WebsiteFunctionalityMapper',
    'WebsiteModernizationMapping',
    'UIComponentMapping',
    'APIMapping',
    'WebsiteFramework',
    'UIComponentType'
] 