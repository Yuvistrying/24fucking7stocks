"""
Werkzeug Compatibility Patch

This module patches older versions of Werkzeug to maintain compatibility with Flask 2.0.1
by adding the missing url_quote function that was renamed to quote in newer Werkzeug versions.
"""

import sys
import importlib.util

# Check if werkzeug is already imported
if 'werkzeug.urls' in sys.modules:
    urls_module = sys.modules['werkzeug.urls']
    # Check if url_quote is missing
    if not hasattr(urls_module, 'url_quote') and hasattr(urls_module, 'quote'):
        # Add alias for renamed function
        setattr(urls_module, 'url_quote', urls_module.quote)
        print("Patched werkzeug.urls.url_quote")
else:
    # Import werkzeug.urls module
    try:
        urls_spec = importlib.util.find_spec('werkzeug.urls')
        if urls_spec:
            urls_module = importlib.util.module_from_spec(urls_spec)
            urls_spec.loader.exec_module(urls_module)
            sys.modules['werkzeug.urls'] = urls_module
            
            # Check if url_quote is missing
            if not hasattr(urls_module, 'url_quote') and hasattr(urls_module, 'quote'):
                # Add alias for renamed function
                setattr(urls_module, 'url_quote', urls_module.quote)
                print("Patched werkzeug.urls.url_quote")
    except Exception as e:
        print(f"Error patching werkzeug: {str(e)}") 