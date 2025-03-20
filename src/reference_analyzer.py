# Add a new file reference_analyzer.py

import re

class ReferenceAnalyzer:
    """Utility class for finding and analyzing code references"""
    
    def __init__(self, reference_tracker):
        self.reference_tracker = reference_tracker
    
    def find_references_in_method(self, file_path, method_name):
        """Find all references within a method body"""
        # Get method details
        method_info = self.reference_tracker.get_detailed_method_info(file_path, method_name)
        if not method_info:
            return []
            
        method_body = method_info.get('body', '')
        if not method_body:
            return []
            
        references = []
        
        # Find method calls
        for call_info in method_info.get('calls', []):
            target_method = call_info.get('method', '')
            target_class = call_info.get('target_class', '')
            target_file = call_info.get('target_file', '')
            line = call_info.get('line', 0)
            
            # Try to locate the call in the method body
            # This would require parsing the line and finding the position
            # A simplified approach:
            pattern = f"{target_class}.{target_method}" if target_class else f"{target_method}"
            position = method_body.find(pattern)
            
            if position >= 0:
                # Calculate line and column position (approximate)
                lines_before = method_body[:position].count('\n') + 1
                start_pos = f"{lines_before}.{position - method_body.rfind('\n', 0, position) - 1}"
                end_pos = f"{start_pos}+{len(pattern)}c"
                
                references.append({
                    'type': 'call',
                    'start_pos': start_pos,
                    'end_pos': end_pos,
                    'target': {
                        'file': target_file,
                        'method': target_method,
                        'class': target_class
                    }
                })
        
        # Find variable usages
        for variable in method_info.get('variables', []):
            # Find all occurrences of the variable
            pattern = r'\b' + re.escape(variable) + r'\b'
            for match in re.finditer(pattern, method_body):
                start, end = match.span()
                
                # Calculate line and column position
                lines_before = method_body[:start].count('\n') + 1
                start_col = start - method_body.rfind('\n', 0, start) - 1
                start_pos = f"{lines_before}.{start_col}"
                end_pos = f"{lines_before}.{start_col + (end - start)}"
                
                references.append({
                    'type': 'usage',
                    'start_pos': start_pos,
                    'end_pos': end_pos,
                    'target': {
                        'variable': variable
                    }
                })
        
        return references
    
    def find_all_references_to_method(self, file_path, method_name):
        """Find all references to a method across the codebase"""
        incoming_refs, outgoing_refs = self.reference_tracker.get_method_references(file_path, method_name)
        
        # Enrich reference data
        enriched_refs = []
        
        for ref in incoming_refs:
            ref_file = ref.get('file', '')
            ref_method = ref.get('method', '')
            ref_class = ref.get('class', '')
            
            # Get context for this reference (e.g., the code surrounding it)
            context = self.get_reference_context(ref_file, ref_method, method_name)
            
            enriched_refs.append({
                'type': 'incoming',
                'file': ref_file,
                'method': ref_method,
                'class': ref_class,
                'context': context
            })
        
        return enriched_refs
    
    def get_reference_context(self, file_path, method_name, target_method):
        """Get context around a reference (code snippet)"""
        # Get method details
        method_info = self.reference_tracker.get_detailed_method_info(file_path, method_name)
        if not method_info:
            return None
            
        method_body = method_info.get('body', '')
        if not method_body:
            return None
            
        # Find target method in body
        pattern = r'\b' + re.escape(target_method) + r'\s*\('
        match = re.search(pattern, method_body)
        if not match:
            return None
            
        # Get a few lines around the match
        start, end = match.span()
        
        # Find start of line containing match
        line_start = method_body.rfind('\n', 0, start) + 1
        if line_start < 0:
            line_start = 0
            
        # Find end of line containing match
        line_end = method_body.find('\n', end)
        if line_end < 0:
            line_end = len(method_body)
            
        # Get one line before and after if available
        prev_line_start = method_body.rfind('\n', 0, line_start - 1) + 1
        if prev_line_start < 0:
            prev_line_start = 0
            
        next_line_end = method_body.find('\n', line_end + 1)
        if next_line_end < 0:
            next_line_end = len(method_body)
            
        context = method_body[prev_line_start:next_line_end]
        
        return context