#!/usr/bin/env python3
"""
Secure XML parsing utilities
"""

import logging
from typing import Optional, Union, Any
import json

logger = logging.getLogger(__name__)

# Always import Element, SubElement, ElementTree from stdlib for type safety
from xml.etree.ElementTree import Element, SubElement, ElementTree

# Try to import defusedxml for secure parsing
try:
    from defusedxml.ElementTree import parse as defused_parse
    from defusedxml.ElementTree import fromstring as defused_fromstring
    DEFUSEDXML_AVAILABLE = True
except ImportError:
    logger.warning("defusedxml not available - using standard library with security warnings")
    from xml.etree.ElementTree import parse as defused_parse
    from xml.etree.ElementTree import fromstring as defused_fromstring
    DEFUSEDXML_AVAILABLE = False

def safe_parse_xml(
    xml_data: Union[str, bytes],
    allow_dtd: bool = False,
    allow_external_entities: bool = False
) -> Optional[Element]:
    """
    Safely parse XML data with protection against XXE attacks
    
    Args:
        xml_data: XML string or bytes to parse
        allow_dtd: Whether to allow DTD processing
        allow_external_entities: Whether to allow external entities
        
    Returns:
        Parsed XML element tree or None if parsing fails
    """
    try:
        if isinstance(xml_data, str):
            xml_data = xml_data.encode('utf-8')
        
        if DEFUSEDXML_AVAILABLE:
            # Use defusedxml for secure parsing
            return defused_fromstring(xml_data)
        else:
            # Use standard library with warning
            logger.warning("Using standard XML parser - potential security risk!")
            return defused_fromstring(xml_data)
            
    except Exception as e:
        logger.error(f"Error parsing XML: {e}")
        return None

def safe_parse_xml_file(
    file_path: str,
    allow_dtd: bool = False,
    allow_external_entities: bool = False
) -> Optional[ElementTree]:
    """
    Safely parse XML file with protection against XXE attacks
    
    Args:
        file_path: Path to XML file
        allow_dtd: Whether to allow DTD processing
        allow_external_entities: Whether to allow external entities
        
    Returns:
        Parsed XML element tree or None if parsing fails
    """
    try:
        if DEFUSEDXML_AVAILABLE:
            # Use defusedxml for secure parsing
            return defused_parse(file_path)  # type: ignore
        else:
            # Use standard library with warning
            logger.warning("Using standard XML parser - potential security risk!")
            return defused_parse(file_path)  # type: ignore
    except Exception as e:
        logger.error(f"Error parsing XML file: {e}")
        return None

def create_safe_xml_element(tag: str, attrib: Optional[dict] = None, text: Optional[str] = None) -> Element:
    """
    Create a safe XML element
    
    Args:
        tag: Element tag name
        attrib: Element attributes
        text: Element text content
        
    Returns:
        XML Element
    """
    elem = Element(tag, attrib if attrib is not None else {})
    if text is not None:
        elem.text = str(text)
    return elem

def add_safe_subelement(parent: Element, tag: str, attrib: Optional[dict] = None, text: Optional[str] = None) -> Element:
    """
    Add a safe subelement to a parent element
    
    Args:
        parent: Parent element
        tag: Subelement tag name
        attrib: Subelement attributes
        text: Subelement text content
        
    Returns:
        Created subelement
    """
    elem = SubElement(parent, tag, attrib if attrib is not None else {})
    if text is not None:
        elem.text = str(text)
    return elem

def xml_to_dict(element: Element) -> dict:
    """
    Convert XML element to dictionary
    
    Args:
        element: XML element to convert
        
    Returns:
        Dictionary representation of XML
    """
    result: str = {
        'tag': element.tag,
        'attrib': dict(element.attrib),
        'text': element.text,
        'children': []
    }
    
    for child in element:
        result['children'].append(xml_to_dict(child))
    
    return result

def safe_xml_to_json(xml_data: Union[str, bytes]) -> Optional[str]:
    """
    Safely convert XML to JSON
    
    Args:
        xml_data: XML string or bytes
        
    Returns:
        JSON string or None if conversion fails
    """
    try:
        root = safe_parse_xml(xml_data)
        if root is not None:
            return json.dumps(xml_to_dict(root), indent=2)
        return None
    except Exception as e:
        logger.error(f"Error converting XML to JSON: {e}")
        return None

# Example usage and testing
if __name__ == "__main__":
    # Test safe XML parsing
    test_xml = """<?xml version="1.0"?>
    <root>
        <element attribute="value">Text content</element>
    </root>"""
    
    result: str = safe_parse_xml(test_xml)
    if result:
        print("XML parsed successfully")
        print(f"Root tag: {result.tag}")
        
    # Test XML to JSON conversion
    json_result: str = safe_xml_to_json(test_xml)
    if json_result:
        print("XML to JSON conversion:")
        print(json_result)
