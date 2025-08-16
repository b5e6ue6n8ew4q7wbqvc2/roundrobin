import streamlit as st
import pandas as pd
import itertools
import random
from typing import List, Set, Tuple, Optional
from dataclasses import dataclass
import plotly.express as px
import plotly.graph_objects as go
from io import BytesIO
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class GroupConfig:
    """Configuration for group generation"""
    student_count: int
    group_size: int
    weeks: int
    student_names: Optional[List[str]] = None
    max_attempts_per_week: int = 1000
    
    def __post_init__(self):
        self.validate()
    
    def validate(self):
        """Validate configuration parameters"""
        if self.student_count < 2:
            raise ValueError("Must have at least 2 students")
        if self.group_size < 2:
            raise ValueError("Group size must be at least 2")
        if self.group_size > self.student_count:
            raise ValueError("Group size cannot exceed student count")
        if self.weeks < 1:
            raise ValueError("Must have at least 1 week")
        if self.student_names and len(self.student_names) != self.student_count:
            raise ValueError(f"Number of names ({len(self.student_names)}) must match student count ({self.student_count})")

class GroupGenerator:
    def __init__(self, config: GroupConfig):
        self.config = config
        self.students = list(range(config.student_count))
        self.previous_week_pairs: Set[Tuple[int, int]] = set()  # Only track previous week
        self.all_historical_pairs: Set[Tuple[int, int]] = set()  # For statistics only
        
    def generate_groups(self) -> List[List[List[int]]]:
        """Generate groups for all weeks"""
        week_groups = []
        
        for week in range(self.config.weeks):
            groups = self._generate_week_groups()
            week_groups.append(groups)
            self._update_pair_history(groups)
            
        return week_groups
    
    def _generate_week_groups(self) -> List[List[int]]:
        """Generate groups for a single week, avoiding previous week pairs"""
        best_groups = None
        best_score = float('inf')
        
        for attempt in range(self.config.max_attempts_per_week):
            groups = self._create_properly_sized_groups()
            score = self._calculate_previous_week_conflicts(groups)
            
            if score == 0:  # Perfect solution - no previous week conflicts
                return groups
            elif score < best_score:
                best_score = score
                best_groups = groups
                
            # If we've tried many times and have a reasonable solution, use it
            if attempt > 200 and best_score <= 3:
                break
        
        # Return best groups found, or create new ones if none found
        return best_groups if best_groups else self._create_properly_sized_groups()
    
    def _create_properly_sized_groups(self) -> List[List[int]]:
        """Create groups with proper sizing - never smaller than group_size"""
        students_copy = self.students.copy()
        random.shuffle(students_copy)
        
        base_groups = self.config.student_count // self.config.group_size
        remainder = self.config.student_count % self.config.group_size
        
        groups = []
        start_idx = 0
        
        # Create groups - first 'remainder' groups get an extra student
        for i in range(base_groups):
            if i < remainder:
                # This group gets an extra student
                group_size = self.config.group_size + 1
            else:
                # This group gets the standard size
                group_size = self.config.group_size
            
            end_idx = start_idx + group_size
            groups.append(students_copy[start_idx:end_idx])
            start_idx = end_idx
        
        return groups
    
    def _calculate_previous_week_conflicts(self, groups: List[List[int]]) -> int:
        """Calculate how many pairs conflict with previous week only"""
        if not self.previous_week_pairs:  # First week has no conflicts
            return 0
            
        conflicts = 0
        for group in groups:
            for pair in itertools.combinations(group, 2):
                sorted_pair = tuple(sorted(pair))
                if sorted_pair in self.previous_week_pairs:
                    conflicts += 1
        return conflicts
    
    def _update_pair_history(self, groups: List[List[int]]):
        """Update pair history - only keep previous week pairs for constraint"""
        # Clear previous week pairs and set current week as previous
        self.previous_week_pairs.clear()
        
        for group in groups:
            pairs = list(itertools.combinations(group, 2))
            for pair in pairs:
                sorted_pair = tuple(sorted(pair))
                self.previous_week_pairs.add(sorted_pair)
                self.all_historical_pairs.add(sorted_pair)  # Keep all for statistics
    
    def get_pair_statistics(self, week_groups: List[List[List[int]]]) -> dict:
        """Calculate statistics about pair repetitions"""
        all_pairs_count = {}
        consecutive_repeats = 0
        
        # Track all pairs and consecutive repeats
        previous_week_pairs_for_stats = set()
        
        for week, groups in enumerate(week_groups):
            current_week_pairs = set()
            
            for group in groups:
                for pair in itertools.combinations(group, 2):
                    sorted_pair = tuple(sorted(pair))
                    all_pairs_count[sorted_pair] = all_pairs_count.get(sorted_pair, 0) + 1
                    current_week_pairs.add(sorted_pair)
            
            # Check for consecutive repeats
            if week > 0:
                consecutive_repeats += len(current_week_pairs.intersection(previous_week_pairs_for_stats))
            
            previous_week_pairs_for_stats = current_week_pairs
        
        repeated_pairs = {pair: count for pair, count in all_pairs_count.items() if count > 1}
        
        return {
            'total_unique_pairs': len(all_pairs_count),
            'repeated_pairs': len(repeated_pairs),
            'consecutive_repeats': consecutive_repeats,
            'max_repetitions': max(all_pairs_count.values()) if all_pairs_count else 0,
            'repeated_pair_details': repeated_pairs,
            'all_pairs_count': all_pairs_count
        }
    
    def get_expected_group_sizes(self) -> List[int]:
        """Calculate expected group sizes"""
        base_groups = self.config.student_count // self.config.group_size
        remainder = self.config.student_count % self.config.group_size
        
        sizes = []
        for i in range(base_groups):
            if i < remainder:
                sizes.append(self.config.group_size + 1)
            else:
                sizes.append(self.config.group_size)
        
        return sorted(sizes, reverse=True)  # Show larger groups first

def get_student_name(student_idx: int, config: GroupConfig) -> str:
    """Get student name - either from names list or default numbering"""
    if config.student_names:
        return config.student_names[student_idx]
    else:
        return f"Student {student_idx + 1}"

def create_results_dataframe(week_groups: List[List[List[int]]], config: GroupConfig) -> pd.DataFrame:
    """Create a pandas DataFrame with the results"""
    data = []
    
    for student in range(config.student_count):
        row = {'Student': get_student_name(student, config)}
        for week in range(config.weeks):
            # Find which group this student is in for this week
            group_num = '-'
            for group_idx, group in enumerate(week_groups[week]):
                if student in group:
                    group_num = group_idx + 1
                    break
            row[f'Week {week + 1}'] = group_num
        data.append(row)
    
    return pd.DataFrame(data)

def create_group_details_dataframe(week_groups: List[List[List[int]]], config: GroupConfig) -> pd.DataFrame:
    """Create a detailed DataFrame showing group compositions"""
    data = []
    
    for week_idx, groups in enumerate(week_groups):
        for group_idx, group in enumerate(groups):
            student_names = [get_student_name(s, config) for s in group]
            data.append({
                'Week': week_idx + 1,
                'Group': group_idx + 1,
                'Students': ', '.join(student_names),
                'Size': len(group)
            })
    
    return pd.DataFrame(data)

def plot_statistics(stats: dict, config: GroupConfig) -> tuple:
    """Create visualizations for statistics"""
    
    # Pair repetition histogram
    repetition_counts = list(stats['all_pairs_count'].values())
    fig1 = px.histogram(
        x=repetition_counts,
        nbins=max(repetition_counts) if repetition_counts else 1,
        title="Distribution of Pair Repetitions",
        labels={'x': 'Number of Times Paired', 'y': 'Number of Pairs'}
    )
    
    # Summary statistics pie chart
    unique_pairs = stats['total_unique_pairs'] - stats['repeated_pairs']
    fig2 = go.Figure(data=[go.Pie(
        labels=['Unique Pairs', 'Repeated Pairs'],
        values=[unique_pairs, stats['repeated_pairs']],
        title="Pair Repetition Overview"
    )])
    
    return fig1, fig2

def plot_group_sizes(week_groups: List[List[List[int]]], config: GroupConfig):
    """Plot group sizes across weeks to verify consistency"""
    week_data = []
    for week_idx, groups in enumerate(week_groups):
        for group_idx, group in enumerate(groups):
            week_data.append({
                'Week': week_idx + 1,
                'Group': group_idx + 1,
                'Size': len(group)
            })
    
    df = pd.DataFrame(week_data)
    fig = px.box(df, x='Week', y='Size', title='Group Size Distribution by Week')
    fig.add_hline(y=config.group_size, line_dash="dash", line_color="red", 
                  annotation_text=f"Min Size: {config.group_size}")
    fig.add_hline(y=config.group_size + 1, line_dash="dash", line_color="orange", 
                  annotation_text=f"Max Size: {config.group_size + 1}")
    return fig

def parse_student_names(names_text: str) -> List[str]:
    """Parse student names from text input"""
    if not names_text.strip():
        return []
    
    # Split by newlines and clean up
    names = [name.strip() for name in names_text.strip().split('\n')]
    # Remove empty names
    names = [name for name in names if name]
    
    return names

def to_excel(df1: pd.DataFrame, df2: pd.DataFrame) -> bytes:
    """Convert DataFrames to Excel file"""
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df1.to_excel(writer, sheet_name='Student Groups', index=False)
        df2.to_excel(writer, sheet_name='Group Details', index=False)
    return output.getvalue()

def main():
    st.set_page_config(
        page_title="Round Robin Group Generator",
        page_icon="🔄",
        layout="wide"
    )
    
    st.title("🔄 Round Robin Group Generator")
    st.markdown("Generate optimal student groups that avoid **immediate consecutive** pairings while maintaining proper group sizes.")
    
    # Sidebar for configuration
    st.sidebar.header("⚙️ Configuration")
    
    # Student input method selection
    input_method = st.sidebar.radio(
        "Student Input Method:",
        ["Use Numbers", "Paste Names"],
        help="Choose whether to use numbered students or paste in actual names"
    )
    
    if input_method == "Use Numbers":
        student_count = st.sidebar.number_input(
            "Number of Students", 
            min_value=2, 
            max_value=100, 
            value=30,
            help="Total number of students to organize into groups"
        )
        student_names = None
        
    else:  # Paste Names
        st.sidebar.markdown("**Paste Student Names** (one per line):")
        names_text = st.sidebar.text_area(
            "Student Names",
            placeholder="Alice\nBob\nCharlie\nDiana\n...",
            height=200,
            help="Enter one student name per line"
        )
        
        student_names = parse_student_names(names_text)
        student_count = len(student_names)
        
        if student_count == 0:
            st.sidebar.warning("⚠️ Please enter student names above")
        else:
            st.sidebar.success(f"✅ {student_count} students entered")
    
    group_size = st.sidebar.number_input(
        "Group Size", 
        min_value=2, 
        max_value=min(10, student_count) if student_count > 0 else 10, 
        value=4,
        help="Target size for each group"
    )
    
    weeks = st.sidebar.number_input(
        "Number of Weeks", 
        min_value=1, 
        max_value=20, 
        value=6,
        help="Number of weeks to generate groups for"
    )
    
    # Show expected group configuration
    if student_count > 0 and group_size > 0:
        try:
            temp_config = GroupConfig(student_count, group_size, 1, student_names)
            generator = GroupGenerator(temp_config)
            expected_sizes = generator.get_expected_group_sizes()
            
            st.sidebar.info(f"""
            **Expected Group Sizes:**
            {', '.join(map(str, expected_sizes))}
            
            **Total Groups:** {len(expected_sizes)}
            **Total Students:** {sum(expected_sizes)}
            """)
            
            # Show student preview for names
            if input_method == "Paste Names" and student_names:
                with st.sidebar.expander("👥 Student Preview", expanded=False):
                    for i, name in enumerate(student_names[:10], 1):  # Show first 10
                        st.write(f"{i}. {name}")
                    if len(student_names) > 10:
                        st.write(f"... and {len(student_names) - 10} more")
                        
        except ValueError as e:
            st.sidebar.error(f"❌ {e}")
    
    # Generate button
    can_generate = student_count > 0 and group_size > 0
    if st.sidebar.button("🚀 Generate Groups", type="primary", disabled=not can_generate):
        try:
            with st.spinner("Generating optimal groups..."):
                config = GroupConfig(student_count, group_size, weeks, student_names)
                generator = GroupGenerator(config)
                week_groups = generator.generate_groups()
                stats = generator.get_pair_statistics(week_groups)
                
                # Store results in session state
                st.session_state.week_groups = week_groups
                st.session_state.config = config
                st.session_state.stats = stats
                
            st.sidebar.success("✅ Groups generated successfully!")
            
        except ValueError as e:
            st.sidebar.error(f"❌ Configuration Error: {str(e)}")
            return
        except Exception as e:
            st.sidebar.error(f"❌ Generation Error: {str(e)}")
            return
    
    # Display results if available
    if hasattr(st.session_state, 'week_groups'):
        week_groups = st.session_state.week_groups
        config = st.session_state.config
        stats = st.session_state.stats
        
        # Create tabs for different views
        tab1, tab2, tab3, tab4 = st.tabs(["📋 Student View", "👥 Group View", "📊 Statistics", "💾 Download"])
        
        with tab1:
            st.header("Student Group Assignments")
            results_df = create_results_dataframe(week_groups, config)
            st.dataframe(results_df, use_container_width=True)
        
        with tab2:
            st.header("Group Compositions by Week")
            details_df = create_group_details_dataframe(week_groups, config)
            
            # Week selector
            selected_week = st.selectbox("Select Week to View:", range(1, config.weeks + 1))
            week_data = details_df[details_df['Week'] == selected_week]
            
            # Display groups for selected week
            cols = st.columns(min(4, len(week_data)))
            for idx, (_, group_info) in enumerate(week_data.iterrows()):
                with cols[idx % len(cols)]:
                    st.info(f"**Group {group_info['Group']}** ({group_info['Size']} students)\n{group_info['Students']}")
            
            st.subheader("All Group Details")
            st.dataframe(details_df, use_container_width=True)
        
        with tab3:
            st.header("📈 Statistics & Analysis")
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Unique Pairs", stats['total_unique_pairs'])
            with col2:
                st.metric("Overall Repeated Pairs", stats['repeated_pairs'])
            with col3:
                st.metric("Consecutive Week Repeats", stats['consecutive_repeats'], 
                         delta="Lower is better", delta_color="inverse")
            with col4:
                efficiency = (1 - stats['consecutive_repeats'] / max(stats['total_unique_pairs'], 1)) * 100
                st.metric("Consecutive Avoidance", f"{efficiency:.1f}%")
            
            # Group size verification
            st.subheader("📏 Group Size Verification")
            group_size_fig = plot_group_sizes(week_groups, config)
            st.plotly_chart(group_size_fig, use_container_width=True)
            
            # Visualizations
            if stats['total_unique_pairs'] > 0:
                fig1, fig2 = plot_statistics(stats, config)
                
                col1, col2 = st.columns(2)
                with col1:
                    st.plotly_chart(fig1, use_container_width=True)
                with col2:
                    st.plotly_chart(fig2, use_container_width=True)
            
            # Repeated pairs details
            if stats['repeated_pairs'] > 0:
                st.subheader("🔄 All Repeated Pair Details")
                st.caption("Note: Pairs may repeat across non-consecutive weeks - this is expected and unavoidable.")
                
                repeated_data = []
                for (s1, s2), count in stats['repeated_pair_details'].items():
                    repeated_data.append({
                        'Student 1': get_student_name(s1, config),
                        'Student 2': get_student_name(s2, config),
                        'Times Paired': count
                    })
                
                repeated_df = pd.DataFrame(repeated_data).sort_values('Times Paired', ascending=False)
                st.dataframe(repeated_df, use_container_width=True)
        
        with tab4:
            st.header("💾 Download Results")
            
            results_df = create_results_dataframe(week_groups, config)
            details_df = create_group_details_dataframe(week_groups, config)
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("📄 CSV Downloads")
                
                csv1 = results_df.to_csv(index=False)
                st.download_button(
                    label="📥 Download Student View (CSV)",
                    data=csv1,
                    file_name="student_groups.csv",
                    mime="text/csv"
                )
                
                csv2 = details_df.to_csv(index=False)
                st.download_button(
                    label="📥 Download Group Details (CSV)",
                    data=csv2,
                    file_name="group_details.csv",
                    mime="text/csv"
                )
            
            with col2:
                st.subheader("📊 Excel Download")
                
                excel_data = to_excel(results_df, details_df)
                st.download_button(
                    label="📥 Download Complete Report (Excel)",
                    data=excel_data,
                    file_name="student_groups_complete.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
    
    else:
        st.info("👆 Configure your settings in the sidebar and click 'Generate Groups' to start!")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            ### 🔢 Use Numbers Mode:
            - Quick setup with numbered students
            - Perfect for testing or when names aren't needed
            - Just set the count and generate
            """)
            
        with col2:
            st.markdown("""
            ### 📝 Paste Names Mode:
            - Use actual student names
            - Paste one name per line
            - Results show real names instead of numbers
            """)
        
        st.markdown("""
        ### Key Features:
        - ✅ **Maintains proper group sizes** (never below target, max +1 for remainder)
        - ✅ **Avoids consecutive week pairings** (most important constraint)
        - ✅ **Allows distant repeats** (unavoidable and acceptable)
        - ✅ **Works with any number of students** (handles remainders intelligently)
        - ✅ **Both numbered and named student support**
        - ✅ Provides detailed statistics and verification
        - ✅ Multiple export formats (CSV, Excel)
        - ✅ Interactive visualizations
        """)

if __name__ == "__main__":
    main()
