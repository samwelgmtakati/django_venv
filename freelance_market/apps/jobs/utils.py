import os
from typing import Optional


def get_file_icon(filename: str) -> str:
    """
    Returns a Font Awesome icon class based on the file extension.
    
    Args:
        filename: The name of the file or the full path
        
    Returns:
        str: Font Awesome icon class
    """
    # Get the file extension in lowercase
    ext = os.path.splitext(filename)[1].lower()
    
    # Document icons
    if ext in ['.pdf']:
        return 'fa-file-pdf text-danger'
    elif ext in ['.doc', '.docx']:
        return 'fa-file-word text-primary'
    elif ext in ['.xls', '.xlsx', '.csv']:
        return 'fa-file-excel text-success'
    elif ext in ['.ppt', '.pptx']:
        return 'fa-file-powerpoint text-warning'
    elif ext in ['.zip', '.rar', '.7z', '.tar', '.gz']:
        return 'fa-file-archive text-secondary'
    
    # Image icons
    elif ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.svg']:
        return 'fa-file-image text-info'
    
    # Code icons
    elif ext in ['.py', '.js', '.java', '.c', '.cpp', '.h', '.hpp', 
                '.php', '.rb', '.go', '.rs', '.swift', '.kt', '.ts']:
        return 'fa-file-code text-primary'
    
    # Text files
    elif ext in ['.txt', '.md', '.markdown', '.log']:
        return 'fa-file-alt text-secondary'
    
    # Default file icon
    return 'fa-file text-muted'


def get_file_type_display(filename: str) -> str:
    """
    Returns a human-readable file type based on the file extension.
    
    Args:
        filename: The name of the file or the full path
        
    Returns:
        str: Human-readable file type
    """
    ext = os.path.splitext(filename)[1].lower()
    
    file_types = {
        # Documents
        '.pdf': 'PDF Document',
        '.doc': 'Word Document',
        '.docx': 'Word Document',
        '.xls': 'Excel Spreadsheet',
        '.xlsx': 'Excel Spreadsheet',
        '.ppt': 'PowerPoint Presentation',
        '.pptx': 'PowerPoint Presentation',
        '.csv': 'CSV File',
        '.txt': 'Text File',
        '.md': 'Markdown File',
        # Images
        '.jpg': 'JPEG Image',
        '.jpeg': 'JPEG Image',
        '.png': 'PNG Image',
        '.gif': 'GIF Image',
        '.bmp': 'Bitmap Image',
        '.webp': 'WebP Image',
        '.svg': 'SVG Image',
        # Archives
        '.zip': 'ZIP Archive',
        '.rar': 'RAR Archive',
        '.7z': '7-Zip Archive',
        '.tar': 'TAR Archive',
        '.gz': 'GZIP Archive',
        # Code
        '.py': 'Python File',
        '.js': 'JavaScript File',
        '.html': 'HTML File',
        '.css': 'CSS File',
        '.json': 'JSON File',
        '.xml': 'XML File',
        # Audio/Video
        '.mp3': 'MP3 Audio',
        '.wav': 'WAV Audio',
        '.mp4': 'MP4 Video',
        '.avi': 'AVI Video',
        '.mov': 'QuickTime Video',
    }
    
    return file_types.get(ext, 'File')


def format_file_size(size_in_bytes: int) -> str:
    """
    Convert a file size in bytes to a human-readable string.
    
    Args:
        size_in_bytes: Size in bytes
        
    Returns:
        str: Formatted file size (e.g., "1.5 MB")
    """
    if size_in_bytes < 1024:
        return f"{size_in_bytes} B"
    
    for unit in ['', 'K', 'M', 'G', 'T', 'P']:
        if abs(size_in_bytes) < 1024.0:
            return f"{size_in_bytes:.1f} {unit}B"
        size_in_bytes /= 1024.0
    
    return f"{size_in_bytes:.1f} PB"


class FileValidator:
    """
    Utility class for validating file uploads.
    """
    
    DEFAULT_MAX_SIZE = 10 * 1024 * 1024  # 10MB
    
    ALLOWED_EXTENSIONS = {
        # Documents
        '.pdf', '.doc', '.docx', '.odt', '.rtf', '.txt',
        # Spreadsheets
        '.xls', '.xlsx', '.ods', '.csv',
        # Presentations
        '.ppt', '.pptx', '.odp',
        # Images
        '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.svg',
        # Archives
        '.zip', '.rar', '.7z',
        # Code
        '.py', '.js', '.html', '.css', '.json', '.xml',
    }
    
    @classmethod
    def validate_file_extension(cls, filename: str) -> bool:
        """
        Check if the file extension is allowed.
        
        Args:
            filename: Name of the file
            
        Returns:
            bool: True if the extension is allowed, False otherwise
        """
        ext = os.path.splitext(filename)[1].lower()
        return ext in cls.ALLOWED_EXTENSIONS
    
    @classmethod
    def validate_file_size(cls, file_obj, max_size: Optional[int] = None) -> bool:
        """
        Check if the file size is within the allowed limit.
        
        Args:
            file_obj: File object with a size attribute or size in bytes
            max_size: Maximum allowed size in bytes (default: 10MB)
            
        Returns:
            bool: True if the file size is within the limit, False otherwise
        """
        if max_size is None:
            max_size = cls.DEFAULT_MAX_SIZE
            
        if hasattr(file_obj, 'size'):
            file_size = file_obj.size
        else:
            file_size = file_obj
            
        return file_size <= max_size
