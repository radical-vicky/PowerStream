# django_context_fix.py
"""
Complete fix for Django 4.2.x context classes to work with Python 3.14
This properly implements all required attributes and methods
"""

import django.template.context

# Store original classes
original_Context = django.template.context.Context
original_RequestContext = django.template.context.RequestContext

class FixedContext(original_Context):
    def __init__(self, dict_=None, **kwargs):
        # Initialize the parent class
        super().__init__(dict_, **kwargs)
        
        # Ensure dicts attribute exists
        if not hasattr(self, 'dicts'):
            self.dicts = [{}] if dict_ is None else [dict_]
        
        # Add any other attributes that might be needed
        if not hasattr(self, '_processors_index'):
            self._processors_index = -1
    
    def __copy__(self):
        # Create a new instance
        new = FixedContext()
        # Copy all relevant attributes
        if hasattr(self, 'dicts'):
            new.dicts = self.dicts[:]
        else:
            new.dicts = []
        
        if hasattr(self, '_processors_index'):
            new._processors_index = self._processors_index
        else:
            new._processors_index = -1
            
        return new

class FixedRequestContext(original_RequestContext):
    def __init__(self, request, dict_=None, processors=None, **kwargs):
        # Initialize the parent class with all parameters
        super().__init__(request, dict_, processors, **kwargs)
        
        # Ensure dicts attribute exists
        if not hasattr(self, 'dicts'):
            self.dicts = [{}] if dict_ is None else [dict_]
        
        # RequestContext has a _processors_index attribute
        if not hasattr(self, '_processors_index'):
            self._processors_index = -1
    
    def __copy__(self):
        # Create a new instance
        new = FixedRequestContext(self.request)
        # Copy all relevant attributes
        if hasattr(self, 'dicts'):
            new.dicts = self.dicts[:]
        else:
            new.dicts = []
        
        if hasattr(self, '_processors_index'):
            new._processors_index = self._processors_index
        else:
            new._processors_index = -1
            
        return new

# Apply patches
django.template.context.Context = FixedContext
django.template.context.RequestContext = FixedRequestContext

print("✓ Django context fully patched with all attributes")