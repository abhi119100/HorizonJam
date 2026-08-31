def display_chord_tabs(chord_tabs):
    """Display guitar chord tabs - handles both list and dict formats."""
    
    try:
        if isinstance(chord_tabs, dict):
            # Handle dictionary format
            for chord_name, tab_info in chord_tabs.items():
                with st.expander(f"🎸 {chord_name} Chord"):
                    
                    col1, col2 = st.columns([1, 1])
                    
                    with col1:
                        st.write("**Fingering:**")
                        fingering = tab_info.get("fingering", "Not available") if isinstance(tab_info, dict) else str(tab_info)
                        st.code(fingering, language="text")
                        
                        if isinstance(tab_info, dict):
                            difficulty = tab_info.get("difficulty", "Unknown")
                            st.write(f"**Difficulty:** {difficulty}")
                    
                    with col2:
                        if isinstance(tab_info, dict):
                            st.write("**Details:**")
                            occurrences = tab_info.get("dataset_occurrences", 0)
                            st.write(f"Dataset occurrences: {occurrences}")
                            
                            compact = tab_info.get("compact_notation", "Not available")
                            st.write(f"Compact notation: {compact}")
        elif isinstance(chord_tabs, list):
            # Handle list format
            for i, tab_info in enumerate(chord_tabs):
                if isinstance(tab_info, dict):
                    chord_name = tab_info.get("chord_name", tab_info.get("chord", f"Chord {i+1}"))
                    with st.expander(f"🎸 {chord_name} Chord"):
                        
                        col1, col2 = st.columns([1, 1])
                        
                        with col1:
                            st.write("**Fingering:**")
                            fingering = tab_info.get("fingering", tab_info.get("tab", "Not available"))
                            st.code(fingering, language="text")
                            
                            difficulty = tab_info.get("difficulty", "Unknown")
                            st.write(f"**Difficulty:** {difficulty}")
                        
                        with col2:
                            st.write("**Details:**")
                            occurrences = tab_info.get("dataset_occurrences", tab_info.get("occurrences", 0))
                            st.write(f"Dataset occurrences: {occurrences}")
                            
                            compact = tab_info.get("compact_notation", tab_info.get("notation", "Not available"))
                            st.write(f"Compact notation: {compact}")
                else:
                    # Handle simple string entries
                    with st.expander(f"🎸 Chord {i+1}"):
                        st.code(str(tab_info), language="text")
        else:
            st.write("No chord tabs available.")
            st.write(f"Received data type: {type(chord_tabs)}")
    except Exception as e:
        st.error(f"Error displaying chord tabs: {str(e)}")
        st.write(f"Data type: {type(chord_tabs)}, Content: {chord_tabs}")
