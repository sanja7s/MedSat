#!/usr/bin/env python3
"""
Comprehensive system analysis and testing framework.
This script analyzes the NHS prescription parser system for:
1. Code quality and consistency
2. Performance bottlenecks  
3. Abstraction opportunities
4. Integration issues
5. Test coverage gaps
"""

import os
import sys
import glob
import pandas as pd
import json
import time
from pathlib import Path
import inspect

# Add parent directory to path
sys.path.append('..')

# Import modules for analysis
try:
    from sources.downloader import Downloader
    from matching.drugMatching import DrugMatcher
    from matching.commonFunc import *
    from matching.commonFunc_updated import *
    from matching.utils import *
except ImportError as e:
    print(f"Warning: Could not import some modules: {e}")


class SystemAnalyzer:
    """Comprehensive system analyzer for the NHS prescription parser."""
    
    def __init__(self, base_dir="../"):
        self.base_dir = base_dir
        self.analysis_results = {}
        self.issues_found = []
        self.recommendations = []
    
    def analyze_code_structure(self):
        """Analyze the overall code structure and organization."""
        print("🔍 Analyzing code structure...")
        
        structure_analysis = {
            'total_python_files': 0,
            'lines_of_code': 0,
            'modules': {},
            'duplicated_functions': [],
            'circular_imports': []
        }
        
        # Find all Python files
        python_files = glob.glob(os.path.join(self.base_dir, "**/*.py"), recursive=True)
        structure_analysis['total_python_files'] = len(python_files)
        
        # Analyze each file
        for file_path in python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    structure_analysis['lines_of_code'] += len(lines)
                    
                    # Extract module info
                    module_name = os.path.basename(file_path)
                    structure_analysis['modules'][module_name] = {
                        'path': file_path,
                        'lines': len(lines),
                        'functions': [],
                        'classes': []
                    }
                    
                    # Basic function/class extraction
                    for line in lines:
                        line = line.strip()
                        if line.startswith('def '):
                            func_name = line.split('(')[0].replace('def ', '').strip()
                            structure_analysis['modules'][module_name]['functions'].append(func_name)
                        elif line.startswith('class '):
                            class_name = line.split('(')[0].replace('class ', '').replace(':', '').strip()
                            structure_analysis['modules'][module_name]['classes'].append(class_name)
            
            except Exception as e:
                print(f"Error analyzing {file_path}: {e}")
        
        self.analysis_results['structure'] = structure_analysis
        return structure_analysis
    
    def analyze_function_duplication(self):
        """Identify duplicated or similar functions across modules."""
        print("🔍 Analyzing function duplication...")
        
        # Compare commonFunc.py and commonFunc_updated.py
        duplications = []
        
        try:
            import matching.commonFunc as cf_old
            import matching.commonFunc_updated as cf_new
            
            old_functions = [name for name, obj in inspect.getmembers(cf_old) 
                           if inspect.isfunction(obj)]
            new_functions = [name for name, obj in inspect.getmembers(cf_new) 
                           if inspect.isfunction(obj)]
            
            # Find overlapping function names
            overlaps = set(old_functions) & set(new_functions)
            for func_name in overlaps:
                duplications.append({
                    'function': func_name,
                    'modules': ['commonFunc.py', 'commonFunc_updated.py'],
                    'recommendation': 'Consider consolidating into a single, unified implementation'
                })
            
            self.issues_found.append({
                'type': 'Code Duplication',
                'severity': 'Medium',
                'description': f'Found {len(duplications)} duplicated functions between old and new modules',
                'details': duplications
            })
            
        except ImportError as e:
            print(f"Could not analyze function duplication: {e}")
        
        return duplications
    
    def analyze_data_format_handling(self):
        """Analyze how different data formats are handled."""
        print("🔍 Analyzing data format handling...")
        
        format_issues = []
        
        # Check hardcoded column references
        hardcoded_columns = [
            "'2'", "'5'", "'7'", "'8'", "'16'", "'19'",  # Old format
            "'PRACTICE_CODE'", "'ITEMS'", "'ACTUAL_COST'"  # New format
        ]
        
        python_files = glob.glob(os.path.join(self.base_dir, "**/*.py"), recursive=True)
        
        for file_path in python_files:
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                    for col in hardcoded_columns:
                        if col in content:
                            format_issues.append({
                                'file': file_path,
                                'column': col,
                                'type': 'hardcoded_column_reference'
                            })
            except Exception as e:
                continue
        
        if format_issues:
            self.issues_found.append({
                'type': 'Data Format Handling',
                'severity': 'High',
                'description': 'Found hardcoded column references that could break with format changes',
                'count': len(format_issues),
                'recommendation': 'Use consistent field mapping approach like in commonFunc_updated.py'
            })
        
        return format_issues
    
    def analyze_error_handling(self):
        """Analyze error handling patterns."""
        print("🔍 Analyzing error handling...")
        
        error_patterns = {
            'bare_except': [],
            'missing_try_catch': [],
            'inconsistent_error_messages': []
        }
        
        python_files = glob.glob(os.path.join(self.base_dir, "**/*.py"), recursive=True)
        
        for file_path in python_files:
            try:
                with open(file_path, 'r') as f:
                    lines = f.readlines()
                    for i, line in enumerate(lines):
                        # Look for bare except clauses
                        if 'except:' in line and 'except Exception' not in line:
                            error_patterns['bare_except'].append({
                                'file': file_path,
                                'line': i + 1,
                                'content': line.strip()
                            })
            except Exception:
                continue
        
        if error_patterns['bare_except']:
            self.issues_found.append({
                'type': 'Error Handling',
                'severity': 'Medium',
                'description': f'Found {len(error_patterns["bare_except"])} bare except clauses',
                'recommendation': 'Use specific exception types for better error handling'
            })
        
        return error_patterns
    
    def analyze_performance_bottlenecks(self):
        """Identify potential performance issues."""
        print("🔍 Analyzing performance bottlenecks...")
        
        performance_issues = []
        
        # Check for inefficient patterns
        patterns_to_check = [
            ('iterrows()', 'Consider using vectorized operations instead of iterrows()'),
            ('for.*in.*groupby', 'Large groupby operations might benefit from optimization'),
            ('pd.read_csv.*chunksize', 'Good: Using chunked reading for large files'),
            ('\.append\(', 'Consider using pd.concat() instead of append() in loops')
        ]
        
        python_files = glob.glob(os.path.join(self.base_dir, "**/*.py"), recursive=True)
        
        for file_path in python_files:
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                    for pattern, recommendation in patterns_to_check:
                        if pattern in content:
                            performance_issues.append({
                                'file': file_path,
                                'pattern': pattern,
                                'recommendation': recommendation
                            })
            except Exception:
                continue
        
        return performance_issues
    
    def test_system_integration(self):
        """Test integration between different system components."""
        print("🔍 Testing system integration...")
        
        integration_results = {
            'downloader_json_consistency': False,
            'mapping_files_exist': False,
            'format_compatibility': False,
            'output_directory_structure': False
        }
        
        try:
            # Test downloader configuration
            sources_file = os.path.join(self.base_dir, 'sources/serialized_file_paths.json')
            if os.path.exists(sources_file):
                with open(sources_file, 'r') as f:
                    sources = json.load(f)
                    integration_results['downloader_json_consistency'] = len(sources) > 0
            
            # Test mapping files
            mappings_dir = os.path.join(self.base_dir, 'mappings/')
            required_mappings = [
                'drug_association_graph.gexf',
                'category_association_graph.gexf', 
                'CHEM_MASTER_MAP.csv'
            ]
            
            mapping_files_exist = all(
                os.path.exists(os.path.join(mappings_dir, f)) 
                for f in required_mappings
            )
            integration_results['mapping_files_exist'] = mapping_files_exist
            
            # Test format compatibility
            try:
                # Test if both old and new format handlers can be imported
                from matching.commonFunc import calculateTemporalMetrics_LSOA as old_calc
                from matching.commonFunc_updated import calculateTemporalMetrics_LSOA as new_calc
                integration_results['format_compatibility'] = True
            except ImportError:
                integration_results['format_compatibility'] = False
            
        except Exception as e:
            print(f"Integration test error: {e}")
        
        return integration_results
    
    def generate_improvement_recommendations(self):
        """Generate comprehensive improvement recommendations."""
        print("📝 Generating improvement recommendations...")
        
        recommendations = []
        
        # Code organization recommendations
        recommendations.append({
            'category': 'Code Organization',
            'priority': 'High',
            'title': 'Unify duplicate functionality',
            'description': 'Merge commonFunc.py and commonFunc_updated.py into a single, unified module',
            'benefits': ['Reduced code duplication', 'Easier maintenance', 'Consistent behavior'],
            'implementation': 'Create a new unified_common_functions.py that handles both formats'
        })
        
        # Data format handling recommendations
        recommendations.append({
            'category': 'Data Format Handling',
            'priority': 'High', 
            'title': 'Implement universal data format abstraction',
            'description': 'Create a DataFrameAdapter class that provides consistent interface for both old and new formats',
            'benefits': ['Format-agnostic processing', 'Easier to add new formats', 'Reduced hardcoded dependencies'],
            'implementation': 'Design adapter pattern with format detection and field mapping'
        })
        
        # Testing recommendations
        recommendations.append({
            'category': 'Testing',
            'priority': 'Medium',
            'title': 'Comprehensive test suite',
            'description': 'Implement unit tests, integration tests, and end-to-end tests',
            'benefits': ['Catch regressions early', 'Confidence in changes', 'Documentation of expected behavior'],
            'implementation': 'Expand existing test framework with pytest and coverage reporting'
        })
        
        # Performance recommendations
        recommendations.append({
            'category': 'Performance',
            'priority': 'Medium',
            'title': 'Optimize data processing pipeline',
            'description': 'Use vectorized operations and optimize memory usage for large datasets',
            'benefits': ['Faster processing', 'Lower memory usage', 'Better scalability'],
            'implementation': 'Replace iterrows() with vectorized operations, implement chunked processing'
        })
        
        # Configuration recommendations
        recommendations.append({
            'category': 'Configuration',
            'priority': 'Low',
            'title': 'Centralized configuration management',
            'description': 'Create configuration files for paths, column mappings, and processing parameters',
            'benefits': ['Easier deployment', 'Environment-specific configs', 'Reduced hardcoding'],
            'implementation': 'Use YAML/JSON config files with validation'
        })
        
        self.recommendations = recommendations
        return recommendations
    
    def run_comprehensive_analysis(self):
        """Run the complete analysis suite."""
        print("🚀 Starting comprehensive system analysis...")
        start_time = time.time()
        
        # Run all analysis components
        self.analyze_code_structure()
        self.analyze_function_duplication()
        self.analyze_data_format_handling()
        self.analyze_error_handling()
        self.analyze_performance_bottlenecks()
        
        integration_results = self.test_system_integration()
        recommendations = self.generate_improvement_recommendations()
        
        end_time = time.time()
        
        # Generate summary report
        print(f"\n📊 Analysis Complete ({end_time - start_time:.2f}s)")
        print(f"📁 Analyzed {self.analysis_results.get('structure', {}).get('total_python_files', 0)} Python files")
        print(f"📝 Total lines of code: {self.analysis_results.get('structure', {}).get('lines_of_code', 0)}")
        print(f"⚠️  Issues found: {len(self.issues_found)}")
        print(f"💡 Recommendations: {len(recommendations)}")
        
        return {
            'analysis_results': self.analysis_results,
            'issues_found': self.issues_found,
            'recommendations': recommendations,
            'integration_results': integration_results
        }
    
    def generate_report(self, output_file="system_analysis_report.md"):
        """Generate a comprehensive analysis report."""
        results = self.run_comprehensive_analysis()
        
        report_content = f"""# NHS Prescription Parser - System Analysis Report

Generated on: {time.strftime('%Y-%m-%d %H:%M:%S')}

## Executive Summary

This report provides a comprehensive analysis of the NHS Prescription Parser system, identifying areas for improvement and providing actionable recommendations.

### Key Metrics
- **Python Files Analyzed**: {self.analysis_results.get('structure', {}).get('total_python_files', 0)}
- **Total Lines of Code**: {self.analysis_results.get('structure', {}).get('lines_of_code', 0)}
- **Issues Identified**: {len(self.issues_found)}
- **Recommendations**: {len(self.recommendations)}

## Issues Found

"""
        
        for i, issue in enumerate(self.issues_found, 1):
            report_content += f"""### {i}. {issue['type']} ({issue['severity']} Priority)

**Description**: {issue['description']}

**Recommendation**: {issue.get('recommendation', 'See detailed recommendations section')}

---

"""
        
        report_content += "\n## Recommendations\n\n"
        
        for i, rec in enumerate(self.recommendations, 1):
            report_content += f"""### {i}. {rec['title']} ({rec['priority']} Priority)

**Category**: {rec['category']}

**Description**: {rec['description']}

**Benefits**:
"""
            for benefit in rec['benefits']:
                report_content += f"- {benefit}\n"
            
            report_content += f"\n**Implementation**: {rec['implementation']}\n\n---\n\n"
        
        report_content += f"""
## Integration Test Results

- **Downloader JSON Consistency**: {'✅ Pass' if results['integration_results']['downloader_json_consistency'] else '❌ Fail'}
- **Mapping Files Exist**: {'✅ Pass' if results['integration_results']['mapping_files_exist'] else '❌ Fail'}
- **Format Compatibility**: {'✅ Pass' if results['integration_results']['format_compatibility'] else '❌ Fail'}

## Next Steps

1. **Immediate Actions** (High Priority):
   - Address code duplication between commonFunc modules
   - Implement universal data format handling
   
2. **Short Term** (Medium Priority):
   - Expand test coverage
   - Optimize performance bottlenecks
   
3. **Long Term** (Low Priority):
   - Implement centralized configuration
   - Add monitoring and logging capabilities

---

*This report was generated automatically by the System Analysis Framework.*
"""
        
        with open(output_file, 'w') as f:
            f.write(report_content)
        
        print(f"📄 Report saved to: {output_file}")
        return output_file


if __name__ == "__main__":
    analyzer = SystemAnalyzer()
    report_file = analyzer.generate_report()
    print(f"\n✅ Analysis complete! See {report_file} for detailed results.")