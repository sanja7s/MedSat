
# Submodule to compute drug prevalences. 
This module contains code to compute LSOA level prevalences given 
1. A list of drug names 
2. A list of drugnames with their respective BNF codes. 
3. A list of conditions/symptoms, provided we can find associated drugs from drugbank 
4. Opioid OME prevalence 

## Installing. 
Simply create a conda environment ```conda env create -f environment.yml```
Activate the environment 

## Prevalence based on drug names 
This will generate prevalence values for a list of drug names. The script will try to find BNF codes for variants of the said drug names and then compute LSOA level prevalences. 
- Cd into the code directory
- run the script as such ```python drug_prevalence.py -d metformin -s <Start_YYYYMM> -e <End_YYYYMM>```

## Prevalence based on list of Drug names 
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

```
python custom_list_prevalence.py -l ./sample_list_antidepressants.json -s 201901 -e 201901

```
## Prevalence for conditions/symptoms
There are two ways to run this use case. 

### Using GPT as a aid to find drugs. 
In this case, the first step is to run the follwing prompt before asking GPT model about a particular condition. Please note that
the prompt to be run on GPT 3.5 Turbo, max token limit set to maximum, and temperature set to 0.

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
The response should be a wellformed JSON with the mapped drugs for the given condition. 
