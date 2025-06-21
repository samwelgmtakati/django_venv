from django import template
from django.template.defaultfilters import filesizeformat
import re

register = template.Library()

@register.filter(name='format_filesize')
def format_filesize(value):
    """
    Format the value like a 'human-readable' file size (e.g., 13 KB, 4.1 MB, 2 GB).
    """
    if value is None:
        return '0 B'
    return filesizeformat(value)

@register.filter(name='file_icon')
def file_icon(file_name):
    """
    Return the appropriate Font Awesome icon class based on file extension.
    """
    if not file_name:
        return 'fa-file'
    
    # Get the file extension
    ext = file_name.split('.')[-1].lower()
    
    # Document icons
    if ext in ['pdf']:
        return 'fa-file-pdf text-danger'
    elif ext in ['doc', 'docx', 'odt']:
        return 'fa-file-word text-primary'
    elif ext in ['xls', 'xlsx', 'csv', 'ods']:
        return 'fa-file-excel text-success'
    elif ext in ['ppt', 'pptx', 'odp']:
        return 'fa-file-powerpoint text-warning'
    
    # Image icons
    elif ext in ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp', 'svg']:
        return 'fa-file-image text-info'
    
    # Archive icons
    elif ext in ['zip', 'rar', '7z', 'tar', 'gz', 'bz2']:
        return 'fa-file-archive text-secondary'
    
    # Code icons
    elif ext in ['py', 'js', 'java', 'c', 'cpp', 'h', 'hpp', 'php', 'rb', 'go', 'rs', 'swift', 'kt', 'ts']:
        return 'fa-file-code text-primary'
    
    # Text files
    elif ext in ['txt', 'md', 'markdown', 'log', 'json', 'xml', 'csv', 'yaml', 'yml', 'ini', 'conf']:
        return 'fa-file-alt text-secondary'
    
    # Default file icon
    return 'fa-file text-muted'

@register.filter(name='file_type')
def file_type(file_name):
    """
    Return a human-readable file type based on the file extension.
    """
    if not file_name:
        return 'File'
    
    # Get the file extension
    ext = file_name.split('.')[-1].lower()
    
    file_types = {
        # Documents
        'pdf': 'PDF Document',
        'doc': 'Word Document',
        'docx': 'Word Document',
        'odt': 'OpenDocument Text',
        'rtf': 'Rich Text Format',
        'txt': 'Text File',
        'md': 'Markdown File',
        'markdown': 'Markdown File',
        # Spreadsheets
        'xls': 'Excel Spreadsheet',
        'xlsx': 'Excel Spreadsheet',
        'ods': 'OpenDocument Spreadsheet',
        'csv': 'CSV File',
        # Presentations
        'ppt': 'PowerPoint Presentation',
        'pptx': 'PowerPoint Presentation',
        'odp': 'OpenDocument Presentation',
        # Images
        'jpg': 'JPEG Image',
        'jpeg': 'JPEG Image',
        'png': 'PNG Image',
        'gif': 'GIF Image',
        'bmp': 'Bitmap Image',
        'webp': 'WebP Image',
        'svg': 'SVG Image',
        # Archives
        'zip': 'ZIP Archive',
        'rar': 'RAR Archive',
        '7z': '7-Zip Archive',
        'tar': 'TAR Archive',
        'gz': 'GZIP Archive',
        'bz2': 'BZIP2 Archive',
        # Audio
        'mp3': 'MP3 Audio',
        'wav': 'WAV Audio',
        'ogg': 'OGG Audio',
        'm4a': 'MPEG-4 Audio',
        # Video
        'mp4': 'MP4 Video',
        'avi': 'AVI Video',
        'mov': 'QuickTime Movie',
        'wmv': 'Windows Media Video',
        'flv': 'Flash Video',
        'webm': 'WebM Video',
        # Code
        'py': 'Python Script',
        'js': 'JavaScript File',
        'html': 'HTML Document',
        'css': 'CSS File',
        'json': 'JSON File',
        'xml': 'XML File',
        'yaml': 'YAML File',
        'yml': 'YAML File',
        'ini': 'Configuration File',
        'conf': 'Configuration File',
        'sh': 'Shell Script',
        'bat': 'Batch File',
        'ps1': 'PowerShell Script',
    }
    
    return file_types.get(ext, 'File')

@register.filter(name='is_image')
def is_image(file_name):
    """Check if the file is an image."""
    if not file_name:
        return False
    ext = file_name.split('.')[-1].lower()
    return ext in ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp', 'svg']

@register.filter(name='is_document')
def is_document(file_name):
    """Check if the file is a document."""
    if not file_name:
        return False
    ext = file_name.split('.')[-1].lower()
    return ext in ['pdf', 'doc', 'docx', 'odt', 'rtf', 'txt', 'md', 'markdown']

@register.filter(name='is_spreadsheet')
def is_spreadsheet(file_name):
    """Check if the file is a spreadsheet."""
    if not file_name:
        return False
    ext = file_name.split('.')[-1].lower()
    return ext in ['xls', 'xlsx', 'ods', 'csv']

@register.filter(name='is_presentation')
def is_presentation(file_name):
    """Check if the file is a presentation."""
    if not file_name:
        return False
    ext = file_name.split('.')[-1].lower()
    return ext in ['ppt', 'pptx', 'odp']

@register.filter(name='is_archive')
def is_archive(file_name):
    """Check if the file is an archive."""
    if not file_name:
        return False
    ext = file_name.split('.')[-1].lower()
    return ext in ['zip', 'rar', '7z', 'tar', 'gz', 'bz2']

@register.simple_tag
def file_icon_tag(file_name, size=''):
    """
    Return a complete HTML icon tag for the file type.
    
    Usage: {% file_icon_tag 'document.pdf' 'fa-2x' %}
    """
    icon_class = file_icon(file_name)
    size_class = f' {size}' if size else ''
    return f'<i class="{icon_class}{size_class}"></i>'
