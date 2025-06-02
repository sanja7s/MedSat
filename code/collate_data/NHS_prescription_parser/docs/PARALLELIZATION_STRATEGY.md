# Parallelization Strategy for NHS Prescription Parser

## 🎯 **Current Performance Issues**

### **Bottleneck Analysis**
- **12 CPU cores available** but only 1 core used
- **Sequential month processing**: Files processed one by one
- **Current speed**: ~30-60 seconds per month = 30-60 minutes for multi-year
- **Target improvement**: 5-10x speedup possible

### **Critical Sequential Code (drug_prevalence.py:66-96)**
```python
for f in tqdm(files_sub):  # SEQUENTIAL - MAJOR BOTTLENECK
    month = f.split('/')[-1].split('.')[0]
    pdp = pd.read_csv(f,compression='gzip')  # I/O INTENSIVE
    
    for drugname in tqdm(drugMap):  # INNER LOOP
        drugs = drugMap[drugname]
        drug_prescriptions = pdp.loc[pdp[bnf_field].isin(drugs)]
        # calculateTemporalMetrics_LSOA() - CPU INTENSIVE
```

## 🚀 **Parallelization Strategy**

### **Level 1: File-Level Parallelization (Primary Focus)**

**Approach**: Process multiple monthly files simultaneously
- **Independence**: Each month file is completely independent
- **Scalability**: Can process up to 12 files concurrently
- **Memory**: Need to manage memory per process

**Implementation**:
```python
import multiprocessing as mp
from functools import partial

def process_month_file(file_path, drugMap, mappings_dir):
    """Process a single monthly file with all drugs"""
    # Load file once
    # Process all drugs for this month
    # Return month results
    
def parallel_drug_prevalence(files_sub, drugMap, mappings_dir, n_cores=None):
    if n_cores is None:
        n_cores = min(mp.cpu_count(), len(files_sub))
    
    with mp.Pool(n_cores) as pool:
        process_func = partial(process_month_file, 
                             drugMap=drugMap, 
                             mappings_dir=mappings_dir)
        results = pool.map(process_func, files_sub)
    
    # Merge results from all months
    return merge_month_results(results)
```

### **Level 2: Drug-Level Parallelization (Secondary)**

**Within each file, process drugs in parallel**:
```python
def process_drugs_parallel(pdp, drugMap, mappings_dir, old):
    """Process multiple drugs within a file in parallel"""
    
    def process_single_drug(drug_info):
        drugname, drugs = drug_info
        drug_prescriptions = pdp.loc[pdp[bnf_field].isin(drugs)]
        return calculateTemporalMetrics_LSOA(drug_prescriptions, mappings_dir, old)
    
    with ThreadPoolExecutor(max_workers=4) as executor:
        drug_items = list(drugMap.items())
        results = executor.map(process_single_drug, drug_items)
    
    return dict(zip(drugMap.keys(), results))
```

### **Level 3: Hybrid Approach (Optimal)**

**Smart resource allocation**:
- **If files < cores**: File-level parallelization
- **If files ≥ cores**: Balanced file + drug parallelization
- **Memory management**: Monitor RAM usage

## 🔧 **Implementation Plan**

### **Phase 1: Basic File Parallelization**
1. Create `process_month_file()` function
2. Add multiprocessing wrapper
3. Maintain existing API compatibility
4. Test with 2-3 month range

### **Phase 2: Memory Optimization**
1. Add memory monitoring
2. Implement chunked processing if needed
3. Optimize data structures

### **Phase 3: Advanced Features**
1. Progress tracking across processes
2. Error handling and recovery
3. Adaptive core allocation

## 📊 **Expected Performance Gains**

### **Theoretical Speedup**
- **Current**: 1 core × 40 seconds/month = 40s per month
- **With 12 cores**: 12 cores × 40 seconds = ~3.3s per month effective
- **Expected real-world**: 5-8x speedup (accounting for overhead)

### **Multi-year Analysis Example**
- **24 months (2018-2019)**:
  - Current: 24 × 40s = 16 minutes
  - Parallel: 24 ÷ 12 × 40s = ~2-3 minutes

### **Memory Considerations**
- **Per process**: ~2-4GB RAM per monthly file
- **12 processes**: Potential 24-48GB peak usage
- **Solution**: Limit concurrent processes based on available RAM

## 🛠️ **Implementation Details**

### **Function Isolation**
Each monthly file processing needs to be isolated:
```python
def process_month_file(file_path, drugMap, mappings_dir):
    """Completely self-contained month processing"""
    import pandas as pd
    import numpy as np
    from matching.commonFunc_updated import detect_file_format, calculateTemporalMetrics_LSOA
    
    month = file_path.split('/')[-1].split('.')[0]
    pdp = pd.read_csv(file_path, compression='gzip')
    
    # Process all drugs for this month
    month_results = {}
    fields = detect_file_format(pdp)
    old = (fields['format'] == 'old')
    
    for drugname, drugs in drugMap.items():
        drug_prescriptions = pdp.loc[pdp[fields['bnfField']].isin(drugs)]
        month_results[drugname] = calculateTemporalMetrics_LSOA(
            drug_prescriptions, mappings_dir, old
        )
    
    return month, month_results
```

### **Resource Management**
```python
def get_optimal_cores(n_files, available_ram_gb=32):
    """Determine optimal number of cores based on files and RAM"""
    max_cores = mp.cpu_count()
    
    # Estimate 4GB per process
    ram_limited_cores = available_ram_gb // 4
    
    # Don't exceed number of files
    file_limited_cores = min(max_cores, n_files)
    
    return min(max_cores, ram_limited_cores, file_limited_cores)
```

## 🧪 **Testing Strategy**

### **Benchmark Tests**
1. **Single month**: Compare serial vs parallel drug processing
2. **3 months**: Test file-level parallelization
3. **12 months**: Full year performance test
4. **24+ months**: Multi-year stress test

### **Validation**
1. **Result accuracy**: Ensure parallel results match serial
2. **Memory usage**: Monitor peak RAM consumption
3. **Error handling**: Test with missing files, corrupt data

## 📋 **API Compatibility**

The parallel implementation will be **backward compatible**:
```python
# Old API still works
drug_prevalence.py -d metformin -s 201801 -e 201812

# New optional parallel flag
drug_prevalence.py -d metformin -s 201801 -e 201812 --parallel --cores 8
```

This strategy should provide **5-10x performance improvement** for multi-year analyses while maintaining full backward compatibility.