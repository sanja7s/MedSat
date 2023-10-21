
# Submodule to compute drug or condition prevalences. 
This module contains code to compute LSOA level prevalences given 
1. A (list of) drug name(s). 
2. A list of drug names with their respective BNF codes. 
3. A list of conditions/symptoms, provided we can find associated drugs from drugbank/GPT/we curated it. 
4. Opioid OME prevalence.

## Installing. 
Simply create a conda environment ```conda env create -f environment.yml```
Activate the environment 

## 1 Prevalence based on (a list of) drug name(s). 
This will generate prevalence values for a list of drug names. The script will try to find BNF codes for variants of the said drug names and then compute LSOA level prevalences. 
- Cd into the code directory
- run the script as such ```python drug_prevalence.py -d metformin -s <Start_YYYYMM> -e <End_YYYYMM>```

## 2 Prevalence based on a list of drug names with BNF codes.
This is a toned down version of the above script which takes in a list of drugs and their corresponding BNF codes as a JSON and computes prevalences. Sample list jsons are included. 
In order to convert an arbitrary list of drugs into this format, you may use the following prompt with GPT completion API. Make sure you douple check the response and the corresponding BNF codes. Also make sure that the temperature is set to 0 and maximum length to its maximum limit. 

```
You are a pharmacy expert who knows the British National Formulary (BNF) codes of all the drugs. You do not make stuff up, and when you don't know some code, you omit that drug from your response. You respond to user query using the following guidelines 
- When the user sends a list of drug names, you will respond with corresponding BNF codes for the drugs you know. 
- You will format the response as a JSON with the following schema as a referance
{
  "fentanyl": ["1501043F0", "1502010Z0", "0407020A0"],
  "oxycodone": ["0407020AD", "0407020AF", "0407020Z0"],
  "codine": ["0309020AB"]
}
```
once you have the json ready, you may run the prevalence script as follows

```python custom_list_prevalence.py -l ./sample_list_antidepressants.json -s 201901 -e 201901```

## 3 Prevalence for conditions/symptoms.
There are two ways to run this use case. 

### a) Using drugbank as an aid to find drugs

This part mathes names of conditions with a drug->condition association graph built from the drugbank crawl. 

To generate prevalences using condition names 

```python condition_prevalence.py -s YYYYMM -e YYYYMM -c condition_name1 condition_name2```

The prevalences files should be created in data_prep folder, along with a csv file called ```Drugs.csv```that contains associations of named conditions with different drugs and BNF codes.


### b) Using custom condition drug name lists.

Here, we have an option b.1) to use a literature-derived or user-curated list of drugs (e.g., `sample_list_antidepressants.json`), or b.2) we can use GPT as an alternative to drugbank to help us associate drugs with the condition. 

#### b.1) Using drug names list we curated from literature or ourselves.
Example of lists curated by us or from the literature are `sample_list_antidepressants.json`, `sample_list_anxiety.json` or `sample_list_painkiller.json`.

#### b.2) Using GPT as an aid to find drugs.
In this case, the first step is to run the follwing prompt before asking GPT model about a particular condition. Please note that the prompt is to be run on GPT 3.5 Turbo, max token limit set to maximum, and temperature set to 0.

```
You are a pharmacy expert who knows the British National Formulary (BNF) codes, drug names, and the conditions or symptoms for which those drugs are prescribed. You follow the following guidelines 
- You do not make stuff up. If you do not know about a drug, its BNF code, or the condition/symptom its associated with, you do not include them in the response. 
- You respond in wellformed JSON. 
- You will also respond with other conditions that you know of, for which the said drug is prescribed. 

The user will send a name of a condition or a symptom, and you must respond in a well formed JSON with the following structure
{ 
 "drug_name_1" : {
     "BNF_code" : ["Code1", "Code2", "Code3"],
      "Other_associations" : ["condition 1" , "condition 2" , "condition 3"]
},
 "drug_name_2" : {
     "BNF_code" : ["Code1", "Code2", "Code3"],
      "Other_associations" : ["condition 1" , "condition 2" , "condition 3"]
  }
}
``` 
The response should be a well-formed JSON with the mapped drugs for the given condition. 
Transform this list into the format such as in `sample_list_antidepressants.json`. Having such a list of drug names associated with our condition, we can then run the following commands (one to extract prevalences for the specific drugs and the other to aggregate those into the condition prevalence):

```python custom_list_prevalence.py -l ./sample_list_antidepressants.json -s 201901 -e 202012```

``` python condition_prevalence.py -s 201901 -e 202012 -c depression -custDLFN sample_list_antidepressants.json```
