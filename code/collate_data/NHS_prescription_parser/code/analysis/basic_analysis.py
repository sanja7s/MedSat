#!/usr/bin/env python3
"""
Basic system analysis without external dependencies.
"""

import os
import glob
import json
import time
import re


class BasicSystemAnalyzer:
    """Basic system analyzer for the NHS prescription parser."""
    
    def __init__(self, base_dir="../"):
        self.base_dir = base_dir
        self.issues = []
        self.recommendations = []
    
    def analyze_code_structure(self):
        """Analyze basic code structure."""
        print("🔍 Analyzing code structure...")
        
        python_files = glob.glob(os.path.join(self.base_dir, "**/*.py"), recursive=True)
        total_lines = 0
        file_info = {}
        
        for file_path in python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    file_info[os.path.basename(file_path)] = {
                        'path': file_path,
                        'lines': len(lines),
                        'functions': len([l for l in lines if l.strip().startswith('def ')]),
                        'classes': len([l for l in lines if l.strip().startswith('class ')])
                    }
                    total_lines += len(lines)
            except Exception as e:
                print(f"Error reading {file_path}: {e}")
        
        print(f"📁 Found {len(python_files)} Python files")
        print(f"📝 Total lines of code: {total_lines}")
        
        return file_info
    
    def check_code_duplication(self):
        """Check for obvious code duplication."""
        print("🔍 Checking for code duplication...")
        
        duplications = []
        
        # Check if both commonFunc.py and commonFunc_updated.py exist
        common_func_old = os.path.join(self.base_dir, "matching/commonFunc.py")
        common_func_new = os.path.join(self.base_dir, "matching/commonFunc_updated.py")
        
        if os.path.exists(common_func_old) and os.path.exists(common_func_new):
            duplications.append({
                'type': 'Module Duplication',
                'files': ['commonFunc.py', 'commonFunc_updated.py'],
                'description': 'Two similar modules exist for common functions'
            })
            
            self.issues.append({
                'type': 'Code Duplication',
                'severity': 'High',
                'description': 'Found duplicate commonFunc modules',
                'recommendation': 'Merge into single unified module'
            })
        
        return duplications
    
    def check_hardcoded_values(self):
        """Check for hardcoded values that should be configurable."""
        print("🔍 Checking for hardcoded values...")
        
        hardcoded_patterns = [
            (r"'[0-9]+'", "Hardcoded column numbers"),
            (r"'../", "Hardcoded relative paths"),
            (r"201[4-9][0-9][0-9]", "Hardcoded date ranges"),
            (r"202[0-9][0-9][0-9]", "Hardcoded date ranges")
        ]
        
        issues = []
        python_files = glob.glob(os.path.join(self.base_dir, "**/*.py"), recursive=True)
        
        for file_path in python_files:
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                    for pattern, description in hardcoded_patterns:
                        matches = re.findall(pattern, content)
                        if matches:
                            issues.append({
                                'file': os.path.basename(file_path),
                                'pattern': description,
                                'matches': len(matches)
                            })
            except Exception:
                continue
        
        if issues:
            self.issues.append({
                'type': 'Hardcoded Values',
                'severity': 'Medium',
                'description': f'Found hardcoded values in {len(issues)} files',
                'recommendation': 'Move to configuration files'
            })
        
        return issues
    
    def check_error_handling(self):
        """Check error handling patterns."""
        print("🔍 Checking error handling...")
        
        error_issues = []
        python_files = glob.glob(os.path.join(self.base_dir, "**/*.py"), recursive=True)
        
        for file_path in python_files:
            try:
                with open(file_path, 'r') as f:
                    lines = f.readlines()
                    for i, line in enumerate(lines):
                        # Check for bare except
                        if 'except:' in line and 'except Exception' not in line:
                            error_issues.append({
                                'file': os.path.basename(file_path),
                                'line': i + 1,
                                'issue': 'Bare except clause'
                            })
                        # Check for exit(-1) without proper error handling
                        if 'exit(-1)' in line:
                            error_issues.append({
                                'file': os.path.basename(file_path),
                                'line': i + 1,
                                'issue': 'Hard exit without cleanup'
                            })
            except Exception:
                continue
        
        if error_issues:
            self.issues.append({
                'type': 'Error Handling',
                'severity': 'Medium',
                'description': f'Found {len(error_issues)} error handling issues',
                'recommendation': 'Use specific exceptions and proper cleanup'
            })
        
        return error_issues
    
    def check_file_structure(self):
        """Check file and directory structure."""
        print("🔍 Checking file structure...")
        
        expected_dirs = ['sources', 'matching', 'mappings', 'prescriptionfiles']
        expected_files = [
            'sources/downloader.py',
            'sources/serialized_file_paths.json',
            'matching/drugMatching.py',
            'matching/commonFunc.py',
            'matching/commonFunc_updated.py'
        ]
        
        missing_dirs = []
        missing_files = []
        
        for directory in expected_dirs:
            if not os.path.exists(os.path.join(self.base_dir, directory)):
                missing_dirs.append(directory)
        
        for file_path in expected_files:
            if not os.path.exists(os.path.join(self.base_dir, file_path)):
                missing_files.append(file_path)
        
        if missing_dirs or missing_files:
            self.issues.append({
                'type': 'File Structure',
                'severity': 'Medium',
                'description': f'Missing {len(missing_dirs)} directories and {len(missing_files)} files',
                'missing_dirs': missing_dirs,
                'missing_files': missing_files
            })
        
        return {'missing_dirs': missing_dirs, 'missing_files': missing_files}
    
    def check_json_configuration(self):
        """Check JSON configuration files."""
        print("🔍 Checking JSON configuration...")
        
        json_files = [
            'sources/serialized_file_paths.json'
        ]
        
        json_issues = []
        
        for json_file in json_files:
            file_path = os.path.join(self.base_dir, json_file)
            if os.path.exists(file_path):
                try:
                    with open(file_path, 'r') as f:
                        data = json.load(f)
                        
                    if json_file == 'sources/serialized_file_paths.json':
                        # Check for both .gz and .ZIP formats
                        gz_files = [k for k in data.keys() if k.endswith('.gz')]
                        zip_files = [k for k in data.keys() if k.endswith('.ZIP')]
                        
                        print(f"  📊 Found {len(gz_files)} .gz files and {len(zip_files)} .ZIP files")
                        
                        if not zip_files:
                            json_issues.append({
                                'file': json_file,
                                'issue': 'No ZIP format files found'
                            })
                
                except json.JSONDecodeError as e:
                    json_issues.append({
                        'file': json_file,
                        'issue': f'JSON parsing error: {e}'
                    })
            else:
                json_issues.append({
                    'file': json_file,
                    'issue': 'File not found'
                })
        
        return json_issues
    
    def generate_recommendations(self):
        """Generate improvement recommendations."""
        print("📝 Generating recommendations...")
        
        recommendations = [
            {
                'priority': 'High',
                'title': 'Unify duplicate modules',
                'description': 'Merge commonFunc.py and commonFunc_updated.py into a single module',
                'benefits': ['Reduced maintenance burden', 'Consistent behavior', 'Easier testing']
            },
            {
                'priority': 'High',
                'title': 'Create configuration system',
                'description': 'Move hardcoded values to configuration files',
                'benefits': ['Easier deployment', 'Environment-specific settings', 'Reduced errors']
            },
            {
                'priority': 'Medium',
                'title': 'Improve error handling',
                'description': 'Replace bare except clauses with specific exception handling',
                'benefits': ['Better debugging', 'Graceful failure recovery', 'User-friendly error messages']
            },
            {
                'priority': 'Medium',
                'title': 'Add comprehensive testing',
                'description': 'Create unit tests and integration tests for all modules',
                'benefits': ['Catch regressions early', 'Confidence in changes', 'Documentation']
            },
            {
                'priority': 'Low',
                'title': 'Add logging system',
                'description': 'Implement proper logging instead of print statements',
                'benefits': ['Better debugging', 'Production monitoring', 'Configurable verbosity']
            }
        ]
        
        self.recommendations = recommendations
        return recommendations
    
    def run_analysis(self):
        """Run the complete analysis."""
        print("🚀 Starting system analysis...")
        start_time = time.time()
        
        structure = self.analyze_code_structure()
        duplications = self.check_code_duplication()
        hardcoded = self.check_hardcoded_values()
        errors = self.check_error_handling()
        file_structure = self.check_file_structure()
        json_config = self.check_json_configuration()
        recommendations = self.generate_recommendations()
        
        end_time = time.time()
        
        print(f"\n📊 Analysis Complete ({end_time - start_time:.2f}s)")
        print(f"⚠️  Issues found: {len(self.issues)}")
        print(f"💡 Recommendations: {len(recommendations)}")
        
        return {
            'structure': structure,
            'issues': self.issues,
            'recommendations': recommendations
        }
    
    def generate_report(self):
        """Generate analysis report."""
        results = self.run_analysis()
        
        print(f"\n{'='*60}")
        print("📋 SYSTEM ANALYSIS REPORT")
        print(f"{'='*60}")
        
        print(f"\n📊 SUMMARY:")
        print(f"  • Python files analyzed: {len(results['structure'])}")
        print(f"  • Issues identified: {len(self.issues)}")
        print(f"  • Recommendations: {len(self.recommendations)}")
        
        print(f"\n⚠️  ISSUES FOUND:")
        for i, issue in enumerate(self.issues, 1):
            print(f"  {i}. {issue['type']} ({issue['severity']} Priority)")
            print(f"     {issue['description']}")
            print(f"     → {issue['recommendation']}")
            print()
        
        print(f"💡 TOP RECOMMENDATIONS:")
        for i, rec in enumerate(self.recommendations[:3], 1):
            print(f"  {i}. {rec['title']} ({rec['priority']} Priority)")
            print(f"     {rec['description']}")
            print()
        
        print(f"🎯 NEXT STEPS:")
        print(f"  1. Address high-priority issues first")
        print(f"  2. Implement unified module structure")
        print(f"  3. Add comprehensive test coverage")
        print(f"  4. Create configuration management system")
        
        return results


if __name__ == "__main__":
    analyzer = BasicSystemAnalyzer()
    analyzer.generate_report()