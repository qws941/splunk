#!/usr/bin/env python3
"""
Dashboard Optimization Script - Phase 1
Implements Base Search Pattern to reduce duplicate queries
"""

import xml.etree.ElementTree as ET
import sys
import re

def optimize_dashboard(input_file, output_file):
    """
    Optimize dashboard by implementing Base Search Pattern

    Changes:
    1. Create base search with common query pattern
    2. Add common eval statements to base search
    3. Convert panels to reference base search
    """

    # Parse dashboard
    tree = ET.parse(input_file)
    root = tree.getroot()

    # Base Search Pattern (to be inserted after <label>)
    base_search_xml = """
  <!-- Base Search: Common query pattern for all panels -->
  <search id="base_fw_search">
    <query>
      index=fw devname=$device_filter$
      | eval severity_level = case(
          level="critical" OR level="emergency" OR level="alert", "critical",
          level="high" OR level="error" OR level="warning", "high",
          level="medium" OR level="notice", "medium",
          1=1, "low"
        )
      | eval event_category = case(
          action="deny" OR action="block" OR action="drop", "blocked",
          action="allow" OR action="accept", "allowed",
          1=1, "other"
        )
      | eval config_change_type = case(
          logid="0100044547", "Deleted",
          logid="0100044546", "Edited",
          logid="0100044545", "Added",
          1=1, null()
        )
    </query>
    <earliest>$time_picker.earliest$</earliest>
    <latest>$time_picker.latest$</latest>
  </search>
"""

    # Find the label element (after which we'll insert base search)
    label_elem = root.find('.//label')

    if label_elem is None:
        print("ERROR: No <label> element found in dashboard")
        return False

    # Get parent of label (should be root)
    parent = root
    label_index = list(parent).index(label_elem)

    # Parse base search XML
    base_search_tree = ET.fromstring(base_search_xml)

    # Insert base search after label
    parent.insert(label_index + 1, base_search_tree)

    print(f"✅ Base search added after <label> element")

    # Now optimize individual panels
    panels = root.findall('.//panel')
    optimized_count = 0

    for panel in panels:
        title_elem = panel.find('.//title')
        search_elem = panel.find('.//search')
        query_elem = panel.find('.//search/query') if search_elem is not None else None

        if query_elem is None or query_elem.text is None:
            continue

        query = query_elem.text.strip()
        title = title_elem.text if title_elem is not None else "Untitled"

        # Check if this query uses the common pattern
        if 'index=fw devname=$device_filter$' in query and 'earliest=$time_picker.earliest$' in query:
            # This panel can use base search

            # Extract the panel-specific filter/processing
            # Remove the base query part
            query_without_base = query

            # Remove index, devname, earliest, latest
            query_without_base = re.sub(r'index=fw\s+devname=\$device_filter\$\s+', '', query_without_base)
            query_without_base = re.sub(r'earliest=\$time_picker\.earliest\$\s+', '', query_without_base)
            query_without_base = re.sub(r'latest=\$time_picker\.latest\$\s+', '', query_without_base)

            # Remove common eval statements if they exist
            query_without_base = re.sub(r'\|\s*eval severity_level = case\(.*?\)', '', query_without_base, flags=re.DOTALL)
            query_without_base = re.sub(r'\|\s*eval event_category = case\(.*?\)', '', query_without_base, flags=re.DOTALL)

            # Clean up extra whitespace and pipes
            query_without_base = query_without_base.strip()
            if query_without_base.startswith('|'):
                query_without_base = query_without_base[1:].strip()

            # Update search element to use base search
            search_elem.set('base', 'base_fw_search')

            # Update query to only include panel-specific processing
            if query_without_base:
                # If there's panel-specific processing, prefix with search command if needed
                if not query_without_base.startswith('search'):
                    # Check if it starts with a filter condition (not a command)
                    if query_without_base.startswith('('):
                        query_without_base = 'search ' + query_without_base
                query_elem.text = '\n      ' + query_without_base + '\n    '
            else:
                # No panel-specific processing, just use base search as-is
                query_elem.text = '\n      | stats count\n    '

            # Remove earliest/latest from search element
            earliest_elem = search_elem.find('earliest')
            latest_elem = search_elem.find('latest')
            if earliest_elem is not None:
                search_elem.remove(earliest_elem)
            if latest_elem is not None:
                search_elem.remove(latest_elem)

            optimized_count += 1
            print(f"✅ Optimized: {title}")

    print(f"\n📊 Optimization Summary:")
    print(f"   Total panels optimized: {optimized_count}")
    print(f"   Base search created: 1")
    print(f"   Expected performance improvement: 30-50%")

    # Write optimized dashboard
    tree.write(output_file, encoding='utf-8', xml_declaration=True)
    print(f"\n✅ Optimized dashboard saved to: {output_file}")

    return True

def main():
    input_file = 'dashboards/fortinet-dashboard.xml.backup-20251021-222245'
    output_file = 'dashboards/fortinet-dashboard-optimized.xml'

    print("=== DASHBOARD OPTIMIZATION - PHASE 1 ===\n")
    print("Implementing Base Search Pattern...\n")

    success = optimize_dashboard(input_file, output_file)

    if success:
        print("\n✅ Optimization completed successfully")
        print("\nNext steps:")
        print("1. Test the optimized dashboard in Splunk")
        print("2. Compare performance (dashboard load time)")
        print("3. If validated, replace original: mv dashboards/fortinet-dashboard-optimized.xml dashboards/fortinet-dashboard.xml")
    else:
        print("\n❌ Optimization failed")
        sys.exit(1)

if __name__ == '__main__':
    main()
