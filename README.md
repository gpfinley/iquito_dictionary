# iquito_dictionary
Generate LaTeX markup for an Iquito dictionary from a FLEx database export

Steps:
- unzip the archive somewhere and navigate to it
- export LIFT XML from FLEx and save it as 'iquito dictionary.lift' in the script directory
- double-click on run_mac.command
- it should open up a terminal and go through the process. At the end, it tells you which LaTeX custom commands were generated for all three dictionaries (Iqt-Spa/Eng, Eng-Iqt, Eng-Spa).
- if that doesn't work, you can run the script from Terminal: navigate to the directory ('cd Downloads/iquito_aug2016', perhaps) and run 'python iquito_dictionary.py' (or 'python2.7 iquito_dictionary.py' if python3 is the default)
- you can also modify 'iquito alphabet.txt' if something has changed in the alphabet
- (note that, alternatively, LIFT and alphabet files living elsewhere can be passed in as command-line arguments: 'python iquito_dictionary.py <LIFT_file> <alphabet_file>' when running from Terminal. If using the double-click strategy, it will only look for files specifically named 'iquito dictionary.lift' and 'iquito alphabet.txt'.)
- the eng_reversal, iqt_dictionary, and spn_reversal folders contain the custom commands and main files we've been using previously. Copy the script-generated '..._entries.tex' files into their respective folders and typeset the '...main.tex' files.
