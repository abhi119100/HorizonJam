import logging
import warnings
import os
from contextlib import contextmanager

def setup_logging():
    """Configure logging to reduce redundant messages and warnings."""
    
    # Set up basic logging configuration
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )
    
    # Suppress ALL warnings that are not actionable
    warnings.filterwarnings('ignore', category=UserWarning)
    warnings.filterwarnings('ignore', category=DeprecationWarning)
    warnings.filterwarnings('ignore', category=FutureWarning)
    warnings.filterwarnings('ignore', category=RuntimeWarning)
    
    # Specifically suppress pkg_resources warnings
    warnings.filterwarnings('ignore', message='.*pkg_resources.*')
    warnings.filterwarnings('ignore', message='.*setuptools.*')
    warnings.filterwarnings('ignore', message='.*LangChain.*')
    
    # Set specific loggers to WARNING level to reduce verbosity
    logging.getLogger('chromadb').setLevel(logging.WARNING)
    logging.getLogger('sentence_transformers').setLevel(logging.WARNING)
    logging.getLogger('transformers').setLevel(logging.WARNING)
    logging.getLogger('tensorflow').setLevel(logging.WARNING)
    logging.getLogger('openai').setLevel(logging.WARNING)
    logging.getLogger('pretty_midi').setLevel(logging.WARNING)
    logging.getLogger('langchain').setLevel(logging.WARNING)
    
@contextmanager
def suppress_warnings():
    """Context manager to temporarily suppress all warnings."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        yield

def filter_output_lines(lines, filter_terms=None):
    """Filter out lines containing specified terms."""
    if filter_terms is None:
        filter_terms = [
            'pkg_resources', 'userwarning', 'deprecated', 'setuptools', 
            'coremltools', 'langchaindeprecationwarning', 'unicodeencodeerror', 
            'charmap', 'tensorflow', 'sklearn'
        ]
    
    filtered_lines = []
    for line in lines:
        if not any(term.lower() in line.lower() for term in filter_terms):
            filtered_lines.append(line)
    
    return filtered_lines