"""
Common parallel processing handler for NHS prescription analysis.

This module provides a unified interface for parallel processing across
drug_prevalence, condition_prevalence, and custom_list_prevalence scripts.
"""

import sys


def try_parallel_processing(processing_type, args, files_sub, **kwargs):
    """
    Attempt to use parallel processing for the given analysis type.
    
    Args:
        processing_type: Type of analysis ('drug', 'condition', 'custom_list')
        args: Parsed command line arguments containing serial, cores, benchmark flags
        files_sub: List of files to process
        **kwargs: Additional parameters specific to each processing type
    
    Returns:
        bool: True if parallel processing was used and completed, False if serial processing should be used
    """
    # Skip parallel processing if explicitly disabled or only one file
    if args.serial or len(files_sub) <= 1:
        if args.serial:
            print("📝 Serial processing forced by --serial flag")
        else:
            print("📝 Using serial processing (single file)")
        return False
    
    # Try to import and use parallel processing
    try:
        from matching.parallel_integration import (
            parallel_drug_prevalence,
            parallel_condition_prevalence, 
            parallel_custom_list_prevalence
        )
        
        print("🚀 Using parallel processing...")
        
        # Call the appropriate parallel function based on processing type
        if processing_type == 'drug':
            parallel_drug_prevalence(
                drug_list=kwargs['drug_list'],
                files=files_sub,
                mappings_dir=kwargs.get('mappings_dir', './mappings/'),
                output_dir=kwargs.get('output_dir', '../data_prep/'),
                cores=args.cores,
                benchmark=args.benchmark
            )
        elif processing_type == 'condition':
            parallel_condition_prevalence(
                conditions=kwargs['conditions'],
                files=files_sub,
                mappings_dir=kwargs.get('mappings_dir', './mappings/'),
                output_dir=kwargs.get('output_dir', '../data_prep/'),
                cores=args.cores,
                benchmark=args.benchmark
            )
        elif processing_type == 'custom_list':
            parallel_custom_list_prevalence(
                drug_map=kwargs['drug_map'],
                files=files_sub,
                mappings_dir=kwargs.get('mappings_dir', './mappings/'),
                output_dir=kwargs.get('output_dir', '../data_prep/'),
                cores=args.cores,
                benchmark=args.benchmark
            )
        else:
            raise ValueError(f"Unknown processing type: {processing_type}")
            
        print("✅ Parallel processing completed!")
        return True
        
    except ImportError:
        print("📝 Parallel processing not available, using serial processing")
        return False
    except Exception as e:
        print(f"⚠️ Parallel processing failed: {e}")
        print("📝 Falling back to serial processing")
        return False


def handle_info_request(args):
    """
    Handle the --info flag to show system information.
    
    Args:
        args: Parsed command line arguments
    
    Returns:
        bool: True if info was displayed and program should exit
    """
    if args.info:
        try:
            from matching.parallel_integration import print_processing_info
            print("🖥️ NHS Prescription Parser - System Information")
            print("=" * 50)
            print_processing_info()
        except ImportError:
            print("⚠️ System info not available - parallel processing module not found")
        return True
    return False