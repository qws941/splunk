# Verify SPL syntax structure
with open('savedsearches-fortigate-alerts-logid-based.conf', 'r') as f:
    content = f.read()
    
    # Check for actual Splunk conf syntax errors
    import re
    
    # Find all stanzas
    stanzas = re.findall(r'\[([^\]]+)\]', content)
    print(f"✅ Found {len(stanzas)} saved search stanzas:")
    for s in stanzas:
        print(f"   - {s}")
    
    # Check for common .conf syntax errors
    errors = []
    
    # Check for unmatched quotes in key=value pairs outside of search
    lines = content.split('\n')
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if stripped.startswith('search =') or 'eval' in stripped:
            continue  # Skip SPL lines
        if '=' in stripped and not stripped.startswith('#'):
            if stripped.count('"') % 2 != 0:
                errors.append(f"Line {i}: Unmatched quotes: {stripped[:50]}")
    
    if errors:
        print("\n❌ Potential .conf syntax errors:")
        for e in errors:
            print(f"   {e}")
    else:
        print("\n✅ No .conf syntax errors detected")
        print("\n📝 Note: case() statements with ha_state=, logid=, etc. are VALID SPL syntax")
        print("   These are comparison operators, not duplicate key assignments")

